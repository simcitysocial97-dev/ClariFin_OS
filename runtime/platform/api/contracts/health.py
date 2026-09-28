"""Health snapshot contract (Phase 1 — ``/platform/v1/health``).

The health snapshot aggregates the high-level platform status across the
sub-systems that Phase 2/3 services will populate. Phase 1 only defines
the shape. Services that fill this contract live in Phase 2.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Status, Timestamp

HEALTH_KIND: str = "platform.health_snapshot"


class DomainHealth(BaseModel):
    """A single sub-system health row."""

    name: str = Field(min_length=1, max_length=128)
    status: Status
    last_check: Timestamp
    source: str = Field(min_length=1, max_length=256)
    detail: str | None = None


class HealthSnapshotData(BaseModel):
    """Top-level health snapshot data."""

    platform: Status
    backend: Status
    frontend: Status
    database: Status
    architecture: Status
    verification: Status
    evidence: Status
    ai: Status
    domains: list[DomainHealth] = Field(default_factory=list)


class HealthSnapshotEnvelope(BaseModel):
    """Full Platform API success envelope for ``/health``.

    The contract is the envelope itself so that Phase 2 services and
    Phase 3 routers cannot accidentally diverge from the documented JSON
    shape.
    """

    kind: str = Field(default=HEALTH_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: HealthSnapshotData


__all__ = [
    "DomainHealth",
    "HealthSnapshotData",
    "HealthSnapshotEnvelope",
    "HEALTH_KIND",
]
