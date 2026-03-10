"""
EDH Gate — Ingress position 4
Echo Detection & Handling Gate

Phase: Ingress
Pass: no echo OR first echo detection (warn only)
Halt ECHO_REPETITION: echo + edh_fired=True + no new evidence
State reads: edh_buffer, edh_fired
State writes: edh_buffer (append, trim to 10), edh_fired (set True if echo)
EMBEDDING-BASED (stub): similarity_score=0.0
"""
from __future__ import annotations

import time

from cgs_runtime_wrapper.classifier.edh_similarity import compute_max_similarity
from cgs_runtime_wrapper.models.envelopes import (
    EDHBufferEntry,
    EDHGateData,
    EchoType,
    FailureClass,
    GateId,
    GateResult,
    GateStatus,
    HaltReasonCode,
    ICCGateData,
    SessionState,
)

# Echo detection threshold
_ECHO_SIMILARITY_THRESHOLD = 0.85


async def run_edh_gate(
    raw_input: str,
    icc_gate_data: ICCGateData,
    session_state: SessionState,
    turn_index: int,
) -> tuple[GateResult, SessionState]:
    """
    Execute the EDH gate.
    Returns (GateResult, updated_session_state).
    State writes: edh_buffer, edh_fired.
    """
    fired_at_ms = int(time.time() * 1000)

    edh_buffer = list(session_state.edh_buffer)
    edh_fired = session_state.edh_fired

    # Compute similarity against buffer (stub: always 0.0)
    similarity_score, embedding = compute_max_similarity(raw_input, edh_buffer)

    echo_detected = similarity_score >= _ECHO_SIMILARITY_THRESHOLD
    forced_reframe_required = False
    external_anchor_check_triggered = False
    ecfd_triggered = False
    echo_type: EchoType | None = None

    if echo_detected:
        echo_type = EchoType.semantic_repetition
        external_anchor_check_triggered = True

        if edh_fired:
            # Second echo without new evidence → halt
            forced_reframe_required = True
            ecfd_triggered = True

            edh_data = EDHGateData(
                echo_detected=True,
                similarity_score=similarity_score,
                forced_reframe_required=True,
                external_anchor_check_triggered=True,
                ecfd_triggered=True,
                echo_type=echo_type,
            )
            return GateResult(
                gate_id=GateId.EDH,
                status=GateStatus.halt,
                failure_class=FailureClass.class1,
                halt_reason_code=HaltReasonCode.ECHO_REPETITION,
                provisional_flag=False,
                assumption_declared=False,
                fired_at_ms=fired_at_ms,
                gate_data=edh_data.model_dump(),
            ), session_state

        # First echo — warn only, set edh_fired
        session_state = session_state.model_copy(update={"edh_fired": True})

    # Append to buffer (always append current turn summary)
    new_entry = EDHBufferEntry(
        turn_index=turn_index,
        conclusion_embedding=embedding,
        conclusion_summary=icc_gate_data.intent_primary[:500],
    )
    new_buffer = edh_buffer + [new_entry]
    # Trim to max 10 entries (oldest first)
    if len(new_buffer) > 10:
        new_buffer = new_buffer[-10:]

    session_state = session_state.model_copy(update={"edh_buffer": new_buffer})

    edh_data = EDHGateData(
        echo_detected=echo_detected,
        similarity_score=similarity_score,
        forced_reframe_required=forced_reframe_required,
        external_anchor_check_triggered=external_anchor_check_triggered,
        ecfd_triggered=ecfd_triggered,
        echo_type=echo_type,
    )

    if echo_detected:
        # First detection — warn
        return GateResult(
            gate_id=GateId.EDH,
            status=GateStatus.warn,
            failure_class=FailureClass.none,
            halt_reason_code=None,
            provisional_flag=False,
            assumption_declared=False,
            fired_at_ms=fired_at_ms,
            gate_data=edh_data.model_dump(),
        ), session_state

    return GateResult(
        gate_id=GateId.EDH,
        status=GateStatus.pass_,
        failure_class=FailureClass.none,
        halt_reason_code=None,
        provisional_flag=False,
        assumption_declared=False,
        fired_at_ms=fired_at_ms,
        gate_data=edh_data.model_dump(),
    ), session_state
