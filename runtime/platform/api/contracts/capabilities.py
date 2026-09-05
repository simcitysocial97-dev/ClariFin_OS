"""Capability contracts (Phase 1 — ``/platform/v1/capabilities``).

Phase 1 defines the JSON shape of capability list / detail / graph
endpoints. Phase 2 services will populate these contracts from
``runtime.foundation.verification.capability_catalog*``.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Timestamp


CAPABILITY_LIST_KIND: str = "platform.capability_list"
CAPABILITY_DETAIL_KIND: str = "platform.capability_detail"
CAPABILITY_GRAPH_KIND: str = "platform.capability_graph"


class CapabilityListItem(BaseModel):
    """Single row in the capability list response."""

    id: str = Field(min_length=1, max_length=256)
    name: str = Field(min_length=1, max_length=256)
    stage: str = Field(min_length=1, max_length=64)
    cost: str = Field(min_length=1, max_length=16)
    authorization: str = Field(min_length=1, max_length=32)
    produces: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)


class CapabilityListData(BaseModel):
    """Top-level capability-list data."""

    count: int = Field(ge=0)
    categories: list[str] = Field(default_factory=list)
    items: list[CapabilityListItem] = Field(default_factory=list)


class CapabilityListEnvelope(BaseModel):
    kind: str = Field(default=CAPABILITY_LIST_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: CapabilityListData


class CapabilityDetailData(BaseModel):
    """Single capability detail."""

    id: str = Field(min_length=1, max_length=256)
    name: str = Field(min_length=1, max_length=256)
    stage: str = Field(min_length=1, max_length=64)
    cost: str = Field(min_length=1, max_length=16)
    authorization: str = Field(min_length=1, max_length=32)
    owner: str = Field(min_length=1, max_length=256)
    command: Optional[str] = None
    dependencies: list[str] = Field(default_factory=list)
    produces: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    recent_executions: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    cache_status: Optional[str] = None
    failure_history: list[str] = Field(default_factory=list)
    health: str = Field(min_length=1, max_length=32)


class CapabilityDetailEnvelope(BaseModel):
    kind: str = Field(default=CAPABILITY_DETAIL_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: CapabilityDetailData


class CapabilityGraphData(BaseModel):
    """Dependency subgraph for one capability."""

    capability_id: str = Field(min_length=1, max_length=256)
    upstream: list[str] = Field(default_factory=list)
    downstream: list[str] = Field(default_factory=list)


class CapabilityGraphEnvelope(BaseModel):
    kind: str = Field(default=CAPABILITY_GRAPH_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: CapabilityGraphData


__all__ = [
    "CAPABILITY_DETAIL_KIND",
    "CAPABILITY_GRAPH_KIND",
    "CAPABILITY_LIST_KIND",
    "CapabilityDetailData",
    "CapabilityDetailEnvelope",
    "CapabilityGraphData",
    "CapabilityGraphEnvelope",
    "CapabilityListData",
    "CapabilityListEnvelope",
    "CapabilityListItem",
]
