"""Status contract (C67.1 — Platform API Foundation).

Defines the JSON shape for ``GET /platform/v1/status`` — an
operator-oriented snapshot of the canonical runtime state.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Status, Timestamp

STATUS_KIND: str = "platform.status"


class StatusData(BaseModel):
    """Operator-oriented runtime snapshot."""

    repository: str = Field(min_length=1, max_length=512)
    commit_sha: str = Field(min_length=1, max_length=64)
    tree_sha: str | None = None
    branch: str = Field(min_length=0, max_length=128)
    runtime_version: str = Field(min_length=1, max_length=64)
    fingerprint: str | None = None
    framework_health: Status
    certification_state: str = Field(min_length=0, max_length=64)
    capability_count: int = Field(ge=0)
    profile_count: int = Field(ge=0)
    workflow_count: int = Field(ge=0)
    recent_run_status: Status | None = None
    recent_run_id: str | None = None
    configuration_identity: str | None = None
    last_updated: Timestamp


class StatusEnvelope(BaseModel):
    kind: str = Field(default=STATUS_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: StatusData


__all__ = [
    "STATUS_KIND",
    "StatusData",
    "StatusEnvelope",
]
