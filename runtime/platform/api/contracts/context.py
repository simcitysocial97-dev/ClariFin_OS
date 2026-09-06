"""Context Pack contracts (Phase 14 — ``/platform/v1/context/*``).

Defines the JSON shape for context packs produced by the Context Engine.
Every component is content-addressed with provenance tracing.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Timestamp

CONTEXT_PACK_KIND: str = "platform.context_pack"


class ContextComponent(BaseModel):
    """A single component in a context pack."""

    type: str = Field(min_length=1, max_length=64)
    source_kind: str = Field(min_length=1, max_length=64)
    data: dict[str, object] = Field(default_factory=dict)
    provenance_ref: str = Field(min_length=1, max_length=256)
    token_estimate: int = Field(ge=0)
    relevance_score: float = Field(ge=0, le=100)


class OmittedComponent(BaseModel):
    """A component omitted due to budget constraints."""

    type: str
    tokens: int


class ContextPackData(BaseModel):
    kind: str = Field(default=CONTEXT_PACK_KIND, frozen=True)
    version: str = "1.0.0"
    generated_at: Timestamp
    symptom: str
    intent_type: str
    capability_id: str | None = None
    run_id: str | None = None
    components: list[ContextComponent] = Field(default_factory=list)
    total_tokens_estimate: int = Field(ge=0)
    token_budget: int = Field(ge=1)
    status: str = Field(pattern="^(complete|incomplete)$")
    omitted: list[OmittedComponent] = Field(default_factory=list)
    sources: list[dict[str, object]] = Field(default_factory=list)
    pack_id: str = Field(min_length=1)
    checksum: str | None = None


class ContextPackEnvelope(BaseModel):
    kind: str
    version: str
    generated_at: Timestamp
    id: Identity
    data: ContextPackData


__all__ = [
    "CONTEXT_PACK_KIND",
    "ContextComponent",
    "OmittedComponent",
    "ContextPackData",
    "ContextPackEnvelope",
]
