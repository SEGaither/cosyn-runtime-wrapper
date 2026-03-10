"""
Phase 6 — Governance Regression Detector & Audit Layer

Governance regression detector: compare TelemetrySessionRollup against prior session
rollups; flag governance_regression_flag=True when halt_rate or class0_failure_count
degrades >20% vs baseline.

Telemetry anonymization: redact session_id in exports, omit raw text, store counts/IDs/flags.
"""
from __future__ import annotations

from typing import Optional

from cgs_runtime_wrapper.models.envelopes import TelemetrySessionRollup

# Regression threshold: >20% degradation
_REGRESSION_THRESHOLD = 0.20


class GovernanceRegressionDetector:
    """
    Detects governance regression by comparing current session rollup
    against a baseline rollup (from a prior session or a configured baseline).
    """

    def detect(
        self,
        current: TelemetrySessionRollup,
        baseline: TelemetrySessionRollup,
    ) -> TelemetrySessionRollup:
        """
        Compare current rollup against baseline.
        Flags governance_regression_flag=True if:
        - halt_rate degraded by >20% vs baseline, OR
        - class0_failure_count increased by >20% vs baseline

        Returns the current rollup with governance_regression_flag updated.
        """
        regression_triggered = False

        # Halt rate regression
        if baseline.halt_rate > 0:
            halt_rate_delta = (current.halt_rate - baseline.halt_rate) / baseline.halt_rate
            if halt_rate_delta > _REGRESSION_THRESHOLD:
                regression_triggered = True
        elif current.halt_rate > 0:
            # Baseline was 0 but now non-zero → regression
            regression_triggered = True

        # Class 0 failure regression
        if baseline.class0_failure_count > 0:
            class0_delta = (
                (current.class0_failure_count - baseline.class0_failure_count)
                / baseline.class0_failure_count
            )
            if class0_delta > _REGRESSION_THRESHOLD:
                regression_triggered = True
        elif current.class0_failure_count > 0:
            # Baseline was 0 but now non-zero
            regression_triggered = True

        return current.model_copy(update={"governance_regression_flag": regression_triggered})

    def detect_multi_session(
        self,
        sessions: list[TelemetrySessionRollup],
        baseline_index: int = 0,
    ) -> list[TelemetrySessionRollup]:
        """
        Apply regression detection across multiple sessions.
        Uses sessions[baseline_index] as the baseline for all subsequent sessions.
        Returns updated list.
        """
        if not sessions or baseline_index >= len(sessions):
            return sessions

        baseline = sessions[baseline_index]
        result = list(sessions)

        for i, session in enumerate(sessions):
            if i == baseline_index:
                continue
            result[i] = self.detect(session, baseline)

        return result

    @staticmethod
    def anonymize_rollup(rollup: TelemetrySessionRollup) -> dict:
        """
        Return anonymized representation of a rollup:
        - Redact session_id
        - Keep counts, rates, flags only
        """
        data = rollup.model_dump()
        data["session_id"] = "[REDACTED]"
        return data

    @staticmethod
    def anonymize_rollups(rollups: list[TelemetrySessionRollup]) -> list[dict]:
        return [GovernanceRegressionDetector.anonymize_rollup(r) for r in rollups]

    @staticmethod
    def build_trace_this_ledger(
        session_id: str,
        rollup: TelemetrySessionRollup,
        turn_records: list[dict],
        coverage_fields: Optional[list[str]] = None,
    ) -> dict:
        """
        Assemble a complete audit ledger for the Trace This handler.
        Ensures all required coverage fields are present.
        """
        required_fields = coverage_fields or [
            "session_id",
            "total_turns",
            "halt_rate",
            "rerender_rate",
            "provisional_rate",
            "assumption_rate",
            "spm_fire_count",
            "spm_dispute_count",
            "class0_failure_count",
            "class1_failure_count",
            "governance_regression_flag",
        ]

        rollup_data = rollup.model_dump()
        ledger = {
            "session_id": session_id,
            "rollup": rollup_data,
            "turn_records": turn_records,
            "coverage_fields_present": all(f in rollup_data for f in required_fields),
        }
        return ledger
