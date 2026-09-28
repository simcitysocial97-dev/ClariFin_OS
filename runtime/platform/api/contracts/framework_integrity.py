"""Framework Integrity contracts (Phase 1 — ``/platform/v1/framework/integrity``).

Exposes the C62 FrameworkIntegrityResult as a canonical Platform API contract.
This is the authoritative self-diagnostic surface for the verification framework.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Timestamp

FRAMEWORK_INTEGRITY_KIND: str = "platform.framework_integrity"


class FrameworkHealth(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


class DriftClassification(str, Enum):
    IMPLEMENTATION_DEFECT = "IMPLEMENTATION_DEFECT"
    AUTHORITY_DRIFT = "AUTHORITY_DRIFT"
    CONFIGURATION_DRIFT = "CONFIGURATION_DRIFT"
    CI_BYPASS = "CI_BYPASS"
    EVIDENCE_INTEGRITY_DEFECT = "EVIDENCE_INTEGRITY_DEFECT"
    ARTIFACT_INTEGRITY_DEFECT = "ARTIFACT_INTEGRITY_DEFECT"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    PRE_EXISTING = "PRE_EXISTING"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    UNRELATED = "UNRELATED"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DriftFinding(BaseModel):
    """A single drift finding from the authority drift detector."""

    check_name: str = Field(min_length=1)
    detected_component: str = Field(min_length=1)
    expected_authority: str = Field(min_length=1)
    actual_authority: str = Field(min_length=1)
    classification: DriftClassification
    source_evidence: str
    severity: Severity


class FrameworkIntegrityData(BaseModel):
    """Framework integrity result data (mirrors C62 FrameworkIntegrityResult)."""

    schema_version: str = "m9-c62-framework-integrity/v1"
    generated_at: Timestamp
    health: FrameworkHealth
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    total_findings: int = 0
    findings: list[DriftFinding] = Field(default_factory=list)
    artifact_summary: dict = Field(default_factory=dict)
    diagnostic: dict = Field(default_factory=dict)

    @property
    def healthy(self) -> bool:
        return self.health == FrameworkHealth.HEALTHY


class FrameworkIntegrityEnvelope(BaseModel):
    """Full Platform API success envelope for ``/framework/integrity``."""

    kind: str = Field(default=FRAMEWORK_INTEGRITY_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: FrameworkIntegrityData


class FrameworkSelfTestResult(BaseModel):
    """Individual self-test result (K1-K9)."""

    name: str
    passed: bool
    detail: str | None = None


class FrameworkSelfTestsData(BaseModel):
    """Framework self-tests summary (K1-K9)."""

    results: list[FrameworkSelfTestResult] = Field(default_factory=list)
    passed: int = 0
    total: int = 0

    @property
    def all_passed(self) -> bool:
        return self.passed == self.total and self.total > 0


class FrameworkSelfTestsEnvelope(BaseModel):
    kind: str = "platform.framework_self_tests"
    version: str
    generated_at: Timestamp
    id: Identity
    data: FrameworkSelfTestsData


__all__ = [
    "DriftClassification",
    "DriftFinding",
    "FrameworkHealth",
    "FrameworkIntegrityData",
    "FrameworkIntegrityEnvelope",
    "FRAMEWORK_INTEGRITY_KIND",
    "FrameworkSelfTestResult",
    "FrameworkSelfTestsData",
    "FrameworkSelfTestsEnvelope",
    "Severity",
]

# Alias for backward compatibility
FrameworkIntegrityKIND = FRAMEWORK_INTEGRITY_KIND