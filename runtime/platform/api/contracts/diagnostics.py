"""Platform-level diagnostic contracts (Phase 11 — ``/platform/v1/diagnose/*``).

Phase 11 introduces the diagnostic engine. These contracts define the
JSON shape for diagnostic results and recommendations.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Timestamp


DIAGNOSTIC_RESULT_KIND: str = "platform.diagnostic_result"
DIAGNOSTIC_RECOMMENDATION_KIND: str = "platform.diagnostic_recommendation"
DIAGNOSTIC_SIGNATURE_KIND: str = "platform.diagnostic_signature"


class DiagnosticRecommendationItem(BaseModel):
    action: str = Field(min_length=1, max_length=128)
    target: str = Field(min_length=1, max_length=512)


class DiagnosticResultData(BaseModel):
    symptom: str = Field(min_length=1, max_length=1024)
    error_code: str | None = None
    capability_id: str | None = None
    level: str = Field(min_length=2, max_length=8)  # e.g. "L0", "L1", ...
    fact: str = Field(min_length=1, max_length=256)
    evidence: list[str] = Field(default_factory=list)
    affected_capability: str | None = None
    recommendation: list[DiagnosticRecommendationItem] = Field(default_factory=list)
    generated_at: Timestamp


class DiagnosticResultEnvelope(BaseModel):
    kind: str = Field(default=DIAGNOSTIC_RESULT_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: DiagnosticResultData


class DiagnosticRecommendationData(BaseModel):
    signature_id: str = Field(min_length=1, max_length=64)
    severity: str = Field(min_length=1, max_length=32)
    recommended_verification: list[str] = Field(default_factory=list)


class DiagnosticRecommendationEnvelope(BaseModel):
    kind: str = Field(default=DIAGNOSTIC_RECOMMENDATION_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: DiagnosticRecommendationData


class DiagnosticSignatureData(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    error_code: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=1024)
    affected_capability: str = Field(min_length=1, max_length=256)
    severity: str = Field(min_length=1, max_length=32)
    occurrences: int = Field(ge=0)
    first_seen: Timestamp
    last_seen: Timestamp


class DiagnosticSignatureEnvelope(BaseModel):
    kind: str = Field(default=DIAGNOSTIC_SIGNATURE_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: DiagnosticSignatureData


__all__ = [
    "DIAGNOSTIC_RESULT_KIND",
    "DIAGNOSTIC_RECOMMENDATION_KIND",
    "DIAGNOSTIC_SIGNATURE_KIND",
    "DiagnosticRecommendationData",
    "DiagnosticRecommendationEnvelope",
    "DiagnosticResultData",
    "DiagnosticResultEnvelope",
    "DiagnosticSignatureData",
    "DiagnosticSignatureEnvelope",
    "DiagnosticRecommendationItem",
]
