"""
Ingress Router — Phase 4.2

Orchestrates: ICC → ASTG → BSG → EDH → SPM → PRAP
Halt path: on any gate halt|fail → assemble HaltResponse, return without calling model
Pass path: assemble IngressPipelineEnvelope with model prompt
Model prompt = system governance block + state annotation block + raw user input
SPM output injection: when SPM fires, attach spm_output to IngressPipelineEnvelope
"""
from __future__ import annotations

import time
from typing import Optional

from cgs_runtime_wrapper.ingress.gates.icc import run_icc_gate
from cgs_runtime_wrapper.ingress.gates.astg import run_astg_gate
from cgs_runtime_wrapper.ingress.gates.bsg import run_bsg_gate
from cgs_runtime_wrapper.ingress.gates.edh import run_edh_gate
from cgs_runtime_wrapper.ingress.gates.spm import run_spm_gate
from cgs_runtime_wrapper.ingress.gates.prap import run_prap_gate
from cgs_runtime_wrapper.models.envelopes import (
    ASTGGateData,
    EDHGateData,
    FailureClass,
    GateId,
    GateResult,
    GateStatus,
    HaltReasonCode,
    HaltResponse,
    HaltType,
    ICCGateData,
    IngressPipelineEnvelope,
    PipelineStatusIngress,
    RequestEnvelope,
    SessionState,
    SPMGateData,
)

_SYSTEM_GOVERNANCE_BLOCK = """\
[CGS RUNTIME GOVERNANCE — INTERNAL USE ONLY]
This response is governed by the Cosyn Governance Stack (CGS).
All outputs must comply with: constraint consistency, assumption transparency,
bias sensitivity, scope adherence, and lexical compliance.
Do not disclose internal gate states. Respond only within declared scope.
[END GOVERNANCE BLOCK]
"""


def _build_state_annotation_block(
    state: SessionState,
    edh_fired: bool,
    prap_status: str,
) -> str:
    """Build state annotation block as KEY: VALUE one per line."""
    lines = [
        "--- STATE ANNOTATION ---",
        f"TURN_INDEX: {state.turn_index + 1}",  # next turn (being processed)
        f"SPM_SIGNAL_A_COUNT: {len(state.spm_signal_a_turns)}",
        f"SPM_SIGNAL_B_COUNT: {len(state.spm_signal_b_turns)}",
        f"SPM_SIGNAL_C_COUNT: {len(state.spm_signal_c_turns)}",
        f"SPM_FIRED_THIS_SESSION: {state.spm_fired}",
        f"CCD_CONFIDENCE_REGISTER: {state.ccd_confidence_register}",
        f"EDH_ECHO_FLAG: {edh_fired}",
        f"PRAP_STATUS: {prap_status}",
        f"MODE_LOCK: {state.mode_lock or 'none'}",
        f"ACTIVE_PERSONA: {state.active_persona}",
        "--- END STATE ANNOTATION ---",
    ]
    return "\n".join(lines)


def _build_assumption_block(astg_data: ASTGGateData) -> str:
    if not astg_data.assumptions_identified:
        return ""
    lines = ["--- ASSUMPTION BLOCK ---"]
    for i, assumption in enumerate(astg_data.assumptions_identified, 1):
        lines.append(f"Assumption {i}: {assumption.assumption_text}")
        lines.append(f"  Failure condition: {assumption.failure_condition}")
        lines.append(f"  Conclusion impact: {assumption.conclusion_impact}")
        lines.append(f"  Stability: {assumption.stability.value}")
    lines.append("--- END ASSUMPTION BLOCK ---")
    return "\n".join(lines)


def _is_terminal_status(status: GateStatus) -> bool:
    return status in (GateStatus.halt, GateStatus.fail)


async def run_ingress_pipeline(
    request: RequestEnvelope,
    session_state: SessionState,
) -> tuple[IngressPipelineEnvelope, SessionState]:
    """
    Run the full ingress pipeline.
    Returns (IngressPipelineEnvelope, updated_session_state).
    """
    pipeline_start = int(time.time() * 1000)
    gate_results: list[GateResult] = []
    active_persona = session_state.active_persona

    # Apply request overrides to session state
    if request.persona_override:
        session_state = session_state.model_copy(
            update={"active_persona": request.persona_override}
        )
        active_persona = request.persona_override

    if request.mode_lock is not None:
        session_state = session_state.model_copy(
            update={"mode_lock": request.mode_lock}
        )

    if request.crs_scope is not None:
        session_state = session_state.model_copy(
            update={"crs_scope": request.crs_scope}
        )

    session_state = session_state.model_copy(
        update={"spm_suppress": request.spm_suppress}
    )

    # -----------------------------------------------------------------------
    # Gate 1: ICC
    # -----------------------------------------------------------------------
    icc_result = await run_icc_gate(
        raw_input=request.raw_input,
        crs_scope=request.crs_scope,
        turn_index=request.turn_index,
    )
    gate_results.append(icc_result)

    if _is_terminal_status(icc_result.status):
        return _build_halt_envelope(
            request, gate_results, session_state, icc_result, pipeline_start, active_persona
        ), session_state

    icc_gate_data = ICCGateData.model_validate(icc_result.gate_data)

    # -----------------------------------------------------------------------
    # Gate 2: ASTG
    # -----------------------------------------------------------------------
    astg_result = await run_astg_gate(
        raw_input=request.raw_input,
        icc_gate_data=icc_gate_data,
        crs_scope=request.crs_scope,
    )
    gate_results.append(astg_result)

    if _is_terminal_status(astg_result.status):
        return _build_halt_envelope(
            request, gate_results, session_state, astg_result, pipeline_start, active_persona
        ), session_state

    astg_gate_data = ASTGGateData.model_validate(astg_result.gate_data)

    # -----------------------------------------------------------------------
    # Gate 3: BSG
    # -----------------------------------------------------------------------
    bsg_result = await run_bsg_gate(
        raw_input=request.raw_input,
        icc_gate_data=icc_gate_data,
    )
    gate_results.append(bsg_result)

    if _is_terminal_status(bsg_result.status):
        return _build_halt_envelope(
            request, gate_results, session_state, bsg_result, pipeline_start, active_persona
        ), session_state

    # -----------------------------------------------------------------------
    # Gate 4: EDH
    # -----------------------------------------------------------------------
    edh_result, session_state = await run_edh_gate(
        raw_input=request.raw_input,
        icc_gate_data=icc_gate_data,
        session_state=session_state,
        turn_index=request.turn_index,
    )
    gate_results.append(edh_result)

    if _is_terminal_status(edh_result.status):
        return _build_halt_envelope(
            request, gate_results, session_state, edh_result, pipeline_start, active_persona
        ), session_state

    edh_gate_data = EDHGateData.model_validate(edh_result.gate_data) if edh_result.gate_data else None

    # -----------------------------------------------------------------------
    # Gate 5: SPM (non-blocking)
    # -----------------------------------------------------------------------
    spm_result, session_state = await run_spm_gate(
        raw_input=request.raw_input,
        icc_gate_data=icc_gate_data,
        edh_gate_data=edh_gate_data,
        session_state=session_state,
        turn_index=request.turn_index,
    )
    gate_results.append(spm_result)

    spm_gate_data = SPMGateData.model_validate(spm_result.gate_data) if spm_result.gate_data else None
    spm_output: str | None = spm_gate_data.spm_output_text if spm_gate_data else None

    # -----------------------------------------------------------------------
    # Gate 6: PRAP
    # -----------------------------------------------------------------------
    prap_result = await run_prap_gate(
        prior_gate_results=gate_results,
        session_state=session_state,
        request=request,
    )
    gate_results.append(prap_result)

    if _is_terminal_status(prap_result.status):
        return _build_halt_envelope(
            request, gate_results, session_state, prap_result, pipeline_start, active_persona
        ), session_state

    # -----------------------------------------------------------------------
    # Build model prompt
    # -----------------------------------------------------------------------
    prap_status = prap_result.status.value
    state_annotation = _build_state_annotation_block(
        session_state,
        edh_fired=session_state.edh_fired,
        prap_status=prap_status,
    )
    assumption_block = _build_assumption_block(astg_gate_data)

    model_prompt_parts = [
        _SYSTEM_GOVERNANCE_BLOCK,
        state_annotation,
    ]
    if assumption_block:
        model_prompt_parts.append(assumption_block)
    if spm_output:
        model_prompt_parts.append(f"--- SPM OBSERVATION ---\n{spm_output}\n--- END SPM ---")

    model_prompt_parts.append(f"User input: {request.raw_input}")
    model_prompt = "\n\n".join(model_prompt_parts)

    ingress_completed_at_ms = int(time.time() * 1000)

    envelope = IngressPipelineEnvelope(
        request=request,
        gate_results=gate_results,
        pipeline_status=PipelineStatusIngress.proceed,
        halt_response=None,
        model_prompt=model_prompt,
        active_persona=active_persona,
        ingress_completed_at_ms=ingress_completed_at_ms,
        spm_output=spm_output,
    )
    return envelope, session_state


def _build_halt_envelope(
    request: RequestEnvelope,
    gate_results: list[GateResult],
    session_state: SessionState,
    failing_gate: GateResult,
    pipeline_start: int,
    active_persona: str,
) -> IngressPipelineEnvelope:
    """Build an IngressPipelineEnvelope for the halt path."""
    halt_reason = failing_gate.halt_reason_code or HaltReasonCode.MISSING_REQUIRED_INPUTS

    # Determine halt type
    halt_type = HaltType.halt
    if halt_reason == HaltReasonCode.AMBIGUOUS_INTENT:
        halt_type = HaltType.clarify
    elif halt_reason == HaltReasonCode.MISSING_REQUIRED_INPUTS:
        halt_type = HaltType.clarify

    halt_resp = HaltResponse(
        type=halt_type,
        halt_reason_code=halt_reason,
        user_facing_text=_halt_user_text(halt_reason),
        gate_id=failing_gate.gate_id,
        session_id=request.session_id,
        turn_index=request.turn_index,
        missing_inputs=None,
    )

    pipeline_status = PipelineStatusIngress.halt
    if halt_type == HaltType.clarify:
        pipeline_status = PipelineStatusIngress.clarify

    return IngressPipelineEnvelope(
        request=request,
        gate_results=gate_results,
        pipeline_status=pipeline_status,
        halt_response=halt_resp.model_dump_json(),
        model_prompt=None,
        active_persona=active_persona,
        ingress_completed_at_ms=int(time.time() * 1000),
        spm_output=None,
    )


def _halt_user_text(code: HaltReasonCode) -> str:
    """Return a user-facing message for a halt reason code."""
    messages = {
        HaltReasonCode.MISSING_REQUIRED_INPUTS: (
            "Required inputs are missing. Please provide the necessary information to proceed."
        ),
        HaltReasonCode.AMBIGUOUS_INTENT: (
            "The intent of your request is ambiguous. Please clarify what you would like to achieve."
        ),
        HaltReasonCode.CONSTRAINT_CONFLICT: (
            "Your request contains conflicting constraints that cannot be simultaneously satisfied."
        ),
        HaltReasonCode.UNDECLARED_ASSUMPTION: (
            "This request requires an assumption that has not been declared. Please confirm the assumption to proceed."
        ),
        HaltReasonCode.IMPLICIT_BIAS: (
            "An implicit bias framing was detected. Please select an explicit perspective frame for this request."
        ),
        HaltReasonCode.CONFLICTING_BIAS_SIGNALS: (
            "Conflicting bias signals were detected in your request. Please clarify the desired framing."
        ),
        HaltReasonCode.ECHO_REPETITION: (
            "Echo repetition detected. Please introduce new evidence or reframe the question to proceed."
        ),
        HaltReasonCode.CRS_SCOPE_VIOLATION: (
            "This request falls outside the declared scope boundary in strict mode."
        ),
        HaltReasonCode.MODE_LOCK_VIOLATION: (
            "A mode lock violation was detected. The requested mode conflicts with the active session mode."
        ),
        HaltReasonCode.SCOPE_EXCEEDED: (
            "The response scope exceeded declared boundaries."
        ),
        HaltReasonCode.LEXICAL_VIOLATION: (
            "A lexical compliance violation was detected in the response."
        ),
        HaltReasonCode.UNRESOLVABLE_DRIFT: (
            "Unresolvable drift detected. The response cannot be aligned with session constraints."
        ),
        HaltReasonCode.RERENDER_LIMIT_EXCEEDED: (
            "The maximum rerender limit has been exceeded. Manual review required."
        ),
    }
    return messages.get(code, f"A governance halt was triggered: {code.value}")
