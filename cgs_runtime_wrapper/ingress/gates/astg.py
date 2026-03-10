"""
ASTG Gate — Ingress position 2
Assumption Stability & Transparency Gate

Phase: Ingress
Pass: all assumptions explicitly identified
Halt UNDECLARED_ASSUMPTION: undeclared assumption required to proceed
Warn (provisional_flag=True): unstable assumption detected
No state mutation (assumption block injected into model prompt by router)
MODEL-BASED (stub): rules-based placeholder
"""
from __future__ import annotations

import time

from cgs_runtime_wrapper.classifier.astg_classifier import run_astg_classifier
from cgs_runtime_wrapper.models.envelopes import (
    ASTGGateData,
    FailureClass,
    GateId,
    GateResult,
    GateStatus,
    HaltReasonCode,
    ICCGateData,
)


async def run_astg_gate(
    raw_input: str,
    icc_gate_data: ICCGateData,
    crs_scope: str | None,
) -> GateResult:
    """
    Execute the ASTG gate.
    Returns GateResult with gate_data containing ASTGGateData fields.
    """
    fired_at_ms = int(time.time() * 1000)

    # Run classifier (stub)
    astg_data: ASTGGateData = run_astg_classifier(raw_input, icc_gate_data, crs_scope)

    # Stub always returns 0 assumptions → pass
    # In production: if assumption required but undeclared → halt
    # For now: check if unstable assumptions detected → warn
    if astg_data.unstable_assumption_present:
        return GateResult(
            gate_id=GateId.ASTG,
            status=GateStatus.warn,
            failure_class=FailureClass.none,
            halt_reason_code=None,
            provisional_flag=True,
            assumption_declared=astg_data.assumption_count > 0,
            fired_at_ms=fired_at_ms,
            gate_data=astg_data.model_dump(),
        )

    return GateResult(
        gate_id=GateId.ASTG,
        status=GateStatus.pass_,
        failure_class=FailureClass.none,
        halt_reason_code=None,
        provisional_flag=False,
        assumption_declared=astg_data.assumption_count > 0,
        fired_at_ms=fired_at_ms,
        gate_data=astg_data.model_dump(),
    )
