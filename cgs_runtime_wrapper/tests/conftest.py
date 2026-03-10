"""
Shared test fixtures for CGS Runtime Wrapper tests.
Uses fakeredis for in-memory Redis simulation (no real Redis required).
"""
from __future__ import annotations

import time
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from cgs_runtime_wrapper.models.envelopes import (
    RequestEnvelope,
    SessionState,
    TelemetryTurnRecord,
    GateResult,
    GateId,
    GateStatus,
    FailureClass,
)
from cgs_runtime_wrapper.adapters.model_adapter import StubModelAdapter
from cgs_runtime_wrapper.state.session_store import SessionStore
from cgs_runtime_wrapper.telemetry.store import TelemetryStore


# ---------------------------------------------------------------------------
# Fake Redis (in-memory dict-backed)
# ---------------------------------------------------------------------------

class FakeRedis:
    """Minimal async in-memory Redis fake for testing."""

    def __init__(self):
        self._data: dict = {}
        self._lists: dict = {}
        self._ttls: dict = {}

    async def get(self, key: str):
        return self._data.get(key)

    async def set(self, key: str, value, ex: int | None = None):
        self._data[key] = value
        if ex is not None:
            self._ttls[key] = ex

    async def delete(self, *keys: str):
        for k in keys:
            self._data.pop(k, None)
            self._lists.pop(k, None)

    async def exists(self, key: str) -> int:
        return 1 if key in self._data else 0

    async def rpush(self, key: str, *values):
        if key not in self._lists:
            self._lists[key] = []
        for v in values:
            self._lists[key].append(str(v))
        return len(self._lists[key])

    async def lrange(self, key: str, start: int, end: int) -> list:
        lst = self._lists.get(key, [])
        if end == -1:
            return lst[start:]
        return lst[start:end + 1]

    async def aclose(self):
        pass


@pytest.fixture
def fake_redis():
    return FakeRedis()


@pytest.fixture
def session_store(fake_redis):
    return SessionStore(redis_client=fake_redis)


@pytest.fixture
def telemetry_store(fake_redis):
    return TelemetryStore(redis_client=fake_redis)


@pytest.fixture
def stub_model():
    return StubModelAdapter("This is a stub response from the model.")


@pytest.fixture
def base_session_state():
    return SessionState(
        session_id="test-session-001",
        cgs_version="1.0.0",
        wrapper_version="0.1.0",
        session_started_at_ms=int(time.time() * 1000),
    )


@pytest.fixture
def base_request():
    return RequestEnvelope(
        session_id="test-session-001",
        turn_index=1,
        raw_input="Please help me understand this concept.",
        wrapper_version="0.1.0",
        cgs_version="1.0.0",
    )


@pytest.fixture
def passing_gate_result():
    return GateResult(
        gate_id=GateId.ICC,
        status=GateStatus.pass_,
        failure_class=FailureClass.none,
        halt_reason_code=None,
        provisional_flag=False,
        assumption_declared=False,
        fired_at_ms=int(time.time() * 1000),
    )


def make_turn_record(
    session_id: str = "test-session-001",
    turn_index: int = 1,
    halt: bool = False,
    rerender: bool = False,
    provisional: bool = False,
    spm_a: int = 0,
    spm_b: int = 0,
    spm_c: int = 0,
    spm_fired: bool = False,
) -> TelemetryTurnRecord:
    return TelemetryTurnRecord(
        session_id=session_id,
        turn_index=turn_index,
        personas_invoked=["Core"],
        synthesis_mode=False,
        gate_triggers_fired=[],
        halt_triggered=halt,
        halt_reason_code=None,
        rerender_requested=rerender,
        rerender_count=1 if rerender else 0,
        provisional_labeling_count=1 if provisional else 0,
        assumption_block_present=False,
        numeric_claims_count=0,
        numeric_claims_with_basis_count=0,
        scope_violation_flags=[],
        spm_signal_a_count=spm_a,
        spm_signal_b_count=spm_b,
        spm_signal_c_count=spm_c,
        spm_threshold_crossed=False,
        spm_fired=spm_fired,
        spm_dispute_event=False,
        spm_dispute_signal_classification=None,
        latency_ms=100,
        classifier_latency_ms=10,
        model_latency_ms=80,
    )
