"""AI Control Layer contracts (Phase 13 — ``/platform/v1/ai/*``).

Phase 13 establishes the governance machinery for AI without connecting
a model provider. These contracts define the JSON shape for:

* AI run lifecycle (start, step, complete, cancel)
* Tool lifecycle (register, invoke, audit)
* Policy enforcement (authority levels, mode handling)
* Audit events (immutable trail)

All contracts are content-addressed via SHA-256.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Timestamp


# ---------------------------------------------------------------------------
# Authority Levels (Section 27)
# ---------------------------------------------------------------------------


class AuthorityLevel(BaseModel):
    """Authority level as defined in PLATFORM_AI_ARCHITECTURE.md §8."""

    level: int = Field(ge=0, le=4)
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=512)
    enabled_by_default: bool = Field(default=False)


AUTHORITY_LEVELS: list[AuthorityLevel] = [
    AuthorityLevel(
        level=0,
        name="Observe",
        description="inspect / summarize / diagnose / recommend",
        enabled_by_default=True,
    ),
    AuthorityLevel(
        level=1,
        name="Analyze",
        description="run diagnostics / tests / compare evidence",
        enabled_by_default=True,
    ),
    AuthorityLevel(
        level=2,
        name="Development",
        description="modify code / create tests / execute verification",
        enabled_by_default=False,
    ),
    AuthorityLevel(
        level=3,
        name="Controlled Operations",
        description="state-changing app operations",
        enabled_by_default=False,
    ),
    AuthorityLevel(
        level=4,
        name="High-Risk",
        description="destructive migrations / bulk financial mutations / data deletion / production deployment",
        enabled_by_default=False,
    ),
]


# ---------------------------------------------------------------------------
# AI Modes
# ---------------------------------------------------------------------------


class AIMode(str, Enum):
    """Operating mode for the AI Control Layer."""

    MANUAL = "MANUAL"
    ASSISTED = "ASSISTED"
    AUTONOMOUS = "AUTONOMOUS"


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------


class ToolParameter(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    type: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=512)
    required: bool = Field(default=False)


class ToolSchema(BaseModel):
    """Schema for a governed AI tool."""

    name: str = Field(min_length=1, max_length=128)
    description: str = Field(min_length=1, max_length=2048)
    authority_level: int = Field(ge=0, le=4)
    parameters: list[ToolParameter] = Field(default_factory=list)
    returns: str = Field(min_length=1, max_length=256)
    idempotent: bool = Field(default=False)
    side_effects: str = Field(default="none", pattern="^(none|read|write|execute)$")


# ---------------------------------------------------------------------------
# AI Run
# ---------------------------------------------------------------------------


class AIStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REQUIRES_AUTHORIZATION = "REQUIRES_AUTHORIZATION"


class AIStep(BaseModel):
    """A single step in an AI run."""

    step_number: int = Field(ge=1)
    tool_name: str = Field(min_length=1, max_length=128)
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Timestamp
    completed_at: Optional[Timestamp] = None
    evidence_id: Optional[str] = None
    duration_ms: Optional[int] = None


class AIEnvelope(BaseModel):
    """Base envelope for AI run operations."""

    kind: str
    version: str
    generated_at: Timestamp
    id: Identity
    data: dict[str, Any]


# ---------------------------------------------------------------------------
# Tool Invocation
# ---------------------------------------------------------------------------


class ToolInvocationRequest(BaseModel):
    tool_name: str = Field(min_length=1, max_length=128)
    arguments: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None


class ToolInvocationResponse(BaseModel):
    run_id: str
    step: AIStep
    status: AIStatus


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


class PolicyDecision(BaseModel):
    allowed: bool
    reason: str = Field(min_length=1, max_length=1024)
    required_authorization: Optional[str] = None


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


class AuditEvent(BaseModel):
    event_id: str = Field(min_length=1, max_length=64)
    event_type: str = Field(min_length=1, max_length=128)
    run_id: Optional[str] = None
    tool_name: Optional[str] = None
    actor: str = Field(min_length=1, max_length=256)  # "human" or "ai"
    timestamp: Timestamp
    payload: dict[str, Any] = Field(default_factory=dict)
    policy_decision: Optional[PolicyDecision] = None


# ---------------------------------------------------------------------------
# Kinds
# ---------------------------------------------------------------------------

AI_RUN_KIND: str = "platform.ai_run"
AI_RUN_LIST_KIND: str = "platform.ai_run_list"
AI_TOOL_KIND: str = "platform.ai_tool"
AI_TOOL_LIST_KIND: str = "platform.ai_tool_list"
AI_POLICY_KIND: str = "platform.ai_policy"
AI_AUDIT_KIND: str = "platform.ai_audit"
AI_MODE_KIND: str = "platform.ai_mode"

__all__ = [
    "AuthorityLevel",
    "AUTHORITY_LEVELS",
    "AIMode",
    "AIStatus",
    "ToolSchema",
    "ToolParameter",
    "AIEnvelope",
    "AIStep",
    "ToolInvocationRequest",
    "ToolInvocationResponse",
    "PolicyDecision",
    "AuditEvent",
    "AI_RUN_KIND",
    "AI_RUN_LIST_KIND",
    "AI_TOOL_KIND",
    "AI_TOOL_LIST_KIND",
    "AI_POLICY_KIND",
    "AI_AUDIT_KIND",
    "AI_MODE_KIND",
]