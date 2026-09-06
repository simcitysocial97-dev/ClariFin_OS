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

try:
    from runtime.platform.ai.providers.local import LOCAL_LARGE_PROVIDER, OPENROUTER_PROVIDER
except Exception:  # pragma: no cover
    LOCAL_LARGE_PROVIDER = None  # type: ignore[assignment]
    OPENROUTER_PROVIDER = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

__all__ = ["ModelRouter", "MODEL_ROUTER_INSTANCE"]


# Task-to-preferred-provider mapping per MODEL_ROUTING_DESIGN §4
TASK_PROFILE_DEFAULTS: dict[str, list[str]] = {
    "classify": ["local-small", "deterministic-fallback"],
    "summarize": ["local-small", "deterministic-fallback"],
    "diagnose": ["local-small", "local-large", "deterministic-fallback"],
    "plan": ["local-small", "local-large", "deterministic-fallback"],
    "explain": ["local-small", "local-large", "deterministic-fallback"],
    "patch": ["local-large", "openrouter", "deterministic-fallback"],  # disabled: human required
    "route": ["local-small", "deterministic-fallback"],
    "tool_select": ["local-small", "deterministic-fallback"],
}


class ModelRouter:
    """Routes AI requests to the best available provider."""

    def __init__(self) -> None:
        self._providers: dict[str, Any] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(LOCAL_OLLAMA_PROVIDER)
        if LOCAL_LARGE_PROVIDER is not None:
            self.register(LOCAL_LARGE_PROVIDER)
        if OPENROUTER_PROVIDER is not None:
            try:
                self.register(OPENROUTER_PROVIDER)
            except Exception:
                pass
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
        """Select the best provider for a given routing profile.

        Implements MODEL_ROUTING_DESIGN §3 ordering:
          1 local first, 2 task_kind capability, 3 context_size, 4 privacy,
          5 availability, 6 latency, 7 cost, 8 best-score.
        """
        if explicit_provider:
            provider = self._providers.get(explicit_provider)
            if provider and provider.is_available():
                # Privacy boundary — explicit external request rejected for local-only
                if profile.privacy == "local" and provider.kind == ProviderKind.EXTERNAL:
                    logger.warning("Explicit provider %s rejected: privacy=local", explicit_provider)
                else:
                    return provider
            logger.warning("Explicit provider %s unavailable, falling back", explicit_provider)

        # Get preferred providers for this task type
        preferred = TASK_PROFILE_DEFAULTS.get(profile.task_kind, ["local-small", "deterministic-fallback"])

        # Filter by constraints
        candidates = []
        for pname in preferred:
            provider = self._providers.get(pname)
            if not provider or not provider.is_available():
                continue
            if profile.privacy == "local" and provider.kind == ProviderKind.EXTERNAL:
                continue
            # Context window filter
            if profile.context_size > 0 and provider.models:
                # Require at least one model that fits context
                if not any(m.context_window >= profile.context_size for m in provider.models):
                    continue
            # Required capability filter
            if profile.required_capability:
                if not any(profile.required_capability in m.capabilities for m in provider.models):
                    continue
            # Latency budget filter
            if profile.latency_budget_ms and provider.models:
                if all(m.latency_p50_ms > profile.latency_budget_ms for m in provider.models):
                    continue
            # Cost budget: only external models have cost; local is 0
            if profile.cost_budget_usd >= 0 and provider.kind == ProviderKind.EXTERNAL:
                # cost is per 1k tokens → estimate tokens = context_size
                est_cost = max((m.cost_per_1k_tokens * profile.context_size / 1000) for m in provider.models) if provider.models else 0
                if est_cost > profile.cost_budget_usd and profile.cost_budget_usd == 0:
                    # zero budget means no external spend allowed
                    continue
                if est_cost > profile.cost_budget_usd and profile.cost_budget_usd > 0:
                    continue
            candidates.append(provider)

        # Fallback to first available that passes privacy/context checks
        if not candidates:
            for provider in self._providers.values():
                if not provider.is_available():
                    continue
                if profile.privacy == "local" and provider.kind == ProviderKind.EXTERNAL:
                    continue
                if profile.context_size > 0 and provider.models:
                    if not any(m.context_window >= profile.context_size for m in provider.models):
                        continue
                candidates.append(provider)
                break

        if not candidates:
            # Ultimate fallback: deterministic (always available)
            return DETERMINISTIC_FALLBACK

        # Weighted scoring among candidates (capability + latency + cost)
        # Prefer lower latency and lower cost when capabilities equal
        def _score(p: Any) -> float:
            # capability match already filtered; score by inverse latency + cost
            latency = min((m.latency_p50_ms for m in p.models), default=1000)
            cost = min((m.cost_per_1k_tokens for m in p.models), default=0)
            # Lower is better → invert
            return (1000 - latency) * 0.5 + (1 - cost) * 100 + (100 if p.kind == ProviderKind.LOCAL else 0)

        candidates.sort(key=_score, reverse=True)
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
