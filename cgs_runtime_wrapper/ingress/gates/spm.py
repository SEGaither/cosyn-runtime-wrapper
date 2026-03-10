"""
SPM Gate — Ingress position 5
Session Pattern Monitor

Phase: Ingress — NON-BLOCKING (always status: pass)
Threshold: all three signals within 5-turn window: A>=3, B>=1, C>=1
State reads: spm_signal_a/b/c_turns, spm_fired, spm_window_reset_at_turn, spm_suppress
State writes: spm_signal_a/b/c_turns (append if signal), spm_fired (set True), spm_fired_at_turn
RULES-BASED (full implementation)
"""
from __future__ import annotations

import time

from cgs_runtime_wrapper.classifier.spm_classifiers import (
    classify_signal_a,
    classify_signal_b,
    classify_signal_c,
)
from cgs_runtime_wrapper.models.envelopes import (
    EDHGateData,
    FailureClass,
    GateId,
    GateResult,
    GateStatus,
    ICCGateData,
    SessionState,
    SPMGateData,
)

SPM_WINDOW_SIZE = 5
SPM_THRESHOLD_A = 3
SPM_THRESHOLD_B = 1
SPM_THRESHOLD_C = 1

# SPM output format — exact per spec
_SPM_OUTPUT_TEMPLATE = """\
Session Pattern Monitor — Threshold Crossed

The SPM gate has fired. The following signals were detected within the last {window_size} turns:

- Signal A (confidence assertion, no new evidence): {a_count} instances — turns {a_turns}
- Signal B (request to adopt conclusion, no evidential basis): {b_count} instance — turn {b_turns}
- Signal C (position change requested, no new proposition introduced): {c_count} instance — turn {c_turns}

All three signal types are present. The minimum 5-turn window is satisfied.

This observation describes turn-level events. It does not assess the reason for those events.

The system's position on {topic} remains as stated in turn {last_position_turn}. To update that position,
introduce new evidence or argument in any subsequent turn."""


def _turns_in_window(
    signal_turns: list[int],
    current_turn: int,
    window_size: int,
    window_reset_at: int | None,
) -> list[int]:
    """Return turns within the active window."""
    window_start = current_turn - window_size + 1
    if window_reset_at is not None:
        window_start = max(window_start, window_reset_at)
    return [t for t in signal_turns if t >= window_start]


def _build_spm_output(
    session_state: SessionState,
    current_turn: int,
    window_turns_a: list[int],
    window_turns_b: list[int],
    window_turns_c: list[int],
    icc_gate_data: ICCGateData,
) -> str:
    topic = icc_gate_data.intent_primary[:80] if icc_gate_data.intent_primary else "this topic"
    # Last turn where the system stated its position — use earliest turn in window or turn 1
    last_position_turn = min(
        window_turns_a + window_turns_b + window_turns_c + [current_turn]
    )

    a_turns_str = str(window_turns_a) if window_turns_a else "[]"
    b_turns_str = str(window_turns_b[0]) if window_turns_b else "N/A"
    c_turns_str = str(window_turns_c[0]) if window_turns_c else "N/A"

    return _SPM_OUTPUT_TEMPLATE.format(
        window_size=SPM_WINDOW_SIZE,
        a_count=len(window_turns_a),
        a_turns=a_turns_str,
        b_count=len(window_turns_b),
        b_turns=b_turns_str,
        c_count=len(window_turns_c),
        c_turns=c_turns_str,
        topic=topic,
        last_position_turn=last_position_turn,
    )


async def run_spm_gate(
    raw_input: str,
    icc_gate_data: ICCGateData,
    edh_gate_data: EDHGateData | None,
    session_state: SessionState,
    turn_index: int,
) -> tuple[GateResult, SessionState]:
    """
    Execute the SPM gate. Always returns status: pass (non-blocking).
    Returns (GateResult, updated_session_state).
    """
    fired_at_ms = int(time.time() * 1000)

    # Classify signals for this turn
    signal_a_this_turn = classify_signal_a(raw_input) if not session_state.spm_suppress else False
    signal_b_this_turn = classify_signal_b(raw_input) if not session_state.spm_suppress else False
    signal_c_this_turn = classify_signal_c(raw_input) if not session_state.spm_suppress else False

    # Update signal turn lists
    new_a_turns = list(session_state.spm_signal_a_turns)
    new_b_turns = list(session_state.spm_signal_b_turns)
    new_c_turns = list(session_state.spm_signal_c_turns)

    if signal_a_this_turn:
        new_a_turns.append(turn_index)
    if signal_b_this_turn:
        new_b_turns.append(turn_index)
    if signal_c_this_turn:
        new_c_turns.append(turn_index)

    # Evaluate threshold within window
    window_reset = session_state.spm_window_reset_at_turn
    window_a = _turns_in_window(new_a_turns, turn_index, SPM_WINDOW_SIZE, window_reset)
    window_b = _turns_in_window(new_b_turns, turn_index, SPM_WINDOW_SIZE, window_reset)
    window_c = _turns_in_window(new_c_turns, turn_index, SPM_WINDOW_SIZE, window_reset)

    threshold_crossed = (
        len(window_a) >= SPM_THRESHOLD_A
        and len(window_b) >= SPM_THRESHOLD_B
        and len(window_c) >= SPM_THRESHOLD_C
    )

    # Dispute detection: Signal C present in same turn (challenge to SPM itself)
    # Per EC-04/EC-05 spec: detect when user disputes SPM observation
    dispute_detected = False
    dispute_response_text: str | None = None
    spm_output_text: str | None = None

    if threshold_crossed and not session_state.spm_fired:
        spm_output_text = _build_spm_output(
            session_state, turn_index, window_a, window_b, window_c, icc_gate_data
        )

    # Update session state
    updates: dict = {
        "spm_signal_a_turns": new_a_turns,
        "spm_signal_b_turns": new_b_turns,
        "spm_signal_c_turns": new_c_turns,
    }
    if threshold_crossed and not session_state.spm_fired:
        updates["spm_fired"] = True
        updates["spm_fired_at_turn"] = turn_index

    updated_state = session_state.model_copy(update=updates)

    window_turn_range: list[int] | None = None
    if window_a or window_b or window_c:
        all_window = window_a + window_b + window_c
        window_turn_range = [min(all_window), max(all_window)]

    spm_data = SPMGateData(
        signal_a_this_turn=signal_a_this_turn,
        signal_b_this_turn=signal_b_this_turn,
        signal_c_this_turn=signal_c_this_turn,
        threshold_crossed=threshold_crossed,
        dispute_detected=dispute_detected,
        spm_output_text=spm_output_text,
        window_turn_range=window_turn_range,
        dispute_response_text=dispute_response_text,
    )

    # SPM is always pass (non-blocking)
    return GateResult(
        gate_id=GateId.SPM,
        status=GateStatus.pass_,
        failure_class=FailureClass.none,
        halt_reason_code=None,
        provisional_flag=False,
        assumption_declared=False,
        fired_at_ms=fired_at_ms,
        gate_data=spm_data.model_dump(),
    ), updated_state
