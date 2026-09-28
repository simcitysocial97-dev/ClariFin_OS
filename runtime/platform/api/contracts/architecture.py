"""Architecture safety contracts (Phase 1 — ``/platform/v1/architecture/*``).

Phase 1 fixes the JSON shape for the architecture safety endpoints.
Phase 9B services populate these from the existing authority modules:

* ``runtime.foundation.verification.configuration_authority``
* ``runtime.foundation.verification.route_authority``
* ``runtime.foundation.verification.capability_authority``
* ``runtime.foundation.verification.control_plane_efficiency``
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Status, Timestamp

ARCHITECTURE_AUTHORITIES_KIND: str = "platform.architecture_authorities"
ARCHITECTURE_AUTHORITY_KIND: str = "platform.architecture_authority"
ARCHITECTURE_BOUNDARIES_KIND: str = "platform.architecture_boundaries"
ARCHITECTURE_DUPLICATES_KIND: str = "platform.architecture_duplicates"
ARCHITECTURE_BYPASSES_KIND: str = "platform.architecture_bypasses"
ARCHITECTURE_DEPRECATIONS_KIND: str = "platform.architecture_deprecations"
ARCHITECTURE_UNMAPPED_KIND: str = "platform.architecture_unmapped"


class AuthoritySummary(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    owner: str = Field(min_length=1, max_length=256)
    status: Status
    last_check: Timestamp
    issues: int = Field(ge=0)


class ArchitectureAuthoritiesData(BaseModel):
    count: int = Field(ge=0)
    items: list[AuthoritySummary] = Field(default_factory=list)


class ArchitectureAuthoritiesEnvelope(BaseModel):
    kind: str = Field(default=ARCHITECTURE_AUTHORITIES_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: ArchitectureAuthoritiesData


class AuthorityDetailData(BaseModel):
    """Single authority detail (Phase 9B — ``/architecture/authority/{name}``)."""

    name: str = Field(min_length=1, max_length=128)
    owner: str = Field(min_length=1, max_length=256)
    status: Status
    last_check: Timestamp
    description: str = Field(min_length=1, max_length=2048)
    recent_evidence: list[str] = Field(default_factory=list)
    issues: int = Field(ge=0)


class AuthorityDetailEnvelope(BaseModel):
    kind: str = Field(default=ARCHITECTURE_AUTHORITY_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: AuthorityDetailData


class ArchitectureIssue(BaseModel):
    """A single architecture safety finding."""

    id: str = Field(min_length=1, max_length=256)
    severity: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=256)
    location: str = Field(min_length=1, max_length=512)
    evidence: list[str] = Field(default_factory=list)
    first_seen: Timestamp | None = None


class ArchitectureFindingsData(BaseModel):
    """Common payload for boundaries / duplicates / bypasses / deprecations / unmapped."""

    count: int = Field(ge=0)
    items: list[ArchitectureIssue] = Field(default_factory=list)


class ArchitectureFindingsEnvelope(BaseModel):
    """Envelope wrapper for the five ``/architecture/*`` listing endpoints."""

    kind: str
    version: str
    generated_at: Timestamp
    id: Identity
    data: ArchitectureFindingsData


__all__ = [
    "ARCHITECTURE_AUTHORITIES_KIND",
    "ARCHITECTURE_AUTHORITY_KIND",
    "ARCHITECTURE_BOUNDARIES_KIND",
    "ARCHITECTURE_BYPASSES_KIND",
    "ARCHITECTURE_DEPRECATIONS_KIND",
    "ARCHITECTURE_DUPLICATES_KIND",
    "ARCHITECTURE_UNMAPPED_KIND",
    "ArchitectureAuthoritiesData",
    "ArchitectureAuthoritiesEnvelope",
    "ArchitectureFindingsData",
    "ArchitectureFindingsEnvelope",
    "ArchitectureIssue",
    "AuthorityDetailData",
    "AuthorityDetailEnvelope",
    "AuthoritySummary",
]
