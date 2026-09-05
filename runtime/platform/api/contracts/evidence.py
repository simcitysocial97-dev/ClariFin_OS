"""Evidence contracts (Phase 1 — ``/platform/v1/evidence/*``).

Phase 1 defines the JSON shape for evidence list, detail, and compare.
Phase 2 services populate these contracts from
``runtime.system.evidence.*`` and ``runtime.foundation.verification.evidence_*``.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Status, Timestamp


EVIDENCE_LIST_KIND: str = "platform.evidence_list"
EVIDENCE_DETAIL_KIND: str = "platform.evidence_detail"
EVIDENCE_COMPARE_KIND: str = "platform.evidence_compare"


class EvidenceListItem(BaseModel):
    id: str = Field(min_length=1, max_length=256)
    kind: str = Field(min_length=1, max_length=64)
    capability_id: Optional[str] = Field(default=None, max_length=256)
    execution_id: Optional[str] = Field(default=None, max_length=256)
    collected_at: Timestamp
    status: Status
    summary: str = Field(min_length=1, max_length=1024)


class EvidenceListData(BaseModel):
    count: int = Field(ge=0)
    items: list[EvidenceListItem] = Field(default_factory=list)


class EvidenceListEnvelope(BaseModel):
    kind: str = Field(default=EVIDENCE_LIST_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: EvidenceListData


class EvidenceDetailData(BaseModel):
    id: str = Field(min_length=1, max_length=256)
    kind: str = Field(min_length=1, max_length=64)
    capability_id: Optional[str] = Field(default=None, max_length=256)
    execution_id: Optional[str] = Field(default=None, max_length=256)
    collected_at: Timestamp
    status: Status
    summary: str = Field(min_length=1, max_length=1024)
    payload: dict = Field(default_factory=dict)
    references: list[str] = Field(default_factory=list)


class EvidenceDetailEnvelope(BaseModel):
    kind: str = Field(default=EVIDENCE_DETAIL_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: EvidenceDetailData


class EvidenceCompareData(BaseModel):
    """Result of ``/evidence/compare``.

    Phase 1 keeps the delta shape deliberately minimal. Phase 8 will
    extend the comparison engine; the contract is structured so that
    ``delta`` can be widened without breaking existing clients.
    """

    left_id: str = Field(min_length=1, max_length=256)
    right_id: str = Field(min_length=1, max_length=256)
    delta: dict = Field(default_factory=dict)


class EvidenceCompareEnvelope(BaseModel):
    kind: str = Field(default=EVIDENCE_COMPARE_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: EvidenceCompareData


__all__ = [
    "EVIDENCE_COMPARE_KIND",
    "EVIDENCE_DETAIL_KIND",
    "EVIDENCE_LIST_KIND",
    "EvidenceCompareData",
    "EvidenceCompareEnvelope",
    "EvidenceDetailData",
    "EvidenceDetailEnvelope",
    "EvidenceListData",
    "EvidenceListEnvelope",
    "EvidenceListItem",
]
