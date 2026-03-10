"""
PRAP Gate — Ingress position 6 (final)
Pre-Response Audit & Pre-flight Gate

Phase: Ingress
Inputs: all prior gate results, session_state, request
Reads all state fields, no writes
Halt if any prior gate was halt|fail
Halt MISSING_REQUIRED_INPUTS: scope not satisfiable
Halt MODE_LOCK_VIOLATION: mode lock violated
Halt CRS_SCOPE_VIOLATION: strict mode + scope violation
"""
from __future__ import annotations

import time

from cgs_runtime_wrapper.models.envelopes import (
    FailureClass,
    GateId,
    GateResult,
    GateStatus,
    HaltReasonCode,
    PRAPGateData,
    RequestEnvelope,
    SessionState,
)


async def run_prap_gate(
    prior_gate_results: list[GateResult],
    session_state: SessionState,
    request: RequestEnvelope,
) -> GateResult:
    """
    Execute the PRAP gate.
    Aggregates prior gate failures and validates pre-flight conditions.
    """
    fired_at_ms = int(time.time() * 1000)

    failed_checks: list[str] = []

    # Check 1: Any prior gate halt or fail
    for gr in prior_gate_results:
        if gr.status in (GateStatus.halt, GateStatus.fail):
            failed_checks.append(
                f"Prior gate {gr.gate_id.value} returned {gr.status.value}: "
                f"{gr.halt_reason_code.value if gr.halt_reason_code else 'no code'}"
            )

    # Check 2: Scope satisfiable
    scope_satisfiable = True
    if request.crs_scope:
        # If scope is set and not satisfiable (rules: always satisfiable in stub)
        scope_satisfiable = True  # stub: assume satisfiable

    # Check 3: Source fidelity satisfiable (stub: always true)
    source_fidelity_satisfiable = True

    # Check 4: Mode lock viable
    mode_lock_viable = True
    if session_state.mode_lock and request.mode_lock:
        if session_state.mode_lock != request.mode_lock:
            mode_lock_viable = False
            failed_checks.append(
                f"Mode lock conflict: session={session_state.mode_lock}, "
                f"request={request.mode_lock}"
            )

    # Check 5: Delegation boundary clean (stub: always true)
    delegation_boundary_clean = True

    # Check 6: CRS scope clean
    crs_scope_clean = True
    if request.crs_strict_mode and request.crs_scope:
        # In strict mode, scope must be explicitly set and consistent
        if session_state.crs_scope and session_state.crs_scope != request.crs_scope:
            crs_scope_clean = False
            failed_checks.append(
                f"CRS scope mismatch in strict mode: "
                f"session={session_state.crs_scope}, request={request.crs_scope}"
            )

    all_checks_passed = len(failed_checks) == 0

    prap_data = PRAPGateData(
        all_checks_passed=all_checks_passed,
        failed_checks=failed_checks,
        scope_satisfiable=scope_satisfiable,
        source_fidelity_satisfiable=source_fidelity_satisfiable,
        mode_lock_viable=mode_lock_viable,
        delegation_boundary_clean=delegation_boundary_clean,
        crs_scope_clean=crs_scope_clean,
    )

    if not all_checks_passed:
        # Determine most specific halt reason
        halt_reason = HaltReasonCode.MISSING_REQUIRED_INPUTS  # default
        failure_class = FailureClass.class1

        if not mode_lock_viable:
            halt_reason = HaltReasonCode.MODE_LOCK_VIOLATION
        elif not crs_scope_clean:
            halt_reason = HaltReasonCode.CRS_SCOPE_VIOLATION
        else:
            # Prior gate failure — re-use the first halt reason found
            for gr in prior_gate_results:
                if gr.status in (GateStatus.halt, GateStatus.fail) and gr.halt_reason_code:
                    halt_reason = gr.halt_reason_code
                    failure_class = gr.failure_class
                    break

        return GateResult(
            gate_id=GateId.PRAP,
            status=GateStatus.halt,
            failure_class=failure_class,
            halt_reason_code=halt_reason,
            provisional_flag=False,
            assumption_declared=False,
            fired_at_ms=fired_at_ms,
            gate_data=prap_data.model_dump(),
        )

    return GateResult(
        gate_id=GateId.PRAP,
        status=GateStatus.pass_,
        failure_class=FailureClass.none,
        halt_reason_code=None,
        provisional_flag=False,
        assumption_declared=False,
        fired_at_ms=fired_at_ms,
        gate_data=prap_data.model_dump(),
    )
