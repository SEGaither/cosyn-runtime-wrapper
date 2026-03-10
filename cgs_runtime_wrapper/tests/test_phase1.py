"""
Phase 1 Tests — Session store, telemetry store, and schema validation.

Tests:
- SessionState persistence across turns
- TTL expiry behavior
- Reset on EOS (retain session_id, reset all other fields)
- Field type enforcement
- TelemetryTurnRecord rejection of non-schema fields
- Rollup aggregation calculation
"""
from __future__ import annotations

import time
import pytest
from pydantic import ValidationError

from cgs_runtime_wrapper.models.envelopes import (
    EDHBufferEntry,
    FailureClass,
    GateId,
    GateStatus,
    HaltReasonCode,
    SessionState,
    TelemetrySessionRollup,
    TelemetryTurnRecord,
)
from cgs_runtime_wrapper.tests.conftest import make_turn_record


# ---------------------------------------------------------------------------
# SessionState persistence across turns
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_session_persistence_across_turns(session_store):
    """Session state should persist and be retrievable between turns."""
    state = await session_store.create(
        session_id="persist-test",
        cgs_version="1.0.0",
        wrapper_version="0.1.0",
    )
    assert state.turn_index == 0

    # Update turn_index
    updated = state.model_copy(update={"turn_index": 1, "spm_signal_a_turns": [1]})
    await session_store.put(updated)

    retrieved = await session_store.get("persist-test")
    assert retrieved is not None
    assert retrieved.turn_index == 1
    assert retrieved.spm_signal_a_turns == [1]


@pytest.mark.asyncio
async def test_session_updates_accumulate(session_store):
    """Signal turn lists should accumulate across multiple puts."""
    state = await session_store.create(
        session_id="accum-test",
        cgs_version="1.0.0",
        wrapper_version="0.1.0",
    )

    for turn in range(1, 4):
        state = state.model_copy(update={
            "turn_index": turn,
            "spm_signal_a_turns": state.spm_signal_a_turns + [turn],
        })
        await session_store.put(state)

    final = await session_store.get("accum-test")
    assert final is not None
    assert final.spm_signal_a_turns == [1, 2, 3]
    assert final.turn_index == 3


# ---------------------------------------------------------------------------
# TTL expiry behavior
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_session_ttl_stored(session_store, fake_redis):
    """TTL should be set on the Redis key."""
    await session_store.create(
        session_id="ttl-test",
        cgs_version="1.0.0",
        wrapper_version="0.1.0",
    )
    # Check TTL was registered in fake_redis
    key = "session:ttl-test"
    assert fake_redis._ttls.get(key) == 3600


@pytest.mark.asyncio
async def test_session_missing_returns_none(session_store):
    """Non-existent session should return None."""
    result = await session_store.get("nonexistent-session")
    assert result is None


@pytest.mark.asyncio
async def test_session_custom_ttl(session_store, fake_redis):
    """Custom TTL should be stored and applied."""
    state = SessionState(
        session_id="custom-ttl",
        cgs_version="1.0.0",
        wrapper_version="0.1.0",
        ttl_seconds=7200,
        session_started_at_ms=int(time.time() * 1000),
    )
    await session_store.put(state)
    assert fake_redis._ttls.get("session:custom-ttl") == 7200


# ---------------------------------------------------------------------------
# Reset on EOS — retain session_id, reset all other fields
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_session_reset_preserves_session_id(session_store):
    """Reset should create a fresh state but preserve session_id."""
    await session_store.create(
        session_id="reset-test",
        cgs_version="1.0.0",
        wrapper_version="0.1.0",
    )
    # Mutate state
    state = await session_store.get("reset-test")
    state = state.model_copy(update={
        "turn_index": 5,
        "spm_signal_a_turns": [1, 2, 3],
        "spm_fired": True,
        "edh_fired": True,
    })
    await session_store.put(state)

    # Reset
    fresh = await session_store.reset("reset-test")
    assert fresh.session_id == "reset-test"
    assert fresh.turn_index == 0
    assert fresh.spm_signal_a_turns == []
    assert fresh.spm_fired is False
    assert fresh.edh_fired is False


@pytest.mark.asyncio
async def test_session_reset_retains_versions(session_store):
    """Reset should retain cgs_version and wrapper_version."""
    await session_store.create(
        session_id="ver-reset",
        cgs_version="2.0.0",
        wrapper_version="0.2.0",
    )
    fresh = await session_store.reset("ver-reset")
    assert fresh.cgs_version == "2.0.0"
    assert fresh.wrapper_version == "0.2.0"


# ---------------------------------------------------------------------------
# Field type enforcement
# ---------------------------------------------------------------------------

def test_session_state_turn_index_non_negative():
    """turn_index must be >= 0."""
    with pytest.raises(ValidationError):
        SessionState(
            session_id="s",
            cgs_version="1.0",
            wrapper_version="0.1",
            turn_index=-1,
            session_started_at_ms=0,
        )


def test_session_state_confidence_register_bounds():
    """ccd_confidence_register must be between 0 and 1."""
    with pytest.raises(ValidationError):
        SessionState(
            session_id="s",
            cgs_version="1.0",
            wrapper_version="0.1",
            ccd_confidence_register=1.5,
            session_started_at_ms=0,
        )
    with pytest.raises(ValidationError):
        SessionState(
            session_id="s",
            cgs_version="1.0",
            wrapper_version="0.1",
            ccd_confidence_register=-0.1,
            session_started_at_ms=0,
        )


def test_edh_buffer_entry_turn_index_ge_1():
    """EDHBufferEntry.turn_index must be >= 1."""
    with pytest.raises(ValidationError):
        EDHBufferEntry(
            turn_index=0,
            conclusion_embedding=[0.0],
            conclusion_summary="test",
        )


# ---------------------------------------------------------------------------
# TelemetryTurnRecord — additionalProperties: false
# ---------------------------------------------------------------------------

def test_telemetry_record_rejects_extra_fields():
    """TelemetryTurnRecord must reject extra fields (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        TelemetryTurnRecord(
            session_id="s",
            turn_index=1,
            personas_invoked=["Core"],
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
            spm_signal_a_count=0,
            spm_signal_b_count=0,
            spm_signal_c_count=0,
            spm_threshold_crossed=False,
            spm_fired=False,
            spm_dispute_event=False,
            spm_dispute_signal_classification=None,
            latency_ms=100,
            classifier_latency_ms=10,
            model_latency_ms=80,
            unexpected_extra_field="should_fail",  # not in schema
        )


def test_telemetry_record_accepts_valid_fields():
    """Valid TelemetryTurnRecord should instantiate without error."""
    record = make_turn_record()
    assert record.session_id == "test-session-001"
    assert record.turn_index == 1


# ---------------------------------------------------------------------------
# Rollup aggregation calculation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rollup_halt_rate(telemetry_store):
    """Rollup halt_rate should match proportion of halted turns."""
    records = [
        make_turn_record(turn_index=1, halt=True),
        make_turn_record(turn_index=2, halt=True),
        make_turn_record(turn_index=3, halt=False),
        make_turn_record(turn_index=4, halt=False),
    ]
    for r in records:
        await telemetry_store.write_turn_record(r)

    rollup = await telemetry_store.build_rollup("test-session-001")
    assert rollup.total_turns == 4
    assert abs(rollup.halt_rate - 0.5) < 0.001


@pytest.mark.asyncio
async def test_rollup_rerender_rate(telemetry_store):
    """Rollup rerender_rate should match proportion of rerendered turns."""
    records = [
        make_turn_record(turn_index=1, rerender=True),
        make_turn_record(turn_index=2, rerender=False),
        make_turn_record(turn_index=3, rerender=False),
    ]
    for r in records:
        await telemetry_store.write_turn_record(r)

    rollup = await telemetry_store.build_rollup("test-session-001")
    assert abs(rollup.rerender_rate - (1 / 3)) < 0.001


@pytest.mark.asyncio
async def test_rollup_spm_fire_count(telemetry_store):
    """spm_fire_count should count turns where spm_fired=True."""
    records = [
        make_turn_record(turn_index=1, spm_fired=True),
        make_turn_record(turn_index=2, spm_fired=True),
        make_turn_record(turn_index=3, spm_fired=False),
    ]
    for r in records:
        await telemetry_store.write_turn_record(r)

    rollup = await telemetry_store.build_rollup("test-session-001")
    assert rollup.spm_fire_count == 2


@pytest.mark.asyncio
async def test_rollup_empty_session(telemetry_store):
    """Rollup for session with no records should have zero rates."""
    rollup = await telemetry_store.build_rollup("empty-session")
    assert rollup.total_turns == 0
    assert rollup.halt_rate == 0.0
    assert rollup.spm_fire_count == 0
