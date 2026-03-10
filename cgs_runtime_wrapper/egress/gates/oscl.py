"""
OSCL Gate — Egress position 1
Output Scope & Claim Limiter

Thresholds: evidence_alignment>=0.7, user_constraint_adherence>=0.75, aggregate_score>=0.72
Status rerender if below threshold
Status halt (MISSING_REQUIRED_INPUTS) if scp_trigger
Status warn if rerender_count>=2 and still below threshold
STUB: return passing scores (0.85 across all axes)
"""
from __future__ import annotations

import time

from cgs_runtime_wrapper.models.envelopes import (
    ASTGGateData,
    FailureClass,
    GateId,
    GateResult,
    GateStatus,
    HaltReasonCode,
    ICCGateData,
    OSCLGateData,
)

_STUB_SCORE = 0.85

_THRESHOLD_EVIDENCE_ALIGNMENT = 0.70
_THRESHOLD_USER_CONSTRAINT_ADHERENCE = 0.75
_THRESHOLD_AGGREGATE = 0.72


async def run_oscl_gate(
    raw_output: str,
    icc_gate_data: ICCGateData | None,
    astg_gate_data: ASTGGateData | None,
    rerender_count: int,
) -> GateResult:
    """
    Execute the OSCL gate.
    STUB: returns passing scores (0.85) across all axes.
    """
    fired_at_ms = int(time.time() * 1000)

    # STUB: all scores at 0.85
    oscl_data = OSCLGateData(
        evidence_alignment=_STUB_SCORE,
        assumption_minimality=_STUB_SCORE,
        overclaim_risk_inverse=_STUB_SCORE,
        user_constraint_adherence=_STUB_SCORE,
        actionability_clarity=_STUB_SCORE,
        aggregate_score=_STUB_SCORE,
        revision_required=False,
        scp_trigger=False,
        lowest_scoring_axes=None,
    )

    # SCP trigger → halt
    if oscl_data.scp_trigger:
        return GateResult(
            gate_id=GateId.OSCL,
            status=GateStatus.halt,
            failure_class=FailureClass.class1,
            halt_reason_code=HaltReasonCode.MISSING_REQUIRED_INPUTS,
            provisional_flag=False,
            assumption_declared=False,
            fired_at_ms=fired_at_ms,
            gate_data=oscl_data.model_dump(),
        )

    # Check thresholds
    below_threshold = (
        oscl_data.evidence_alignment < _THRESHOLD_EVIDENCE_ALIGNMENT
        or oscl_data.user_constraint_adherence < _THRESHOLD_USER_CONSTRAINT_ADHERENCE
        or oscl_data.aggregate_score < _THRESHOLD_AGGREGATE
    )

    if below_threshold:
        if rerender_count >= 2:
            # Warn but do not block further (rerender limit handled at router level)
            return GateResult(
                gate_id=GateId.OSCL,
                status=GateStatus.warn,
                failure_class=FailureClass.class1,
                halt_reason_code=None,
                provisional_flag=True,
                assumption_declared=False,
                fired_at_ms=fired_at_ms,
                rerender_reason="OSCL scores below threshold after max rerenders",
                gate_data=oscl_data.model_dump(),
            )
        return GateResult(
            gate_id=GateId.OSCL,
            status=GateStatus.rerender,
            failure_class=FailureClass.class1,
            halt_reason_code=None,
            provisional_flag=False,
            assumption_declared=False,
            fired_at_ms=fired_at_ms,
            rerender_reason="OSCL scores below minimum threshold",
            gate_data=oscl_data.model_dump(),
        )

    return GateResult(
        gate_id=GateId.OSCL,
        status=GateStatus.pass_,
        failure_class=FailureClass.none,
        halt_reason_code=None,
        provisional_flag=False,
        assumption_declared=False,
        fired_at_ms=fired_at_ms,
        gate_data=oscl_data.model_dump(),
    )
