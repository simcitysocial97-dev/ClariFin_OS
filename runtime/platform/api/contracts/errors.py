"""Platform-level error aggregator contracts (Phase 1 — ``/platform/v1/errors/*``).

Phase 1 fixes the JSON shape for the platform-wide Error Observatory.
Phase 9 (``9A — Error Observatory``) services populate these contracts
from ``backend.src.errors``, C50 verification failures, and AI run
errors. The aggregator does not parse log files; it reads structured
records produced by the underlying authorities.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Timestamp

ERRORS_CURRENT_KIND: str = "platform.errors_current"
ERRORS_RECENT_KIND: str = "platform.errors_recent"
ERRORS_RECURRING_KIND: str = "platform.errors_recurring"
ERRORS_FREQUENCY_KIND: str = "platform.errors_frequency"
ERRORS_DETAIL_KIND: str = "platform.errors_detail"


class PlatformErrorItem(BaseModel):
    """A single platform-aggregated error record."""

    id: str = Field(min_length=1, max_length=256)
    code: str = Field(min_length=1, max_length=64)
    layer: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=2048)
    first_seen: Timestamp
    last_seen: Timestamp
    occurrences: int = Field(ge=1)
    affected_workflow: str | None = Field(default=None, max_length=256)


class PlatformErrorsListData(BaseModel):
    """Common payload for current / recent / recurring error listings."""

    window: str = Field(min_length=1, max_length=64)
    count: int = Field(ge=0)
    items: list[PlatformErrorItem] = Field(default_factory=list)


class PlatformErrorsListEnvelope(BaseModel):
    """Envelope wrapper used by current / recent / recurring endpoints.

    The ``kind`` field is intentionally not frozen so that the same
    envelope model can carry each endpoint's specific kind value.
    """

    kind: str
    version: str
    generated_at: Timestamp
    id: Identity
    data: PlatformErrorsListData


class PlatformErrorsFrequencyBucket(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    layer: str = Field(min_length=1, max_length=64)
    count: int = Field(ge=0)


class PlatformErrorsFrequencyData(BaseModel):
    window: str = Field(min_length=1, max_length=64)
    total: int = Field(ge=0)
    buckets: list[PlatformErrorsFrequencyBucket] = Field(default_factory=list)


class PlatformErrorsFrequencyEnvelope(BaseModel):
    kind: str = Field(default=ERRORS_FREQUENCY_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: PlatformErrorsFrequencyData


class PlatformErrorsDetailData(BaseModel):
    item: PlatformErrorItem
    recent_occurrences: list[Timestamp] = Field(default_factory=list)
    related_capabilities: list[str] = Field(default_factory=list)
    related_evidence: list[str] = Field(default_factory=list)


class PlatformErrorsDetailEnvelope(BaseModel):
    kind: str = Field(default=ERRORS_DETAIL_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: PlatformErrorsDetailData


__all__ = [
    "ERRORS_CURRENT_KIND",
    "ERRORS_DETAIL_KIND",
    "ERRORS_FREQUENCY_KIND",
    "ERRORS_RECENT_KIND",
    "ERRORS_RECURRING_KIND",
    "PlatformErrorItem",
    "PlatformErrorsDetailData",
    "PlatformErrorsDetailEnvelope",
    "PlatformErrorsFrequencyBucket",
    "PlatformErrorsFrequencyData",
    "PlatformErrorsFrequencyEnvelope",
    "PlatformErrorsListData",
    "PlatformErrorsListEnvelope",
]
