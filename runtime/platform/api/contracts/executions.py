"""Execution contracts (Phase 1 — ``/platform/v1/executions/*``).

Phase 1 defines the JSON shape for execution detail and the SSE event
stream. The SSE envelope is a superset of
``runtime.system.observability.event_store.EngineeringEvent`` so that
existing C50 events can flow through the Platform API without
re-serialization.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Status, Timestamp


EXECUTION_DETAIL_KIND: str = "platform.execution_detail"
EXECUTION_STREAM_EVENT_KIND: str = "platform.execution_stream_event"


class ExecutionDetailData(BaseModel):
    id: str = Field(min_length=1, max_length=256)
    task_id: str = Field(min_length=1, max_length=256)
    capability_id: str = Field(min_length=1, max_length=256)
    status: Status
    started_at: Timestamp
    finished_at: Optional[Timestamp] = None
    phase: str = Field(min_length=1, max_length=64)
    current_state: str = Field(min_length=1, max_length=256)
    events: list[str] = Field(default_factory=list)
    stdout_ref: Optional[str] = None
    stderr_ref: Optional[str] = None
    evidence_ids: list[str] = Field(default_factory=list)
    decision_id: Optional[str] = None


class ExecutionDetailEnvelope(BaseModel):
    kind: str = Field(default=EXECUTION_DETAIL_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: ExecutionDetailData


class ExecutionStreamEventData(BaseModel):
    """A single SSE event emitted by ``/executions/{id}/stream``."""

    execution_id: str = Field(min_length=1, max_length=256)
    event_type: str = Field(min_length=1, max_length=64)
    payload: dict = Field(default_factory=dict)
    emitted_at: Timestamp


class ExecutionStreamEventEnvelope(BaseModel):
    kind: str = Field(default=EXECUTION_STREAM_EVENT_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: ExecutionStreamEventData


__all__ = [
    "EXECUTION_DETAIL_KIND",
    "EXECUTION_STREAM_EVENT_KIND",
    "ExecutionDetailData",
    "ExecutionDetailEnvelope",
    "ExecutionStreamEventData",
    "ExecutionStreamEventEnvelope",
]
