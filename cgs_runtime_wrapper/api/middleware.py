"""
Production hardening middleware and dependencies.

APIKeyMiddleware — Starlette BaseHTTPMiddleware applied to all routes.
  Reads CGS_API_KEY from environment. Checks X-API-Key request header.
  Returns 401 JSON on missing or invalid key.

RateLimiter — FastAPI dependency applied only to POST /turn.
  Per-session sliding-window counter keyed in Redis.
  Default: 60 requests per minute per session_id.
  Configurable via RATE_LIMIT_RPM environment variable.
  Returns 429 JSON when limit exceeded.
"""
from __future__ import annotations

import json
import math
import os
import time
from typing import Optional

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

_API_KEY: str = os.environ.get("CGS_API_KEY", "")
_RATE_LIMIT_RPM: int = int(os.environ.get("RATE_LIMIT_RPM", "60"))

# ---------------------------------------------------------------------------
# API Key Middleware
# ---------------------------------------------------------------------------


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Validate X-API-Key header against CGS_API_KEY environment variable on
    every request.  Returns 401 if the key is absent or does not match.
    CGS_API_KEY must be set in the environment (loaded from .env by the
    application startup); if it is empty the middleware rejects all calls.
    """

    _OPEN_PATHS = {"/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self._OPEN_PATHS:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key", "")
        expected = os.environ.get("CGS_API_KEY", _API_KEY)

        if not expected:
            # Server misconfiguration — reject with 500 rather than silently
            # accepting all traffic.
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error_code": "SERVER_MISCONFIGURED", "message": "CGS_API_KEY is not set."},
            )

        if not api_key or api_key != expected:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error_code": "UNAUTHORIZED", "message": "Missing or invalid API key."},
            )

        return await call_next(request)


# ---------------------------------------------------------------------------
# Rate Limiter — dependency (POST /turn only)
# ---------------------------------------------------------------------------

# Redis key pattern: rate_limit:{session_id}:{minute_bucket}
# minute_bucket = floor(unix_time / 60)  — one counter per calendar minute
_RATE_KEY_PREFIX = "rate_limit"


def _minute_bucket() -> int:
    return math.floor(time.time() / 60)


class RateLimiter:
    """
    Per-session sliding-window rate limiter backed by Redis.

    Usage (FastAPI dependency):
        @app.post("/turn")
        async def post_turn(
            request_body: RequestEnvelope,
            _: None = Depends(RateLimiter()),
        ) -> OutputEnvelope:
            ...

    The limiter reads the parsed request body that FastAPI already provided
    to the endpoint, so the request body is not consumed twice.
    """

    def __init__(self, rpm: Optional[int] = None) -> None:
        self._rpm = rpm or int(os.environ.get("RATE_LIMIT_RPM", str(_RATE_LIMIT_RPM)))

    async def __call__(self, request: Request, request_body: "RequestEnvelope") -> None:  # type: ignore[name-defined]
        """
        Check and increment the per-session rate limit counter.
        Raises HTTP 429 if the limit is exceeded.
        The redis client is retrieved from app.state set during lifespan.
        """
        redis_client: Optional[aioredis.Redis] = getattr(request.app.state, "redis_client", None)
        if redis_client is None:
            # No Redis available — fail open (do not block the request)
            return

        session_id: str = request_body.session_id
        bucket = _minute_bucket()
        key = f"{_RATE_KEY_PREFIX}:{session_id}:{bucket}"

        # Atomic increment; set TTL of 90 s on first creation so keys self-expire
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, 90)

        if count > self._rpm:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": (
                        f"Session '{session_id}' has exceeded the rate limit of "
                        f"{self._rpm} requests per minute."
                    ),
                },
            )
