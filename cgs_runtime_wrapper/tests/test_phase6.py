"""
Phase 6 Tests — Audit layer and governance regression detector.
Tests:
- Regression detector fires on simulated degradation
- Trace This completeness
- Anonymization verified
"""
from __future__ import annotations

import pytest

from cgs_runtime_wrapper.audit.regression import GovernanceRegressionDetector
from cgs_runtime_wrapper.models.envelopes import TelemetrySessionRollup
from cgs_runtime_wrapper.telemetry.store import TelemetryStore
from cgs_runtime_wrapper.tests.conftest import FakeRedis, make_turn_record


def make_rollup(
    session_id: str = "s1",
    halt_rate: float = 0.0,
    class0_failure_count: int = 0,
    total_turns: int = 10,
    **overrides,
) -> TelemetrySessionRollup:
    base = {
        "session_id": session_id,
        "total_turns": total_turns,
        "halt_rate": halt_rate,
        "rerender_rate": 0.0,
        "provisional_rate": 0.0,
        "assumption_rate": 0.0,
        "spm_fire_count": 0,
        "spm_dispute_count": 0,
        "spm_retraction_count": 0,
        "class0_failure_count": class0_failure_count,
        "class1_failure_count": 0,
        "governance_regression_flag": False,
    }
    base.update(overrides)
    return TelemetrySessionRollup(**base)


# ---------------------------------------------------------------------------
# Regression detector
# ---------------------------------------------------------------------------

def test_regression_fires_on_halt_rate_degradation():
    """Halt rate increase >20% vs baseline should trigger regression flag."""
    detector = GovernanceRegressionDetector()
    baseline = make_rollup(halt_rate=0.10)
    current = make_rollup(halt_rate=0.13)  # 30% increase

    result = detector.detect(current, baseline)
    assert result.governance_regression_flag is True


def test_regression_no_flag_on_small_increase():
    """Halt rate increase <=20% should NOT trigger regression flag."""
    detector = GovernanceRegressionDetector()
    baseline = make_rollup(halt_rate=0.10)
    current = make_rollup(halt_rate=0.11)  # 10% increase — within threshold

    result = detector.detect(current, baseline)
    assert result.governance_regression_flag is False


def test_regression_fires_on_class0_degradation():
    """class0_failure_count increase >20% should trigger regression flag."""
    detector = GovernanceRegressionDetector()
    baseline = make_rollup(class0_failure_count=10)
    current = make_rollup(class0_failure_count=13)  # 30% increase

    result = detector.detect(current, baseline)
    assert result.governance_regression_flag is True


def test_regression_no_flag_on_class0_small_increase():
    """class0 increase <=20% should NOT trigger flag."""
    detector = GovernanceRegressionDetector()
    baseline = make_rollup(class0_failure_count=10)
    current = make_rollup(class0_failure_count=11)  # 10% increase

    result = detector.detect(current, baseline)
    assert result.governance_regression_flag is False


def test_regression_fires_from_zero_baseline():
    """When baseline halt_rate=0 but current>0, flag should trigger."""
    detector = GovernanceRegressionDetector()
    baseline = make_rollup(halt_rate=0.0)
    current = make_rollup(halt_rate=0.05)

    result = detector.detect(current, baseline)
    assert result.governance_regression_flag is True


def test_regression_no_flag_when_improving():
    """When current rates improve vs baseline, no flag."""
    detector = GovernanceRegressionDetector()
    baseline = make_rollup(halt_rate=0.20, class0_failure_count=5)
    current = make_rollup(halt_rate=0.10, class0_failure_count=2)

    result = detector.detect(current, baseline)
    assert result.governance_regression_flag is False


def test_regression_multi_session():
    """Multi-session regression detection uses first session as baseline."""
    detector = GovernanceRegressionDetector()
    sessions = [
        make_rollup(session_id="s1", halt_rate=0.10),  # baseline
        make_rollup(session_id="s2", halt_rate=0.10),  # no change
        make_rollup(session_id="s3", halt_rate=0.15),  # 50% increase → regression
    ]
    result = detector.detect_multi_session(sessions)
    assert result[0].governance_regression_flag is False
    assert result[1].governance_regression_flag is False
    assert result[2].governance_regression_flag is True


# ---------------------------------------------------------------------------
# Anonymization
# ---------------------------------------------------------------------------

def test_anonymize_rollup_redacts_session_id():
    """Anonymized rollup should have [REDACTED] session_id."""
    rollup = make_rollup(session_id="sensitive-session-abc123")
    anon = GovernanceRegressionDetector.anonymize_rollup(rollup)
    assert anon["session_id"] == "[REDACTED]"


def test_anonymize_rollup_preserves_counts():
    """Anonymized rollup should preserve counts and rates."""
    rollup = make_rollup(halt_rate=0.25, spm_fire_count=3)
    anon = GovernanceRegressionDetector.anonymize_rollup(rollup)
    assert anon["halt_rate"] == 0.25
    assert anon["spm_fire_count"] == 3


def test_anonymize_multiple_rollups():
    """Multiple rollups all get session_id redacted."""
    rollups = [
        make_rollup(session_id=f"session-{i}") for i in range(3)
    ]
    anon_list = GovernanceRegressionDetector.anonymize_rollups(rollups)
    for anon in anon_list:
        assert anon["session_id"] == "[REDACTED]"


@pytest.mark.asyncio
async def test_telemetry_export_anonymized():
    """Exported telemetry records should have session_id redacted."""
    redis = FakeRedis()
    store = TelemetryStore(redis)

    records = [make_turn_record(turn_index=i) for i in range(1, 4)]
    for r in records:
        await store.write_turn_record(r)

    exported = await store.export_anonymized("test-session-001")
    assert len(exported) == 3
    for record in exported:
        assert record["session_id"] == "[REDACTED]"


# ---------------------------------------------------------------------------
# Trace This completeness
# ---------------------------------------------------------------------------

def test_trace_this_ledger_coverage():
    """Audit ledger should contain all required coverage fields."""
    rollup = make_rollup()
    ledger = GovernanceRegressionDetector.build_trace_this_ledger(
        session_id="s1",
        rollup=rollup,
        turn_records=[],
    )
    assert ledger["coverage_fields_present"] is True
    assert "rollup" in ledger
    assert "turn_records" in ledger
    assert "session_id" in ledger


def test_trace_this_ledger_missing_field_detected():
    """Missing field in rollup should be detected."""
    rollup = make_rollup()
    # Check coverage of a non-existent field
    ledger = GovernanceRegressionDetector.build_trace_this_ledger(
        session_id="s1",
        rollup=rollup,
        turn_records=[],
        coverage_fields=["nonexistent_field"],
    )
    assert ledger["coverage_fields_present"] is False


@pytest.mark.asyncio
async def test_telemetry_render_full_level():
    """Full telemetry render should include per-turn breakdown."""
    redis = FakeRedis()
    store = TelemetryStore(redis)
    from cgs_runtime_wrapper.models.envelopes import TelemetryRenderLevel

    records = [
        make_turn_record(turn_index=1, halt=True),
        make_turn_record(turn_index=2, spm_fired=True),
    ]
    for r in records:
        await store.write_turn_record(r)

    rendered = await store.render(
        session_id="test-session-001",
        level=TelemetryRenderLevel.full,
    )
    assert "Turn 1" in rendered
    assert "Turn 2" in rendered
    assert "Halt: True" in rendered
