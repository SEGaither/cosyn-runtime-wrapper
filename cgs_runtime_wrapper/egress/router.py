"""
Egress Router — Phase 5.2

- Assemble OutputEnvelope from egress gate results
- Rerender loop: on FINALIZATION rerender, return annotated prompt to model with reason. Max 2 cycles.
  On limit: RERENDER_LIMIT_EXCEEDED halt
- Persona header injection: prepend to all user-facing output
- NFAR handler: "NFAR" or "no further action required" → return exactly "Standing by."
- EOS handler: "EOS" → assemble session snapshot → call POST /session/reset
- Trace This handler: assemble audit ledger from telemetry store
"""
from __future__ import annotations

import time
from typing import Optional

from cgs_runtime_wrapper.adapters.model_adapter import ModelAdapter
from cgs_runtime_wrapper.egress.gates.finalization import run_finalization_gate
from cgs_runtime_wrapper.egress.gates.oscl import run_oscl_gate
from cgs_runtime_wrapper.egress.gates.telemetry_gate import run_telemetry_gate
from cgs_runtime_wrapper.models.envelopes import (
    ASTGGateData,
    FailureClass,
    GateId,
    GateResult,
    GateStatus,
    HaltReasonCode,
    HaltType,
    ICCGateData,
    IngressPipelineEnvelope,
    ModelResponseEnvelope,
    OutputEnvelope,
    PipelineStatusOutput,
    RequestEnvelope,
    SessionState,
    SPMGateData,
    TelemetryTurnRecord,
)
from cgs_runtime_wrapper.state.session_store import SessionStore
from cgs_runtime_wrapper.telemetry.store import TelemetryStore

_PERSONA_HEADER_CONTROL = "Router (control-plane): Stack Architect"
_PERSONA_HEADER_ACTIVE_PREFIX = "Active persona (this turn):"

_NFAR_TRIGGERS = ["nfar", "no further action required"]
_EOS_TRIGGER = "eos"
_TRACE_THIS_TRIGGER = "trace this"

MAX_RERENDERS = 2

_STANDING_BY = "Standing by."


def _is_nfar(raw_output: str) -> bool:
    lower = raw_output.strip().lower()
    return any(trigger in lower for trigger in _NFAR_TRIGGERS)


def _is_eos(raw_output: str) -> bool:
    return raw_output.strip().lower() == _EOS_TRIGGER


def _is_trace_this(raw_input: str) -> bool:
    return _TRACE_THIS_TRIGGER in raw_input.strip().lower()


def _prepend_persona_headers(text: str, persona: str) -> str:
    header = f"{_PERSONA_HEADER_CONTROL}\n{_PERSONA_HEADER_ACTIVE_PREFIX} {persona}"
    if _PERSONA_HEADER_CONTROL in text:
        return text  # already present
    return f"{header}\n\n{text}"


def _build_rerender_prompt(
    original_prompt: str,
    rerender_reason: str,
    prior_output: str,
    rerender_count: int,
) -> str:
    return (
        f"{original_prompt}\n\n"
        f"--- RERENDER REQUEST (attempt {rerender_count + 1}/{MAX_RERENDERS}) ---\n"
        f"The previous response was rejected for the following reason:\n"
        f"{rerender_reason}\n\n"
        f"Prior output (rejected):\n{prior_output}\n\n"
        f"Please rewrite the response addressing the above issue. "
        f"Do not include the rejection reason in your output.\n"
        f"--- END RERENDER REQUEST ---"
    )


async def _assemble_session_snapshot(
    session_state: SessionState,
    telemetry_store: TelemetryStore,
) -> dict:
    """Assemble a complete session snapshot for EOS handling."""
    records = await telemetry_store.get_all_records(session_state.session_id)
    rollup = await telemetry_store.build_rollup(session_state.session_id)
    return {
        "session_state": session_state.model_dump(),
        "turn_records": [r.model_dump() for r in records],
        "rollup": rollup.model_dump(),
    }


async def _assemble_audit_ledger(
    session_id: str,
    telemetry_store: TelemetryStore,
) -> str:
    """Assemble audit ledger for Trace This handler."""
    records = await telemetry_store.get_all_records(session_id)
    rollup = await telemetry_store.build_rollup(session_id)

    lines = [
        f"=== AUDIT LEDGER: {session_id} ===",
        f"Total turns: {rollup.total_turns}",
        f"Halt rate: {rollup.halt_rate:.2%}",
        f"Rerender rate: {rollup.rerender_rate:.2%}",
        f"SPM fires: {rollup.spm_fire_count}",
        f"SPM disputes: {rollup.spm_dispute_count}",
        f"Provisional rate: {rollup.provisional_rate:.2%}",
        "",
        "--- Turn-level audit ---",
    ]
    for rec in records:
        lines.append(
            f"Turn {rec.turn_index}: halt={rec.halt_triggered} "
            f"code={rec.halt_reason_code} "
            f"rerender={rec.rerender_requested} "
            f"spm_A={rec.spm_signal_a_count} B={rec.spm_signal_b_count} C={rec.spm_signal_c_count}"
        )
    return "\n".join(lines)


async def run_egress_pipeline(
    ingress_envelope: IngressPipelineEnvelope,
    session_state: SessionState,
    model_adapter: ModelAdapter,
    session_store: SessionStore,
    telemetry_store: TelemetryStore,
    turn_start_ms: int,
) -> tuple[OutputEnvelope, SessionState]:
    """
    Run the full egress pipeline.
    Returns (OutputEnvelope, updated_session_state).
    """
    request = ingress_envelope.request
    persona = session_state.active_persona

    # -----------------------------------------------------------------------
    # Handle halt path from ingress
    # -----------------------------------------------------------------------
    if ingress_envelope.pipeline_status.value in ("halt", "clarify"):
        halt_text = ingress_envelope.halt_response or "Request halted by governance pipeline."
        emission = _prepend_persona_headers(halt_text, persona)
        now_ms = int(time.time() * 1000)
        latency = now_ms - turn_start_ms

        # Build minimal telemetry
        tel_record = TelemetryTurnRecord(
            session_id=request.session_id,
            turn_index=request.turn_index,
            personas_invoked=[persona],
            synthesis_mode=False,
            gate_triggers_fired=[gr.gate_id for gr in ingress_envelope.gate_results
                                  if gr.status in (GateStatus.halt, GateStatus.fail)],
            halt_triggered=True,
            halt_reason_code=_get_first_halt_code(ingress_envelope.gate_results),
            rerender_requested=False,
            rerender_count=0,
            provisional_labeling_count=0,
            assumption_block_present=False,
            numeric_claims_count=0,
            numeric_claims_with_basis_count=0,
            scope_violation_flags=[],
            spm_signal_a_count=len(session_state.spm_signal_a_turns),
            spm_signal_b_count=len(session_state.spm_signal_b_turns),
            spm_signal_c_count=len(session_state.spm_signal_c_turns),
            spm_threshold_crossed=False,
            spm_fired=session_state.spm_fired,
            spm_dispute_event=False,
            spm_dispute_signal_classification=None,
            latency_ms=latency,
            classifier_latency_ms=0,
            model_latency_ms=0,
        )
        try:
            await telemetry_store.write_turn_record(tel_record)
        except Exception:
            pass

        updated_state = session_state.model_copy(update={
            "turn_index": session_state.turn_index + 1,
            "last_turn_completed_at_ms": now_ms,
        })
        await session_store.put(updated_state)

        return OutputEnvelope(
            session_id=request.session_id,
            turn_index=request.turn_index,
            emission=emission,
            pipeline_status=PipelineStatusOutput.halted,
            gate_results_egress=[],
            telemetry_payload=tel_record,
            provisional=False,
            spm_fired_this_turn=False,
            halt_response=halt_text,
            rerender_count=0,
            turn_completed_at_ms=now_ms,
            latency_ms=latency,
        ), updated_state

    # -----------------------------------------------------------------------
    # Trace This — intercept before model call
    # -----------------------------------------------------------------------
    if _is_trace_this(request.raw_input):
        audit_text = await _assemble_audit_ledger(request.session_id, telemetry_store)
        emission = _prepend_persona_headers(audit_text, persona)
        now_ms = int(time.time() * 1000)
        latency = now_ms - turn_start_ms

        tel_record = _minimal_tel_record(request, session_state, latency)
        try:
            await telemetry_store.write_turn_record(tel_record)
        except Exception:
            pass

        updated_state = session_state.model_copy(update={
            "turn_index": session_state.turn_index + 1,
            "last_turn_completed_at_ms": now_ms,
        })
        await session_store.put(updated_state)

        return OutputEnvelope(
            session_id=request.session_id,
            turn_index=request.turn_index,
            emission=emission,
            pipeline_status=PipelineStatusOutput.emitted,
            gate_results_egress=[],
            telemetry_payload=tel_record,
            provisional=False,
            spm_fired_this_turn=False,
            halt_response=None,
            rerender_count=0,
            turn_completed_at_ms=now_ms,
            latency_ms=latency,
        ), updated_state

    # -----------------------------------------------------------------------
    # Call model
    # -----------------------------------------------------------------------
    model_prompt = ingress_envelope.model_prompt or request.raw_input
    model_start_ms = int(time.time() * 1000)
    raw_output, model_latency_ms = await model_adapter.call_model(
        model_prompt, request.session_id
    )
    classifier_latency_ms = model_start_ms - turn_start_ms

    # -----------------------------------------------------------------------
    # NFAR handler
    # -----------------------------------------------------------------------
    if _is_nfar(raw_output):
        emission = _prepend_persona_headers(_STANDING_BY, persona)
        now_ms = int(time.time() * 1000)
        latency = now_ms - turn_start_ms

        tel_record = _minimal_tel_record(request, session_state, latency, model_latency_ms=model_latency_ms)
        try:
            await telemetry_store.write_turn_record(tel_record)
        except Exception:
            pass

        updated_state = session_state.model_copy(update={
            "turn_index": session_state.turn_index + 1,
            "last_turn_completed_at_ms": now_ms,
        })
        await session_store.put(updated_state)

        return OutputEnvelope(
            session_id=request.session_id,
            turn_index=request.turn_index,
            emission=emission,
            pipeline_status=PipelineStatusOutput.emitted,
            gate_results_egress=[],
            telemetry_payload=tel_record,
            provisional=False,
            spm_fired_this_turn=False,
            halt_response=None,
            rerender_count=0,
            turn_completed_at_ms=now_ms,
            latency_ms=latency,
        ), updated_state

    # -----------------------------------------------------------------------
    # EOS handler
    # -----------------------------------------------------------------------
    if _is_eos(raw_output):
        snapshot = await _assemble_session_snapshot(session_state, telemetry_store)
        snapshot_text = f"Session snapshot assembled. {len(snapshot['turn_records'])} turns recorded."
        emission = _prepend_persona_headers(snapshot_text, persona)
        now_ms = int(time.time() * 1000)
        latency = now_ms - turn_start_ms

        tel_record = _minimal_tel_record(request, session_state, latency, model_latency_ms=model_latency_ms)
        try:
            await telemetry_store.write_turn_record(tel_record)
        except Exception:
            pass

        # Reset session
        updated_state = await session_store.reset(
            request.session_id,
            cgs_version=request.cgs_version,
            wrapper_version=request.wrapper_version,
        )

        return OutputEnvelope(
            session_id=request.session_id,
            turn_index=request.turn_index,
            emission=emission,
            pipeline_status=PipelineStatusOutput.emitted,
            gate_results_egress=[],
            telemetry_payload=tel_record,
            provisional=False,
            spm_fired_this_turn=False,
            halt_response=None,
            rerender_count=0,
            turn_completed_at_ms=now_ms,
            latency_ms=latency,
        ), updated_state

    # -----------------------------------------------------------------------
    # Egress gate pipeline with rerender loop
    # -----------------------------------------------------------------------
    egress_gate_results: list[GateResult] = []
    rerender_count = 0
    rerender_reason_history: list[str] = []
    current_output = raw_output
    provisional = False

    # Extract gate data for egress
    icc_gate_data: Optional[ICCGateData] = None
    astg_gate_data: Optional[ASTGGateData] = None
    for gr in ingress_envelope.gate_results:
        if gr.gate_id == GateId.ICC and gr.gate_data:
            try:
                icc_gate_data = ICCGateData.model_validate(gr.gate_data)
            except Exception:
                pass
        if gr.gate_id == GateId.ASTG and gr.gate_data:
            try:
                astg_gate_data = ASTGGateData.model_validate(gr.gate_data)
            except Exception:
                pass

    # Check provisional flag from any ingress gate
    provisional = any(gr.provisional_flag for gr in ingress_envelope.gate_results)

    while True:
        egress_gate_results = []

        # Gate OSCL
        oscl_result = await run_oscl_gate(
            raw_output=current_output,
            icc_gate_data=icc_gate_data,
            astg_gate_data=astg_gate_data,
            rerender_count=rerender_count,
        )
        egress_gate_results.append(oscl_result)

        if oscl_result.status == GateStatus.halt:
            # SCP trigger → halt
            break

        if oscl_result.status == GateStatus.rerender:
            if rerender_count >= MAX_RERENDERS:
                break  # will be caught below
            rerender_reason = oscl_result.rerender_reason or "OSCL threshold not met"
            rerender_reason_history.append(rerender_reason)
            rerender_prompt = _build_rerender_prompt(
                model_prompt, rerender_reason, current_output, rerender_count
            )
            current_output, _ = await model_adapter.call_model(rerender_prompt, request.session_id)
            rerender_count += 1
            continue

        # Gate FINALIZATION
        fin_result, current_output = await run_finalization_gate(
            raw_output=current_output,
            request=request,
            session_state=session_state,
            rerender_count=rerender_count,
            has_provisional=provisional,
        )
        egress_gate_results.append(fin_result)

        if fin_result.status == GateStatus.halt:
            break

        if fin_result.status == GateStatus.rerender:
            if rerender_count >= MAX_RERENDERS:
                break  # rerender limit
            rerender_reason = fin_result.rerender_reason or "Finalization checks failed"
            rerender_reason_history.append(rerender_reason)
            rerender_prompt = _build_rerender_prompt(
                model_prompt, rerender_reason, current_output, rerender_count
            )
            current_output, _ = await model_adapter.call_model(rerender_prompt, request.session_id)
            rerender_count += 1
            continue

        # Both OSCL and FINALIZATION passed
        break

    # -----------------------------------------------------------------------
    # Check rerender limit exceeded
    # -----------------------------------------------------------------------
    now_ms = int(time.time() * 1000)
    latency = now_ms - turn_start_ms

    # Determine final pipeline status
    any_halt = any(gr.status == GateStatus.halt for gr in egress_gate_results)
    rerender_limit_hit = rerender_count >= MAX_RERENDERS and any(
        gr.status == GateStatus.rerender for gr in egress_gate_results
    )

    if rerender_limit_hit:
        pipeline_status = PipelineStatusOutput.rerender_limit_exceeded
        emission = _prepend_persona_headers(
            "The rerender limit has been exceeded. This turn cannot be completed.",
            persona,
        )
        halt_text = f"RERENDER_LIMIT_EXCEEDED: {'; '.join(rerender_reason_history)}"
    elif any_halt:
        pipeline_status = PipelineStatusOutput.halted
        halt_code = _get_halt_code_from_results(egress_gate_results)
        halt_text = f"Egress halt: {halt_code.value if halt_code else 'UNKNOWN'}"
        emission = _prepend_persona_headers(
            ingress_envelope.halt_response or halt_text, persona
        )
    else:
        pipeline_status = PipelineStatusOutput.emitted
        emission = current_output
        halt_text = None

    # SPM fired this turn detection
    spm_gate = next(
        (gr for gr in ingress_envelope.gate_results if gr.gate_id == GateId.SPM), None
    )
    spm_fired_this_turn = False
    if spm_gate and spm_gate.gate_data:
        try:
            spm_data = SPMGateData.model_validate(spm_gate.gate_data)
            spm_fired_this_turn = spm_data.threshold_crossed and not session_state.spm_fired
        except Exception:
            pass

    # -----------------------------------------------------------------------
    # TELEMETRY gate
    # -----------------------------------------------------------------------
    tel_gate_result, updated_state = await run_telemetry_gate(
        ingress_envelope=ingress_envelope,
        egress_gate_results=egress_gate_results,
        output_text=current_output,
        session_state=session_state,
        telemetry_store=telemetry_store,
        latency_ms=latency,
        classifier_latency_ms=classifier_latency_ms,
        model_latency_ms=model_latency_ms,
        rerender_count=rerender_count,
        provisional=provisional,
    )
    egress_gate_results.append(tel_gate_result)
    await session_store.put(updated_state)

    # Build final telemetry payload from store
    tel_record = await telemetry_store.get_turn_record(request.session_id, request.turn_index)
    if tel_record is None:
        # Fallback: create minimal record
        tel_record = _minimal_tel_record(request, session_state, latency, model_latency_ms=model_latency_ms)

    return OutputEnvelope(
        session_id=request.session_id,
        turn_index=request.turn_index,
        emission=emission,
        pipeline_status=pipeline_status,
        gate_results_egress=egress_gate_results,
        telemetry_payload=tel_record,
        provisional=provisional,
        spm_fired_this_turn=spm_fired_this_turn,
        halt_response=halt_text,
        rerender_count=rerender_count,
        turn_completed_at_ms=now_ms,
        latency_ms=latency,
    ), updated_state


def _get_first_halt_code(gate_results: list[GateResult]):
    for gr in gate_results:
        if gr.status in (GateStatus.halt, GateStatus.fail) and gr.halt_reason_code:
            return gr.halt_reason_code
    return None


def _get_halt_code_from_results(gate_results: list[GateResult]):
    for gr in gate_results:
        if gr.status == GateStatus.halt and gr.halt_reason_code:
            return gr.halt_reason_code
    return None


def _minimal_tel_record(
    request: RequestEnvelope,
    session_state: SessionState,
    latency_ms: int,
    model_latency_ms: int = 0,
) -> TelemetryTurnRecord:
    return TelemetryTurnRecord(
        session_id=request.session_id,
        turn_index=request.turn_index,
        personas_invoked=[session_state.active_persona],
        synthesis_mode=False,
        gate_triggers_fired=[],
        halt_triggered=False,
        halt_reason_code=None,
        rerender_requested=False,
        rerender_count=0,
        provisional_labeling_count=0,
        assumption_block_present=False,
        numeric_claims_count=0,
        numeric_claims_with_basis_count=0,
        scope_violation_flags=[],
        spm_signal_a_count=len(session_state.spm_signal_a_turns),
        spm_signal_b_count=len(session_state.spm_signal_b_turns),
        spm_signal_c_count=len(session_state.spm_signal_c_turns),
        spm_threshold_crossed=False,
        spm_fired=session_state.spm_fired,
        spm_dispute_event=False,
        spm_dispute_signal_classification=None,
        latency_ms=latency_ms,
        classifier_latency_ms=0,
        model_latency_ms=model_latency_ms,
    )
