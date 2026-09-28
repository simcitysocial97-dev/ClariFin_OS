"""Change intelligence contracts (Phase 1 — ``/platform/v1/change/intelligence``).

Phase 10 services populate this contract from the existing C50 modules:

* ``runtime.foundation.verification.blast_radius``
* ``runtime.foundation.verification.change_surface``
* ``runtime.foundation.verification.capability_resolver``
* ``runtime.foundation.verification.evidence_integrity``
* ``runtime.foundation.verification.capability_graph``

Phase 1 only fixes the JSON shape.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Timestamp

CHANGE_INTELLIGENCE_KIND: str = "platform.change_intelligence"


class ChangedFileEntry(BaseModel):
    path: str = Field(min_length=1, max_length=512)
    change_type: str = Field(min_length=1, max_length=32)


class ChangeIntelligenceData(BaseModel):
    changed_files: list[ChangedFileEntry] = Field(default_factory=list)
    affected_capabilities: list[str] = Field(default_factory=list)
    stale_evidence: list[str] = Field(default_factory=list)
    affected_tests: list[str] = Field(default_factory=list)
    affected_workflows: list[str] = Field(default_factory=list)
    recommended_verification: list[str] = Field(default_factory=list)
    risk: str = Field(min_length=1, max_length=32)
    generated_from: Timestamp


class ChangeIntelligenceEnvelope(BaseModel):
    kind: str = Field(default=CHANGE_INTELLIGENCE_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: ChangeIntelligenceData


__all__ = [
    "CHANGE_INTELLIGENCE_KIND",
    "ChangeIntelligenceData",
    "ChangeIntelligenceEnvelope",
    "ChangedFileEntry",
]
