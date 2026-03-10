"""
Telemetry Store — Phase 1
Key pattern: telemetry:{session_id}:{turn_index}
List key: telemetry_turns:{session_id}  (ordered turn index list)
Anonymized export: redact session_id, omit raw text, keep counts/IDs/flags.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import redis.asyncio as aioredis

from cgs_runtime_wrapper.models.envelopes import (
    TelemetryTurnRecord,
    TelemetrySessionRollup,
    TelemetryRenderLevel,
)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
TELEMETRY_KEY_PREFIX = "telemetry:"
TELEMETRY_TURNS_LIST_PREFIX = "telemetry_turns:"


def _record_key(session_id: str, turn_index: int) -> str:
    return f"{TELEMETRY_KEY_PREFIX}{session_id}:{turn_index}"


def _turns_list_key(session_id: str) -> str:
    return f"{TELEMETRY_TURNS_LIST_PREFIX}{session_id}"


class TelemetryStore:
    """Async Redis-backed telemetry store."""

    def __init__(self, redis_client: Optional[aioredis.Redis] = None) -> None:
        self._redis: Optional[aioredis.Redis] = redis_client

    async def _get_client(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        return self._redis

    async def write_turn_record(self, record: TelemetryTurnRecord) -> None:
        """Persist a TelemetryTurnRecord."""
        client = await self._get_client()
        key = _record_key(record.session_id, record.turn_index)
        list_key = _turns_list_key(record.session_id)
        payload = record.model_dump_json()
        await client.set(key, payload)
        # Push turn_index to the ordered list (avoid duplicates)
        existing: list[str] = await client.lrange(list_key, 0, -1)
        if str(record.turn_index) not in existing:
            await client.rpush(list_key, record.turn_index)

    async def get_turn_record(
        self, session_id: str, turn_index: int
    ) -> Optional[TelemetryTurnRecord]:
        client = await self._get_client()
        raw = await client.get(_record_key(session_id, turn_index))
        if raw is None:
            return None
        return TelemetryTurnRecord.model_validate(json.loads(raw))

    async def get_all_records(self, session_id: str) -> list[TelemetryTurnRecord]:
        """Return all records for a session ordered by turn_index."""
        client = await self._get_client()
        list_key = _turns_list_key(session_id)
        turn_indices_raw: list[str] = await client.lrange(list_key, 0, -1)
        records: list[TelemetryTurnRecord] = []
        for ti_str in turn_indices_raw:
            rec = await self.get_turn_record(session_id, int(ti_str))
            if rec is not None:
                records.append(rec)
        records.sort(key=lambda r: r.turn_index)
        return records

    async def get_records_in_range(
        self, session_id: str, start_turn: int, end_turn: int
    ) -> list[TelemetryTurnRecord]:
        all_records = await self.get_all_records(session_id)
        return [r for r in all_records if start_turn <= r.turn_index <= end_turn]

    async def build_rollup(self, session_id: str) -> TelemetrySessionRollup:
        """Aggregate all turn records into a session rollup."""
        records = await self.get_all_records(session_id)
        total = len(records)
        if total == 0:
            return TelemetrySessionRollup(
                session_id=session_id,
                total_turns=0,
                halt_rate=0.0,
                rerender_rate=0.0,
                provisional_rate=0.0,
                assumption_rate=0.0,
                spm_fire_count=0,
                spm_dispute_count=0,
                spm_retraction_count=0,
                class0_failure_count=0,
                class1_failure_count=0,
                governance_regression_flag=False,
            )

        halt_count = sum(1 for r in records if r.halt_triggered)
        rerender_count = sum(1 for r in records if r.rerender_requested)
        provisional_count = sum(1 for r in records if r.provisional_labeling_count > 0)
        assumption_count = sum(1 for r in records if r.assumption_block_present)
        spm_fire_count = sum(1 for r in records if r.spm_fired)
        spm_dispute_count = sum(1 for r in records if r.spm_dispute_event)

        # Compute numeric basis ratio
        total_numeric = sum(r.numeric_claims_count for r in records)
        total_with_basis = sum(r.numeric_claims_with_basis_count for r in records)
        numeric_basis_ratio: Optional[float] = (
            total_with_basis / total_numeric if total_numeric > 0 else None
        )

        return TelemetrySessionRollup(
            session_id=session_id,
            total_turns=total,
            halt_rate=halt_count / total,
            rerender_rate=rerender_count / total,
            provisional_rate=provisional_count / total,
            assumption_rate=assumption_count / total,
            spm_fire_count=spm_fire_count,
            spm_dispute_count=spm_dispute_count,
            spm_retraction_count=0,  # retraction detection is a higher-layer concern
            class0_failure_count=0,  # tracked at egress router level
            class1_failure_count=0,
            governance_regression_flag=False,
            numeric_basis_ratio=numeric_basis_ratio,
        )

    async def render(
        self,
        session_id: str,
        level: TelemetryRenderLevel,
        turn_range: Optional[list[int]] = None,
    ) -> str:
        """Render telemetry as a human-readable string at the specified level."""
        if turn_range and len(turn_range) == 2:
            records = await self.get_records_in_range(session_id, turn_range[0], turn_range[1])
        else:
            records = await self.get_all_records(session_id)

        if not records:
            return f"[Telemetry] No records found for session {session_id}."

        rollup = await self.build_rollup(session_id)
        lines: list[str] = []

        lines.append(f"=== Telemetry Report: {session_id} ===")
        lines.append(f"Total turns: {rollup.total_turns}")
        lines.append(f"Halt rate: {rollup.halt_rate:.2%}")
        lines.append(f"Rerender rate: {rollup.rerender_rate:.2%}")

        if level == TelemetryRenderLevel.minimal:
            return "\n".join(lines)

        lines.append(f"SPM fire count: {rollup.spm_fire_count}")
        lines.append(f"SPM dispute count: {rollup.spm_dispute_count}")
        lines.append(f"Provisional rate: {rollup.provisional_rate:.2%}")
        lines.append(f"Assumption rate: {rollup.assumption_rate:.2%}")

        if level == TelemetryRenderLevel.standard:
            return "\n".join(lines)

        # full — include per-turn breakdown
        lines.append("")
        lines.append("--- Per-Turn Breakdown ---")
        for rec in records:
            lines.append(f"Turn {rec.turn_index}:")
            lines.append(f"  Gates fired: {[g.value for g in rec.gate_triggers_fired]}")
            lines.append(f"  Halt: {rec.halt_triggered} ({rec.halt_reason_code})")
            lines.append(f"  Rerender: {rec.rerender_requested} (count={rec.rerender_count})")
            lines.append(f"  Provisional labels: {rec.provisional_labeling_count}")
            lines.append(f"  SPM A/B/C: {rec.spm_signal_a_count}/{rec.spm_signal_b_count}/{rec.spm_signal_c_count}")
            lines.append(f"  Latency: {rec.latency_ms}ms (classifier={rec.classifier_latency_ms}ms, model={rec.model_latency_ms}ms)")

        return "\n".join(lines)

    async def export_anonymized(self, session_id: str) -> list[dict]:
        """
        Export telemetry with anonymization:
        - redact session_id
        - omit raw text
        - keep counts, IDs, flags only
        """
        records = await self.get_all_records(session_id)
        result = []
        for rec in records:
            data = rec.model_dump()
            data["session_id"] = "[REDACTED]"
            # Remove any raw text fields if they exist
            data.pop("raw_input", None)
            data.pop("raw_output", None)
            result.append(data)
        return result

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
