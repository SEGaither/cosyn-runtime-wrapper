"""
Phase 7 Tests — Model adapter interface and latency measurement.
Tests:
- Model adapter interface
- Latency measurement
"""
from __future__ import annotations

import time
import pytest

from cgs_runtime_wrapper.adapters.model_adapter import (
    ClaudeAPIAdapter,
    ModelAdapter,
    OpenAIAdapter,
    StubModelAdapter,
)


# ---------------------------------------------------------------------------
# StubModelAdapter
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stub_adapter_returns_response():
    """Stub adapter should return the configured response."""
    adapter = StubModelAdapter("Test response text.")
    response, latency_ms = await adapter.call_model("test prompt", "session-1")
    assert response == "Test response text."


@pytest.mark.asyncio
async def test_stub_adapter_returns_latency():
    """Stub adapter should return latency_ms as non-negative integer."""
    adapter = StubModelAdapter("Response.")
    _, latency_ms = await adapter.call_model("prompt", "session-1")
    assert isinstance(latency_ms, int)
    assert latency_ms >= 0


@pytest.mark.asyncio
async def test_stub_adapter_default_response():
    """Stub adapter with no args should return default response."""
    adapter = StubModelAdapter()
    response, _ = await adapter.call_model("prompt", "s1")
    assert len(response) > 0


@pytest.mark.asyncio
async def test_stub_adapter_custom_response():
    """Stub adapter should return any configured response."""
    custom = "NFAR"
    adapter = StubModelAdapter(custom)
    response, _ = await adapter.call_model("any prompt", "s1")
    assert response == custom


# ---------------------------------------------------------------------------
# Interface compliance
# ---------------------------------------------------------------------------

def test_stub_is_model_adapter():
    """StubModelAdapter must implement ModelAdapter interface."""
    adapter = StubModelAdapter()
    assert isinstance(adapter, ModelAdapter)


def test_claude_api_is_model_adapter():
    """ClaudeAPIAdapter must implement ModelAdapter interface."""
    adapter = ClaudeAPIAdapter(api_key="test")
    assert isinstance(adapter, ModelAdapter)


def test_openai_is_model_adapter():
    """OpenAIAdapter must implement ModelAdapter interface."""
    adapter = OpenAIAdapter(api_key="test")
    assert isinstance(adapter, ModelAdapter)


@pytest.mark.asyncio
async def test_claude_api_placeholder_returns_string():
    """ClaudeAPIAdapter placeholder should return a non-empty string."""
    adapter = ClaudeAPIAdapter(api_key="placeholder-key")
    response, latency_ms = await adapter.call_model("test prompt", "s1")
    assert isinstance(response, str)
    assert len(response) > 0
    assert isinstance(latency_ms, int)


@pytest.mark.asyncio
async def test_openai_placeholder_returns_string():
    """OpenAIAdapter placeholder should return a non-empty string."""
    adapter = OpenAIAdapter(api_key="placeholder-key")
    response, latency_ms = await adapter.call_model("test prompt", "s1")
    assert isinstance(response, str)
    assert len(response) > 0


# ---------------------------------------------------------------------------
# Latency measurement
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_latency_measured_in_ms():
    """Latency should be measured in milliseconds."""
    adapter = StubModelAdapter("Response")
    start = time.time()
    _, latency_ms = await adapter.call_model("prompt", "s1")
    elapsed = (time.time() - start) * 1000
    # latency_ms should be within a reasonable range of actual elapsed time
    # Allow 50ms tolerance for overhead
    assert latency_ms <= elapsed + 50


@pytest.mark.asyncio
async def test_latency_is_non_negative():
    """Latency should never be negative."""
    adapter = StubModelAdapter("Response")
    for _ in range(5):
        _, latency_ms = await adapter.call_model("prompt", "s")
        assert latency_ms >= 0


# ---------------------------------------------------------------------------
# Abstract interface enforcement
# ---------------------------------------------------------------------------

def test_cannot_instantiate_base_adapter():
    """ModelAdapter is abstract and cannot be instantiated directly."""
    with pytest.raises(TypeError):
        ModelAdapter()


def test_subclass_must_implement_call_model():
    """Subclass without call_model should fail to instantiate."""
    class IncompleteAdapter(ModelAdapter):
        pass  # No call_model implementation

    with pytest.raises(TypeError):
        IncompleteAdapter()


def test_concrete_subclass_works():
    """Custom concrete adapter should work correctly."""
    class EchoAdapter(ModelAdapter):
        async def call_model(self, prompt: str, session_id: str) -> tuple[str, int]:
            return f"Echo: {prompt}", 0

    adapter = EchoAdapter()
    assert isinstance(adapter, ModelAdapter)
