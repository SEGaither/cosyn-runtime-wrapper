"""
TELEMETRY Gate — Egress position 3 (final, non-blocking)

- Write TelemetryTurnRecord to store
- Write SessionState.last_turn_completed_at_ms
- Increment SessionState.turn_index (ONLY gate that does this)
- Always warn on failure, never block
"""
from __future__ import annotations

import time
from typing import Optional

from cgs_runtime_wrapper.models.envelopes import (
    ASTGGateData,
    FailureClass,
    GateId,
    GateResult,
    GateStatus,
    HaltReasonCode,
    ICCGateData,
    IngressPipelineEnvelope,
    OutputEnvelope,
    SessionState,
    SPMGateData,
    TelemetryGateData,
    TelemetryTurnRecord,
)
from cgs_runtime_wrapper.telemetry.store import TelemetryStore


def _extract_numeric_claims(text: str) -> tuple[int, int]:
    """
    Heuristic: count numeric claims and those with basis.
    Returns (total_numeric_claims, claims_with_basis).
    """
    import re
    # Count numbers/percentages as numeric claims
    numbers = re.findall(r'\b\d+(?:\.\d+)?(?:%|percent|million|billion|thousand)?\b', text)
    total = len(numbers)
    # Basis markers
    basis_markers = ["according to", "source:", "citation:", "data shows", "study found", "per "]
    with_basis = sum(1 for m in basis_markers if m.lower() in text.lower())
    # Each basis marker covers some claims
    return total, min(with_basis, total)


async def run_telemetry_gate(
    ingress_envelope: IngressPipelineEnvelope,
    egress_gate_results: list[GateResult],
    output_text: str,
    session_state: SessionState,
    telemetry_store: TelemetryStore,
    latency_ms: int,
    classifier_latency_ms: int,
    model_latency_ms: int,
    rerender_count: int,
    provisional: bool,
) -> tuple[GateResult, SessionState]:
    """
    Execute the TELEMETRY gate.
    Returns (GateResult, updated_session_state).
    ONLY gate that increments session_state.turn_index.
    """
    fired_at_ms = int(time.time() * 1000)
    now_ms = fired_at_ms

    request = ingress_envelope.request

    # Extract gate data
    icc_data: Optional[ICCGateData] = None
    astg_data: Optional[ASTGGateData] = None
    spm_data: Optional[SPMGateData] = None

    all_gate_results = ingress_envelope.gate_results + egress_gate_results
    gate_triggers_fired: list[GateId] = []

    for gr in all_gate_results:
        if gr.status not in (GateStatus.pass_,):
            gate_triggers_fired.append(gr.gate_id)
        if gr.gate_id == GateId.ICC and gr.gate_data:
            try:
                icc_data = ICCGateData.model_validate(gr.gate_data)
            except Exception:
                pass
        if gr.gate_id == GateId.ASTG and gr.gate_data:
            try:
                astg_data = ASTGGateData.model_validate(gr.gate_data)
            except Exception:
                pass
        if gr.gate_id == GateId.SPM and gr.gate_data:
            try:
                spm_data = SPMGateData.model_validate(gr.gate_data)
            except Exception:
                pass

    halt_triggered = any(
        gr.status in (GateStatus.halt, GateStatus.fail) for gr in all_gate_results
    )
    halt_reason_code: Optional[HaltReasonCode] = None
    for gr in all_gate_results:
        if gr.status in (GateStatus.halt, GateStatus.fail) and gr.halt_reason_code:
            halt_reason_code = gr.halt_reason_code
            break

    rerender_requested = any(gr.status == GateStatus.rerender for gr in all_gate_results)
    provisional_labeling_count = 1 if provisional else 0
    assumption_block_present = (astg_data is not None and astg_data.assumption_count > 0)

    numeric_claims, numeric_with_basis = _extract_numeric_claims(output_text)

    scope_violation_flags: list[str] = []
    for gr in all_gate_results:
        if gr.halt_reason_code in (HaltReasonCode.CRS_SCOPE_VIOLATION, HaltReasonCode.SCOPE_EXCEEDED):
            scope_violation_flags.append(gr.gate_id.value)

    spm_signal_a_count = len(session_state.spm_signal_a_turns)
    spm_signal_b_count = len(session_state.spm_signal_b_turns)
    spm_signal_c_count = len(session_state.spm_signal_c_turns)
    spm_threshold_crossed = spm_data.threshold_crossed if spm_data else False
    spm_fired = session_state.spm_fired
    spm_dispute_event = spm_data.dispute_detected if spm_data else False
    spm_dispute_signal_classification: Optional[str] = None

    # Build record
    record = TelemetryTurnRecord(
        session_id=request.session_id,
        turn_index=request.turn_index,
        personas_invoked=[session_state.active_persona],
        synthesis_mode=False,
        gate_triggers_fired=gate_triggers_fired,
        halt_triggered=halt_triggered,
        halt_reason_code=halt_reason_code,
        rerender_requested=rerender_requested,
        rerender_count=rerender_count,
        provisional_labeling_count=provisional_labeling_count,
        assumption_block_present=assumption_block_present,
        numeric_claims_count=numeric_claims,
        numeric_claims_with_basis_count=numeric_with_basis,
        scope_violation_flags=scope_violation_flags,
        spm_signal_a_count=spm_signal_a_count,
        spm_signal_b_count=spm_signal_b_count,
        spm_signal_c_count=spm_signal_c_count,
        spm_threshold_crossed=spm_threshold_crossed,
        spm_fired=spm_fired,
        spm_dispute_event=spm_dispute_event,
        spm_dispute_signal_classification=spm_dispute_signal_classification,
        latency_ms=latency_ms,
        classifier_latency_ms=classifier_latency_ms,
        model_latency_ms=model_latency_ms,
    )

    tel_data = TelemetryGateData(record_written=False, write_error=None)
    write_error: Optional[str] = None

    try:
        await telemetry_store.write_turn_record(record)
        tel_data = TelemetryGateData(record_written=True, write_error=None)
    except Exception as exc:
        write_error = str(exc)
        tel_data = TelemetryGateData(record_written=False, write_error=write_error)

    # Update session state — increment turn_index, set last_turn_completed_at_ms
    updated_state = session_state.model_copy(update={
        "turn_index": session_state.turn_index + 1,
        "last_turn_completed_at_ms": now_ms,
    })

    # Status: warn on failure (never block)
    if write_error:
        gate_result = GateResult(
            gate_id=GateId.TELEMETRY,
            status=GateStatus.warn,
            failure_class=FailureClass.class1,
            halt_reason_code=None,
            provisional_flag=False,
            assumption_declared=False,
            fired_at_ms=fired_at_ms,
            gate_data=tel_data.model_dump(),
        )
    else:
        gate_result = GateResult(
            gate_id=GateId.TELEMETRY,
            status=GateStatus.pass_,
            failure_class=FailureClass.none,
            halt_reason_code=None,
            provisional_flag=False,
            assumption_declared=False,
            fired_at_ms=fired_at_ms,
            gate_data=tel_data.model_dump(),
        )

    return gate_result, updated_state
