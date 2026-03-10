"""
FastAPI application — CGS Runtime Wrapper
Three endpoints:
- POST /turn       → full pipeline
- POST /telemetry/render → formatted telemetry
- POST /session/reset   → reset session state
"""
from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from typing import Optional

import redis.asyncio as aioredis
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from cgs_runtime_wrapper.adapters.model_adapter import ModelAdapter, StubModelAdapter
from cgs_runtime_wrapper.api.middleware import APIKeyMiddleware, RateLimiter
from cgs_runtime_wrapper.egress.router import run_egress_pipeline
from cgs_runtime_wrapper.ingress.router import run_ingress_pipeline
from cgs_runtime_wrapper.models.envelopes import (
    ErrorResponse,
    OutputEnvelope,
    RequestEnvelope,
    SessionResetRequest,
    SessionResetResponse,
    TelemetryRenderRequest,
    TelemetryRenderLevel,
)
from cgs_runtime_wrapper.state.session_store import SessionStore
from cgs_runtime_wrapper.telemetry.store import TelemetryStore

# Load .env before reading any environment variables
load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

# ---------------------------------------------------------------------------
# Application state holders
# ---------------------------------------------------------------------------
_redis_client: Optional[aioredis.Redis] = None
_session_store: Optional[SessionStore] = None
_telemetry_store: Optional[TelemetryStore] = None
_model_adapter: Optional[ModelAdapter] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and tear down Redis connections."""
    global _redis_client, _session_store, _telemetry_store, _model_adapter

    _redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    _session_store = SessionStore(_redis_client)
    _telemetry_store = TelemetryStore(_redis_client)

    # Expose redis client on app.state so RateLimiter dependency can reach it
    app.state.redis_client = _redis_client

    # Default to StubModelAdapter; replace with real adapter via env/config
    model_type = os.environ.get("MODEL_ADAPTER", "stub")
    if model_type == "claude":
        from cgs_runtime_wrapper.adapters.model_adapter import ClaudeAPIAdapter
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        model_name = os.environ.get("CLAUDE_MODEL", "claude-opus-4-5")
        _model_adapter = ClaudeAPIAdapter(api_key=api_key, model=model_name)
    else:
        _model_adapter = StubModelAdapter()

    yield

    if _redis_client:
        await _redis_client.aclose()


app = FastAPI(
    title="CGS Runtime Wrapper",
    version="0.1.0",
    description="Cosyn Governance Stack Runtime Wrapper API",
    lifespan=lifespan,
)

# Authentication — applied to every request
app.add_middleware(APIKeyMiddleware)

# Shared rate limiter instance — configured once from env at import time
_rate_limiter = RateLimiter()


def _get_stores() -> tuple[SessionStore, TelemetryStore]:
    if _session_store is None or _telemetry_store is None:
        raise RuntimeError("Stores not initialized — lifespan not complete")
    return _session_store, _telemetry_store


def _get_adapter() -> ModelAdapter:
    if _model_adapter is None:
        raise RuntimeError("Model adapter not initialized")
    return _model_adapter


# ---------------------------------------------------------------------------
# Exception handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_ERROR",
            message=str(exc),
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# POST /turn
# ---------------------------------------------------------------------------

@app.post("/turn", response_model=OutputEnvelope)
async def post_turn(
    request_body: RequestEnvelope,
    _rl: None = Depends(_rate_limiter),
) -> OutputEnvelope:
    """
    Full pipeline: ingress gates → model call → egress gates → OutputEnvelope.
    """
    session_store, telemetry_store = _get_stores()
    model_adapter = _get_adapter()

    turn_start_ms = int(time.time() * 1000)

    # Get or create session state
    session_state = await session_store.get_or_create(
        session_id=request_body.session_id,
        cgs_version=request_body.cgs_version,
        wrapper_version=request_body.wrapper_version,
        crs_strict_mode=request_body.crs_strict_mode,
        crs_scope=request_body.crs_scope,
        mode_lock=request_body.mode_lock,
        spm_suppress=request_body.spm_suppress,
    )

    # Run ingress pipeline
    ingress_envelope, session_state = await run_ingress_pipeline(
        request=request_body,
        session_state=session_state,
    )

    # Run egress pipeline
    output_envelope, session_state = await run_egress_pipeline(
        ingress_envelope=ingress_envelope,
        session_state=session_state,
        model_adapter=model_adapter,
        session_store=session_store,
        telemetry_store=telemetry_store,
        turn_start_ms=turn_start_ms,
    )

    return output_envelope


# ---------------------------------------------------------------------------
# POST /telemetry/render
# ---------------------------------------------------------------------------

@app.post("/telemetry/render", response_model=str)
async def post_telemetry_render(request_body: TelemetryRenderRequest) -> str:
    """
    Render telemetry for a session at the specified level.
    """
    _, telemetry_store = _get_stores()

    rendered = await telemetry_store.render(
        session_id=request_body.session_id,
        level=request_body.level,
        turn_range=request_body.range,
    )
    return rendered


# ---------------------------------------------------------------------------
# POST /session/reset
# ---------------------------------------------------------------------------

@app.post("/session/reset", response_model=SessionResetResponse)
async def post_session_reset(request_body: SessionResetRequest) -> SessionResetResponse:
    """
    Reset session state. Preserves session_id for audit log.
    """
    session_store, _ = _get_stores()
    await session_store.reset(session_id=request_body.session_id)
    return SessionResetResponse(status="ok")
