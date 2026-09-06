"""AI Providers package (Phase 15).

Provider abstraction for LLM routing. Supports local (Ollama) and
external providers with deterministic fallback.
"""

from __future__ import annotations

from runtime.platform.ai.providers.base import (
    ProviderKind,
    ToolChoice,
    ModelDescriptor,
    Message,
    ToolSpec,
    CompletionResult,
    ProviderHealth,
    RoutingProfile,
    ModelProvider,
    BaseProvider,
)
from runtime.platform.ai.providers.local import (
    LocalOllamaProvider,
    LocalLargeProvider,
    OpenRouterProvider,
    DeterministicFallbackProvider,
    LOCAL_OLLAMA_PROVIDER,
    LOCAL_LARGE_PROVIDER,
    OPENROUTER_PROVIDER,
    DETERMINISTIC_FALLBACK,
)
from runtime.platform.ai.providers.router import (
    ModelRouter,
    MODEL_ROUTER_INSTANCE,
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
    "DeterministicFallbackProvider",
    "LOCAL_OLLAMA_PROVIDER",
    "DETERMINISTIC_FALLBACK",
    # Router
    "ModelRouter",
    "MODEL_ROUTER_INSTANCE",
]
