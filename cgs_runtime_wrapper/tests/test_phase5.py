"""
Phase 5 Tests — Egress pipeline.
Tests:
- Rerender on lexical violation
- NFAR returns exactly "Standing by."
- EOS snapshot completeness
- Trace This field coverage
"""
from __future__ import annotations

import time
import pytest

from cgs_runtime_wrapper.adapters.model_adapter import StubModelAdapter
from cgs_runtime_wrapper.egress.gates.finalization import run_finalization_gate
from cgs_runtime_wrapper.egress.router import (
    run_egress_pipeline,
    _is_nfar,
    _is_eos,
    _is_trace_this,
    _STANDING_BY,
)
from cgs_runtime_wrapper.ingress.router import run_ingress_pipeline
from cgs_runtime_wrapper.models.envelopes import (
    ConstraintConsistency,
    FailureClass,
    GateId,
    GateResult,
    GateStatus,
    HaltReasonCode,
    ICCGateData,
    IngressPipelineEnvelope,
    PipelineStatusIngress,
    RequestEnvelope,
    SessionState,
)
from cgs_runtime_wrapper.state.session_store import SessionStore
from cgs_runtime_wrapper.telemetry.store import TelemetryStore

from cgs_runtime_wrapper.tests.conftest import FakeRedis


def make_fake_stores():
    redis = FakeRedis()
    return SessionStore(redis), TelemetryStore(redis)


def make_session(session_id: str = "s1") -> SessionState:
    return SessionState(
        session_id=session_id,
        cgs_version="1.0.0",
        wrapper_version="0.1.0",
        session_started_at_ms=int(time.time() * 1000),
    )


def make_request(raw_input: str = "Help me.", turn_index: int = 1) -> RequestEnvelope:
    return RequestEnvelope(
        session_id="s1",
        turn_index=turn_index,
        raw_input=raw_input,
        wrapper_version="0.1.0",
        cgs_version="1.0.0",
    )


def make_passing_ingress_envelope(request: RequestEnvelope) -> IngressPipelineEnvelope:
    """Create a minimal passing IngressPipelineEnvelope."""
    return IngressPipelineEnvelope(
        request=request,
        gate_results=[
            GateResult(
                gate_id=GateId.PRAP,
                status=GateStatus.pass_,
                failure_class=FailureClass.none,
                halt_reason_code=None,
                provisional_flag=False,
                assumption_declared=False,
                fired_at_ms=int(time.time() * 1000),
            )
        ],
        pipeline_status=PipelineStatusIngress.proceed,
        halt_response=None,
        model_prompt="Process this request.",
        active_persona="Core",
        ingress_completed_at_ms=int(time.time() * 1000),
    )


# ---------------------------------------------------------------------------
# NFAR handler
# ---------------------------------------------------------------------------

def test_nfar_detection_exact():
    """'NFAR' should be detected."""
    assert _is_nfar("NFAR") is True


def test_nfar_detection_lowercase():
    """'nfar' should be detected."""
    assert _is_nfar("nfar") is True


def test_nfar_detection_phrase():
    """'no further action required' should be detected."""
    assert _is_nfar("No further action required.") is True


def test_not_nfar():
    """Normal output should not trigger NFAR."""
    assert _is_nfar("Here is the analysis you requested.") is False


@pytest.mark.asyncio
async def test_nfar_returns_exactly_standing_by():
    """NFAR output must be EXACTLY 'Standing by.' (with headers)."""
    session_store, telemetry_store = make_fake_stores()
    stub_model = StubModelAdapter("NFAR")
    request = make_request("Acknowledged.")
    state = make_session()
    ingress = make_passing_ingress_envelope(request)

    output, _ = await run_egress_pipeline(
        ingress_envelope=ingress,
        session_state=state,
        model_adapter=stub_model,
        session_store=session_store,
        telemetry_store=telemetry_store,
        turn_start_ms=int(time.time() * 1000),
    )

    # The emission should contain "Standing by." (with persona headers prepended)
    assert _STANDING_BY in output.emission


@pytest.mark.asyncio
async def test_nfar_emission_exact_after_strip():
    """Standing by. must appear verbatim in emission content."""
    session_store, telemetry_store = make_fake_stores()
    stub_model = StubModelAdapter("nfar")
    request = make_request("OK, noted.")
    state = make_session()
    ingress = make_passing_ingress_envelope(request)

    output, _ = await run_egress_pipeline(
        ingress_envelope=ingress,
        session_state=state,
        model_adapter=stub_model,
        session_store=session_store,
        telemetry_store=telemetry_store,
        turn_start_ms=int(time.time() * 1000),
    )

    assert "Standing by." in output.emission


# ---------------------------------------------------------------------------
# EOS handler
# ---------------------------------------------------------------------------

def test_eos_detection():
    """'EOS' should be detected."""
    assert _is_eos("EOS") is True


def test_eos_not_triggered_by_normal_output():
    """Normal output should not trigger EOS."""
    assert _is_eos("This is the end of the analysis.") is False


@pytest.mark.asyncio
async def test_eos_resets_session():
    """EOS should reset session state."""
    session_store, telemetry_store = make_fake_stores()
    stub_model = StubModelAdapter("EOS")

    state = make_session()
    # Pre-populate session
    state = state.model_copy(update={"turn_index": 3, "spm_fired": True})
    await session_store.put(state)

    request = make_request("We are done here.")
    ingress = make_passing_ingress_envelope(request)

    output, updated_state = await run_egress_pipeline(
        ingress_envelope=ingress,
        session_state=state,
        model_adapter=stub_model,
        session_store=session_store,
        telemetry_store=telemetry_store,
        turn_start_ms=int(time.time() * 1000),
    )

    # Session should be reset
    fresh = await session_store.get("s1")
    assert fresh is not None
    # After reset, turn_index should be 0
    assert fresh.turn_index == 0


@pytest.mark.asyncio
async def test_eos_snapshot_completeness():
    """EOS snapshot should contain session_state, turn_records, rollup."""
    from cgs_runtime_wrapper.egress.router import _assemble_session_snapshot

    redis = FakeRedis()
    telemetry_store = TelemetryStore(redis)
    # Use a session with the same session_id as the telemetry records
    state = make_session(session_id="s1")

    from cgs_runtime_wrapper.tests.conftest import make_turn_record
    record = make_turn_record(session_id="s1", turn_index=1)
    await telemetry_store.write_turn_record(record)

    snapshot = await _assemble_session_snapshot(state, telemetry_store)
    assert "session_state" in snapshot
    assert "turn_records" in snapshot
    assert "rollup" in snapshot
    assert len(snapshot["turn_records"]) == 1


# ---------------------------------------------------------------------------
# Trace This
# ---------------------------------------------------------------------------

def test_trace_this_detection():
    """'trace this' should be detected."""
    assert _is_trace_this("trace this") is True
    assert _is_trace_this("Can you trace this session?") is True


def test_trace_this_not_triggered():
    """Normal input should not trigger trace this."""
    assert _is_trace_this("What is the weather today?") is False


@pytest.mark.asyncio
async def test_trace_this_returns_audit_ledger():
    """Trace This should return audit ledger with required fields."""
    from cgs_runtime_wrapper.egress.router import _assemble_audit_ledger

    redis = FakeRedis()
    telemetry_store = TelemetryStore(redis)

    from cgs_runtime_wrapper.tests.conftest import make_turn_record
    await telemetry_store.write_turn_record(make_turn_record(turn_index=1))
    await telemetry_store.write_turn_record(make_turn_record(turn_index=2, halt=True))

    ledger = await _assemble_audit_ledger("test-session-001", telemetry_store)

    assert "AUDIT LEDGER" in ledger
    assert "test-session-001" in ledger
    assert "Total turns" in ledger
    assert "Halt rate" in ledger
    assert "SPM" in ledger


@pytest.mark.asyncio
async def test_trace_this_pipeline_integration():
    """Trace This request should return audit ledger via egress pipeline."""
    session_store, telemetry_store = make_fake_stores()
    stub_model = StubModelAdapter("Some normal response")

    from cgs_runtime_wrapper.tests.conftest import make_turn_record
    await telemetry_store.write_turn_record(make_turn_record(turn_index=1))

    request = make_request("Can you trace this session for me?")
    state = make_session()
    ingress = make_passing_ingress_envelope(request)

    output, _ = await run_egress_pipeline(
        ingress_envelope=ingress,
        session_state=state,
        model_adapter=stub_model,
        session_store=session_store,
        telemetry_store=telemetry_store,
        turn_start_ms=int(time.time() * 1000),
    )

    assert "AUDIT LEDGER" in output.emission


# ---------------------------------------------------------------------------
# Finalization rerender on lexical violation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_finalization_rerender_on_lexical_violation():
    """Finalization should return rerender when lexical violations found."""
    request = make_request()
    state = make_session()

    # Output with prohibited pattern
    violating_output = (
        "You are trying to push this agenda without providing evidence.\n"
        "Here is the analysis you requested."
    )

    result, _ = await run_finalization_gate(
        raw_output=violating_output,
        request=request,
        session_state=state,
        rerender_count=0,
        has_provisional=False,
    )

    assert result.status == GateStatus.rerender
    assert result.gate_data is not None
    from cgs_runtime_wrapper.models.envelopes import FinalizationGateData
    fin_data = FinalizationGateData.model_validate(result.gate_data)
    assert fin_data.spm_lexical_compliant is False
    assert fin_data.lexical_violations_found is not None
    assert len(fin_data.lexical_violations_found) > 0


@pytest.mark.asyncio
async def test_finalization_pass_on_clean_output():
    """Finalization should pass on clean output with persona headers."""
    request = make_request()
    state = make_session()

    clean_output = (
        "Router (control-plane): Stack Architect\n"
        "Active persona (this turn): Core\n\n"
        "Here is a clear and helpful response to your question."
    )

    result, _ = await run_finalization_gate(
        raw_output=clean_output,
        request=request,
        session_state=state,
        rerender_count=0,
        has_provisional=False,
    )

    assert result.status == GateStatus.pass_
