"""AI Providers package (Phase 15).

Provider abstraction for LLM routing. Supports local (Ollama) and
external providers with deterministic fallback.
"""

from __future__ import annotations

from runtime.platform.ai.providers.base import (
    BaseProvider,
    CompletionResult,
    Message,
    ModelDescriptor,
    ModelProvider,
    ProviderHealth,
    ProviderKind,
    RoutingProfile,
    ToolChoice,
    ToolSpec,
)
from runtime.platform.ai.providers.local import (
    DETERMINISTIC_FALLBACK,
    LOCAL_LARGE_PROVIDER,
    LOCAL_OLLAMA_PROVIDER,
    OPENROUTER_PROVIDER,
    DeterministicFallbackProvider,
    LocalLargeProvider,
    LocalOllamaProvider,
    OpenRouterProvider,
)
from runtime.platform.ai.providers.router import (
    MODEL_ROUTER_INSTANCE,
    ModelRouter,
)

__all__ = [
    # Base
    "ProviderKind",
    "ToolChoice",
    "ModelDescriptor",
    "Message",
    "ToolSpec",
    "CompletionResult",
    "ProviderHealth",
    "RoutingProfile",
    "ModelProvider",
    "BaseProvider",
    # Local
    "LocalOllamaProvider",
    "LocalLargeProvider",
    "OpenRouterProvider",
    "DeterministicFallbackProvider",
    "LOCAL_OLLAMA_PROVIDER",
    "LOCAL_LARGE_PROVIDER",
    "OPENROUTER_PROVIDER",
    "DETERMINISTIC_FALLBACK",
    # Router
    "ModelRouter",
    "MODEL_ROUTER_INSTANCE",
]
