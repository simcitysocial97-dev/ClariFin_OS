"""Model Provider protocol (Phase 15).

Abstract interface for LLM providers. Platforms remain decoupled from
vendor-specific implementations. Providers can be local (Ollama),
external (OpenRouter, Anthropic), or mock/deterministic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol


class ProviderKind(str, Enum):
    LOCAL = "local"
    EXTERNAL = "external"


class ToolChoice(str, Enum):
    AUTO = "auto"
    NONE = "none"
    REQUIRED = "required"


@dataclass(frozen=True)
class ModelDescriptor:
    """A specific model variant available from a provider."""

    name: str
    context_window: int
    capabilities: list[str]
    cost_per_1k_tokens: float
    latency_p50_ms: int


@dataclass(frozen=True)
class Message:
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_calls: list[dict[str, Any]] | None = None


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class CompletionResult:
    model: str
    text: str
    finish_reason: str  # "stop", "length", "tool_calls"
    usage: dict[str, int]
    tool_calls: list[dict[str, Any]] | None = None
    provider: str = ""
    latency_ms: int = 0
    deterministic: bool = False  # True when no LLM was used


@dataclass(frozen=True)
class ProviderHealth:
    provider: str
    reachable: bool
    last_check: datetime
    last_success: datetime | None
    last_failure: datetime | None
    failure_streak: int = 0
    p50_latency_ms: int = 0
    notes: str = ""


class RoutingProfile:
    """Request-level routing configuration."""

    def __init__(
        self,
        task_kind: str,
        context_size: int,
        privacy: str = "local",
        latency_budget_ms: int = 30_000,
        cost_budget_usd: float = 0.0,
        required_capability: str | None = None,
        availability_required: bool = False,
    ):
        self.task_kind = task_kind
        self.context_size = context_size
        self.privacy = privacy
        self.latency_budget_ms = latency_budget_ms
        self.cost_budget_usd = cost_budget_usd
        self.required_capability = required_capability
        self.availability_required = availability_required

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_kind": self.task_kind,
            "context_size": self.context_size,
            "privacy": self.privacy,
            "latency_budget_ms": self.latency_budget_ms,
            "cost_budget_usd": self.cost_budget_usd,
            "required_capability": self.required_capability,
            "availability_required": self.availability_required,
        }


class ModelProvider(Protocol):
    """Protocol that all model providers must implement."""

    name: str
    kind: ProviderKind

    @property
    def models(self) -> list[ModelDescriptor]: ...

    @abstractmethod
    def complete(
        self,
        *,
        model: str,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
        tool_choice: ToolChoice | str = ToolChoice.AUTO,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> CompletionResult: ...

    @abstractmethod
    def health(self) -> ProviderHealth: ...

    @abstractmethod
    def is_available(self) -> bool: ...


class BaseProvider(ABC):
    """Base class for model providers."""

    def __init__(self, name: str, kind: ProviderKind, default_model: str, **model_kwargs: Any) -> None:
        self.name = name
        self.kind = kind
        self._default_model = default_model
        self._models: list[ModelDescriptor] = []
        self._health: ProviderHealth = ProviderHealth(
            provider=name,
            reachable=False,
            last_check=datetime.utcnow(),
            last_success=None,
            last_failure=None,
        )
        self._failure_streak = 0
        self._setup_models(**model_kwargs)

    def _setup_models(self, **kwargs: Any) -> None: ...

    @property
    def models(self) -> list[ModelDescriptor]:
        return self._models

    @property
    def health(self) -> ProviderHealth:
        return self._health

    def mark_healthy(self, latency_ms: int = 0) -> None:
        self._health = ProviderHealth(
            provider=self.name,
            reachable=True,
            last_check=datetime.utcnow(),
            last_success=datetime.utcnow(),
            last_failure=self._health.last_failure,
            failure_streak=0,
            p50_latency_ms=latency_ms or self._health.p50_latency_ms,
        )

    def mark_unhealthy(self, notes: str = "") -> None:
        self._failure_streak += 1
        self._health = ProviderHealth(
            provider=self.name,
            reachable=False,
            last_check=datetime.utcnow(),
            last_success=self._health.last_success,
            last_failure=datetime.utcnow(),
            failure_streak=self._failure_streak,
            notes=notes or self._health.notes,
        )

    def is_available(self) -> bool:
        return self._health.reachable and self._failure_streak < 3
