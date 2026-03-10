"""
Phase 7 — Model Adapter

Abstract interface accepting any model endpoint.
Method: call_model(prompt: str, session_id: str) -> (str, latency_ms)
Includes placeholder for Claude API integration.
Measures and returns latency_ms.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Optional


class ModelAdapter(ABC):
    """Abstract base for model endpoint adapters."""

    @abstractmethod
    async def call_model(self, prompt: str, session_id: str) -> tuple[str, int]:
        """
        Call the model with the given prompt.

        Args:
            prompt: The full model prompt (system + state + user input).
            session_id: Active session identifier (for logging/routing).

        Returns:
            (raw_output, latency_ms) tuple.
        """
        ...


class StubModelAdapter(ModelAdapter):
    """
    Stub model adapter for testing.
    Returns a configurable response without calling any real model.
    """

    def __init__(self, response: str = "This is a stub model response.") -> None:
        self._response = response

    async def call_model(self, prompt: str, session_id: str) -> tuple[str, int]:
        start = time.time()
        # Simulate minimal processing
        response = self._response
        latency_ms = int((time.time() - start) * 1000)
        return response, latency_ms


class ClaudeAPIAdapter(ModelAdapter):
    """
    Placeholder Claude API adapter.
    Configure with your Anthropic API key and model ID.

    Usage:
        adapter = ClaudeAPIAdapter(api_key="sk-ant-...", model="claude-opus-4-5")
        output, latency = await adapter.call_model(prompt, session_id)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-opus-4-5",
        max_tokens: int = 4096,
        base_url: str = "https://api.anthropic.com",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.base_url = base_url

    async def call_model(self, prompt: str, session_id: str) -> tuple[str, int]:
        """
        Call the Claude API.

        NOTE: This is a placeholder. Install the anthropic package and
        uncomment the implementation below.

        import anthropic
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        message = await client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text, latency_ms
        """
        start = time.time()
        # Placeholder: return a canned response until API is configured
        response = (
            "[Claude API placeholder] Configure ClaudeAPIAdapter with a valid "
            "API key to receive real model responses."
        )
        latency_ms = int((time.time() - start) * 1000)
        return response, latency_ms


class OpenAIAdapter(ModelAdapter):
    """
    Placeholder OpenAI-compatible adapter.
    Works with any OpenAI-compatible REST endpoint.

    Usage:
        adapter = OpenAIAdapter(api_key="sk-...", model="gpt-4o", base_url="...")
        output, latency = await adapter.call_model(prompt, session_id)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.base_url = base_url

    async def call_model(self, prompt: str, session_id: str) -> tuple[str, int]:
        """
        Placeholder OpenAI adapter.

        NOTE: Uncomment and implement when using:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": self.max_tokens,
                },
                timeout=60.0,
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"], latency_ms
        """
        start = time.time()
        response = "[OpenAI placeholder] Configure OpenAIAdapter with a valid API key."
        latency_ms = int((time.time() - start) * 1000)
        return response, latency_ms
