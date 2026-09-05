"""Application readiness contracts (Phase 1 — ``/platform/v1/app/*``).

Phase 12 services populate these contracts from:

* ``backend.src.health``
* ``backend.src.core.domain``
* the platform's own health snapshot.

Phase 1 only fixes the JSON shape.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Status, Timestamp


APP_BACKEND_KIND: str = "platform.app_backend"
APP_FRONTEND_KIND: str = "platform.app_frontend"
APP_DOMAIN_KIND: str = "platform.app_domain"
APP_FINANCIAL_KIND: str = "platform.app_financial"
APP_WORKFLOWS_KIND: str = "platform.app_workflows"


class ApplicationReadinessData(BaseModel):
    """Common payload used by every ``/app/*`` readiness endpoint."""

    subject: str = Field(min_length=1, max_length=64)
    status: Status
    summary: str = Field(min_length=1, max_length=1024)
    last_check: Timestamp
    details: list[str] = Field(default_factory=list)


class ApplicationReadinessEnvelope(BaseModel):
    """Envelope wrapper used by every ``/app/*`` readiness endpoint."""

    kind: str
    version: str
    generated_at: Timestamp
    id: Identity
    data: ApplicationReadinessData


__all__ = [
    "APP_BACKEND_KIND",
    "APP_DOMAIN_KIND",
    "APP_FINANCIAL_KIND",
    "APP_FRONTEND_KIND",
    "APP_WORKFLOWS_KIND",
    "ApplicationReadinessData",
    "ApplicationReadinessEnvelope",
]
