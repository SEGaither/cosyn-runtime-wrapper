"""
ICC Gate — Ingress position 1
Intent & Constraint Classification

Phase: Ingress
Pass: explicit goal extractable, clauses consistent
Halt AMBIGUOUS_INTENT: ambiguous intent
Halt CONSTRAINT_CONFLICT: conflicting constraints
No state mutation
MODEL-BASED (stub): rules-based placeholder
"""
from __future__ import annotations

import time

from cgs_runtime_wrapper.classifier.icc_classifier import run_icc_classifier
from cgs_runtime_wrapper.models.envelopes import (
    ConstraintConsistency,
    FailureClass,
    GateId,
    GateResult,
    GateStatus,
    HaltReasonCode,
    ICCGateData,
)


async def run_icc_gate(
    raw_input: str,
    crs_scope: str | None,
    turn_index: int,
) -> GateResult:
    """
    Execute the ICC gate.
    Returns GateResult with gate_data containing ICCGateData fields.
    """
    fired_at_ms = int(time.time() * 1000)

    # Run classifier (stub)
    icc_data: ICCGateData = run_icc_classifier(raw_input, crs_scope)

    # Determine gate status based on constraint_consistency
    if icc_data.constraint_consistency == ConstraintConsistency.conflicting:
        return GateResult(
            gate_id=GateId.ICC,
            status=GateStatus.halt,
            failure_class=FailureClass.class1,
            halt_reason_code=HaltReasonCode.CONSTRAINT_CONFLICT,
            provisional_flag=False,
            assumption_declared=False,
            fired_at_ms=fired_at_ms,
            gate_data=icc_data.model_dump(),
        )

    if icc_data.constraint_consistency == ConstraintConsistency.ambiguous:
        # Class 0 on silent resolution attempt
        return GateResult(
            gate_id=GateId.ICC,
            status=GateStatus.halt,
            failure_class=FailureClass.class0,
            halt_reason_code=HaltReasonCode.AMBIGUOUS_INTENT,
            provisional_flag=False,
            assumption_declared=False,
            fired_at_ms=fired_at_ms,
            gate_data=icc_data.model_dump(),
        )

    # Pass
    return GateResult(
        gate_id=GateId.ICC,
        status=GateStatus.pass_,
        failure_class=FailureClass.none,
        halt_reason_code=None,
        provisional_flag=icc_data.provisional_flag,
        assumption_declared=False,
        fired_at_ms=fired_at_ms,
        gate_data=icc_data.model_dump(),
    )
