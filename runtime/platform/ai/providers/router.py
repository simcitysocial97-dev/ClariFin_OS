"""Model Router (Phase 15).

Routes AI requests to the best available provider based on task profile.
Falls back to deterministic when no LLM is available.
"""

from __future__ import annotations

import logging
from typing import Any

from runtime.platform.ai.providers.base import (
    CompletionResult,
    Message,
    ModelDescriptor,
    ProviderHealth,
    ProviderKind,
    RoutingProfile,
    ToolChoice,
    ToolSpec,
)
from runtime.platform.ai.providers.local import (
    DETERMINISTIC_FALLBACK,
    LOCAL_OLLAMA_PROVIDER,
)

logger = logging.getLogger(__name__)

__all__ = ["ModelRouter", "MODEL_ROUTER_INSTANCE"]


# Task-to-preferred-provider mapping
TASK_PROFILE_DEFAULTS: dict[str, list[str]] = {
    "classify": ["local-small", "deterministic-fallback"],
    "summarize": ["local-small", "deterministic-fallback"],
    "diagnose": ["local-small", "deterministic-fallback"],
    "plan": ["local-small", "deterministic-fallback"],
    "explain": ["local-small", "deterministic-fallback"],
    "patch": ["local-small", "deterministic-fallback"],  # disabled: human required
}


class ModelRouter:
    """Routes AI requests to the best available provider."""

    def __init__(self) -> None:
        self._providers: dict[str, Any] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(LOCAL_OLLAMA_PROVIDER)
        self.register(DETERMINISTIC_FALLBACK)

    def register(self, provider: Any) -> None:
        """Register a model provider."""
        self._providers[provider.name] = provider
        logger.info("Registered provider: %s (%s)", provider.name, provider.kind)

    def get_provider(self, name: str) -> Any | None:
        return self._providers.get(name)

    def list_providers(self) -> list[dict[str, Any]]:
        """List all registered providers with their health status."""
        result = []
        for name, provider in self._providers.items():
            health = provider.health
            result.append({
                "name": name,
                "kind": provider.kind.value,
                "models": [m.name for m in provider.models],
                "health": {
                    "reachable": health.reachable,
                    "last_check": health.last_check.isoformat(),
                    "last_success": health.last_success.isoformat() if health.last_success else None,
                    "last_failure": health.last_failure.isoformat() if health.last_failure else None,
                    "failure_streak": health.failure_streak,
                    "p50_latency_ms": health.p50_latency_ms,
                    "notes": health.notes,
                },
            })
        return result

    def route(
        self,
        profile: RoutingProfile,
        *,
        explicit_provider: str | None = None,
    ) -> Any:
        """Select the best provider for a given routing profile."""
        if explicit_provider:
            provider = self._providers.get(explicit_provider)
            if provider and provider.is_available():
                return provider
            logger.warning("Explicit provider %s unavailable, falling back", explicit_provider)

        # Get preferred providers for this task type
        preferred = TASK_PROFILE_DEFAULTS.get(profile.task_kind, [])

        # Filter by constraints
        candidates = []
        for pname in preferred:
            provider = self._providers.get(pname)
            if not provider or not provider.is_available():
                continue
            if profile.privacy == "local" and provider.kind == ProviderKind.EXTERNAL:
                continue
            if profile.cost_budget_usd >= 0 and any(
                m.cost_per_1k_tokens > profile.cost_budget_usd / 1000
                for m in provider.models
            ):
                continue
            candidates.append(provider)

        # Fallback to first available
        if not candidates:
            for provider in self._providers.values():
                if provider.is_available():
                    candidates.append(provider)
                    break

        if not candidates:
            # Ultimate fallback: deterministic
            return DETERMINISTIC_FALLBACK

        return candidates[0]

    def complete(
        self,
        *,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
        profile: RoutingProfile | None = None,
        **kwargs: Any,
    ) -> CompletionResult:
        """Route and execute a completion request."""
        profile = profile or RoutingProfile(task_kind="diagnose", context_size=1000)

        provider = self.route(profile)
        logger.debug("Routing to provider: %s for task: %s", provider.name, profile.task_kind)

        return provider.complete(
            messages=messages,
            tools=tools,
            **kwargs,
        )


# Singleton instance
MODEL_ROUTER_INSTANCE = ModelRouter()
