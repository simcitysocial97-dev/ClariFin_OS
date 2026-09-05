"""Verification contracts (Phase 1 — ``/platform/v1/verification/*``).

Phase 1 only fixes the JSON shape. Phase 2 services wrap
``runtime.foundation.verification.canonical_control_plane``.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Status, Timestamp


VERIFICATION_RUN_REQUEST_KIND: str = "platform.verification_run_request"
VERIFICATION_RUN_RESULT_KIND: str = "platform.verification_run_result"
VERIFICATION_RECOMMENDATION_KIND: str = "platform.verification_recommendation"


class VerificationRunRequestData(BaseModel):
    """Request body for ``/verification/run``.

    Phase 1 keeps this minimal: ``capability_id`` is the only required
    field. Optional flags will be added in Phase 6.
    """

    capability_id: str = Field(min_length=1, max_length=256)
    group: Optional[str] = None
    authorization_token: Optional[str] = None


class VerificationRunRequestEnvelope(BaseModel):
    kind: str = Field(default=VERIFICATION_RUN_REQUEST_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: VerificationRunRequestData


class VerificationRunResultData(BaseModel):
    capability_id: str = Field(min_length=1, max_length=256)
    status: Status
    task_id: Optional[str] = None
    execution_id: Optional[str] = None
    started_at: Timestamp
    finished_at: Optional[Timestamp] = None
    duration_ms: Optional[int] = Field(default=None, ge=0)
    message: str = Field(min_length=1, max_length=1024)


class VerificationRunResultEnvelope(BaseModel):
    kind: str = Field(default=VERIFICATION_RUN_RESULT_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: VerificationRunResultData


class VerificationRecommendationData(BaseModel):
    """Output of ``/verification/what-should-i-run``."""

    recommended: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1, max_length=1024)


class VerificationRecommendationEnvelope(BaseModel):
    kind: str = Field(default=VERIFICATION_RECOMMENDATION_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: VerificationRecommendationData


__all__ = [
    "VERIFICATION_RECOMMENDATION_KIND",
    "VERIFICATION_RUN_REQUEST_KIND",
    "VERIFICATION_RUN_RESULT_KIND",
    "VerificationRecommendationData",
    "VerificationRecommendationEnvelope",
    "VerificationRunRequestData",
    "VerificationRunRequestEnvelope",
    "VerificationRunResultData",
    "VerificationRunResultEnvelope",
]
