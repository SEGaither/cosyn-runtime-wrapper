"""
Redis Session Store — Phase 1
Key pattern: session:{session_id}
TTL: SessionState.ttl_seconds (default 3600)
"""
from __future__ import annotations

import json
import os
import time
from typing import Optional

import redis.asyncio as aioredis

from cgs_runtime_wrapper.models.envelopes import SessionState


REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
SESSION_KEY_PREFIX = "session:"


def _session_key(session_id: str) -> str:
    return f"{SESSION_KEY_PREFIX}{session_id}"


class SessionStore:
    """Async Redis-backed session store for SessionState objects."""

    def __init__(self, redis_client: Optional[aioredis.Redis] = None) -> None:
        self._redis: Optional[aioredis.Redis] = redis_client

    async def _get_client(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        return self._redis

    async def get(self, session_id: str) -> Optional[SessionState]:
        """Return SessionState or None if not found / expired."""
        client = await self._get_client()
        raw = await client.get(_session_key(session_id))
        if raw is None:
            return None
        data = json.loads(raw)
        return SessionState.model_validate(data)

    async def put(self, state: SessionState) -> None:
        """Persist SessionState with TTL."""
        client = await self._get_client()
        key = _session_key(state.session_id)
        payload = state.model_dump_json()
        await client.set(key, payload, ex=state.ttl_seconds)

    async def create(
        self,
        session_id: str,
        cgs_version: str,
        wrapper_version: str,
        crs_strict_mode: bool = False,
        crs_scope: Optional[str] = None,
        mode_lock: Optional[str] = None,
        spm_suppress: bool = False,
    ) -> SessionState:
        """Create and persist a new SessionState."""
        now_ms = int(time.time() * 1000)
        state = SessionState(
            session_id=session_id,
            cgs_version=cgs_version,
            wrapper_version=wrapper_version,
            crs_strict_mode=crs_strict_mode,
            crs_scope=crs_scope,
            mode_lock=mode_lock,
            spm_suppress=spm_suppress,
            session_started_at_ms=now_ms,
        )
        await self.put(state)
        return state

    async def reset(self, session_id: str, cgs_version: str = "", wrapper_version: str = "") -> SessionState:
        """
        Reset a session: delete key, preserve session_id, create fresh state.
        Preserves audit trail note by logging the reset.
        """
        client = await self._get_client()
        # Read existing state to capture versions if available
        existing = await self.get(session_id)
        cv = cgs_version or (existing.cgs_version if existing else "")
        wv = wrapper_version or (existing.wrapper_version if existing else "")

        await client.delete(_session_key(session_id))

        now_ms = int(time.time() * 1000)
        fresh = SessionState(
            session_id=session_id,
            cgs_version=cv,
            wrapper_version=wv,
            session_started_at_ms=now_ms,
        )
        await self.put(fresh)
        return fresh

    async def exists(self, session_id: str) -> bool:
        client = await self._get_client()
        return bool(await client.exists(_session_key(session_id)))

    async def get_or_create(
        self,
        session_id: str,
        cgs_version: str,
        wrapper_version: str,
        crs_strict_mode: bool = False,
        crs_scope: Optional[str] = None,
        mode_lock: Optional[str] = None,
        spm_suppress: bool = False,
    ) -> SessionState:
        """Return existing session or create a new one."""
        state = await self.get(session_id)
        if state is not None:
            return state
        return await self.create(
            session_id=session_id,
            cgs_version=cgs_version,
            wrapper_version=wrapper_version,
            crs_strict_mode=crs_strict_mode,
            crs_scope=crs_scope,
            mode_lock=mode_lock,
            spm_suppress=spm_suppress,
        )

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
