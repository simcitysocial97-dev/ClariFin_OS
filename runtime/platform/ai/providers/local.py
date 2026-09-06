"""Local (Ollama) Provider (Phase 15).

Connects to a local Ollama instance. Disabled by default when
Ollama is unavailable — falls back to deterministic responses.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from runtime.platform.ai.providers.base import (
    BaseProvider,
    CompletionResult,
    Message,
    ModelDescriptor,
    ModelProvider,
    ProviderHealth,
    ProviderKind,
    ToolChoice,
    ToolSpec,
)

logger = logging.getLogger(__name__)

__all__ = ["LocalOllamaProvider"]


class LocalOllamaProvider(BaseProvider):
    """Local Ollama provider via HTTP API."""

    def __init__(
        self,
        endpoint: str = "http://localhost:11434",
        default_model: str = "qwen2.5:3b-instruct",
        timeout_s: float = 120.0,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._timeout_s = timeout_s
        self._available = False
        super().__init__(
            name="local-small",
            kind=ProviderKind.LOCAL,
            default_model=default_model,
        )

    def _setup_models(self, **kwargs: Any) -> None:
        context_window = kwargs.get("context_window", 4096)
        self._models = [
            ModelDescriptor(
                name=self._default_model,
                context_window=context_window,
                capabilities=["classify", "summarize", "route", "tool_select", "simple_plan", "short_explain"],
                cost_per_1k_tokens=0.0,
                latency_p50_ms=kwargs.get("latency_p50_ms", 800),
            ),
        ]
        # Check if Ollama is available
        self._check_availability()

    def _check_availability(self) -> None:
        try:
            import httpx
            resp = httpx.get(f"{self._endpoint}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                self.mark_healthy()
                self._available = True
                logger.info("LocalOllama provider available at %s", self._endpoint)
                return
        except Exception as exc:
            logger.debug("Ollama not reachable at %s: %s", self._endpoint, exc)
        finally:
            self._available = False
            self.mark_unhealthy("Ollama not reachable")

    def is_available(self) -> bool:
        return self._available and super().is_available()

    def complete(
        self,
        *,
        model: str | None = None,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
        tool_choice: ToolChoice | str = ToolChoice.AUTO,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> CompletionResult:
        """Send completion request to Ollama."""
        import httpx

        model = model or self._default_model
        start = time.time()

        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": m.role, "content": m.content}
                for m in messages
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]

        try:
            with httpx.Client(timeout=self._timeout_s) as client:
                resp = client.post(f"{self._endpoint}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                elapsed_ms = int((time.time() - start) * 1000)

                choice = data.get("message", {})
                text = choice.get("content", "")
                tool_calls = choice.get("tool_calls")

                result = CompletionResult(
                    model=model,
                    text=text,
                    finish_reason=choice.get("finish_reason", "stop"),
                    usage=data.get("eval_count", 0),
                    tool_calls=tool_calls,
                    provider=self.name,
                    latency_ms=elapsed_ms,
                )
                self.mark_healthy(elapsed_ms)
                return result
        except Exception as exc:
            logger.warning("Ollama call failed: %s", exc)
            self.mark_unhealthy(str(exc)[:100])
            raise


class DeterministicFallbackProvider(BaseProvider):
    """Deterministic fallback when no LLM is available.

    Returns canned responses based on intent — never fabricates AI output.
    """

    def __init__(self) -> None:
        super().__init__(
            name="deterministic-fallback",
            kind=ProviderKind.LOCAL,
            default_model="deterministic",
        )
        self._models = [
            ModelDescriptor(
                name="deterministic",
                context_window=4096,
                capabilities=["classify", "summarize", "route"],
                cost_per_1k_tokens=0.0,
                latency_p50_ms=0,
            ),
        ]

    def is_available(self) -> bool:
        return True  # Always available

    def complete(
        self,
        *,
        model: str | None = None,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
        tool_choice: ToolChoice | str = ToolChoice.AUTO,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> CompletionResult:
        """Return deterministic response based on message content."""
        last_user = next((m for m in reversed(messages) if m.role == "user"), None)
        symptom = last_user.content if last_user else ""

        # Build deterministic response
        response_text = f"[DETERMINISTIC FALLBACK] Based on symptom '{symptom[:100]}':\n"
        response_text += "No LLM provider available. Use platform tools directly.\n"
        response_text += "Run: POST /platform/v1/diagnose with your symptom."

        return CompletionResult(
            model="deterministic",
            text=response_text,
            finish_reason="stop",
            usage={"prompt_tokens": 0, "completion_tokens": 0},
            provider=self.name,
            latency_ms=0,
            deterministic=True,
        )

    @property
    def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider=self.name,
            reachable=True,
            last_check=datetime.now(timezone.utc),
            last_success=datetime.now(timezone.utc),
            last_failure=None,
            failure_streak=0,
            p50_latency_ms=0,
            notes="deterministic_fallback",
        )


# Singleton instances
LOCAL_OLLAMA_PROVIDER = LocalOllamaProvider()
DETERMINISTIC_FALLBACK = DeterministicFallbackProvider()
