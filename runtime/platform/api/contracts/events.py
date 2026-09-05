"""Event bus contracts (Phase 1 — ``/platform/v1/events*``).

The Platform API exposes the C50 ``EngineeringEvent`` bus through:

* ``/events`` — recent events snapshot.
* ``/events/stream`` — SSE live stream.

Phase 1 only fixes the JSON shape; Phase 7 wires the SSE endpoint to
``runtime.system.observability.event_store.EngineeringEventStore``.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Timestamp


EVENTS_LIST_KIND: str = "platform.events_list"
EVENTS_STREAM_KIND: str = "platform.events_stream"


class PlatformEvent(BaseModel):
    """One event emitted by the C50 EngineeringEventStore."""

    id: str = Field(min_length=1, max_length=256)
    event_type: str = Field(min_length=1, max_length=64)
    task_id: str | None = Field(default=None, max_length=256)
    execution_id: str | None = Field(default=None, max_length=256)
    capability_id: str | None = Field(default=None, max_length=256)
    emitted_at: Timestamp
    payload: dict = Field(default_factory=dict)


class EventsListData(BaseModel):
    window: str = Field(min_length=1, max_length=64)
    count: int = Field(ge=0)
    items: list[PlatformEvent] = Field(default_factory=list)


class EventsListEnvelope(BaseModel):
    kind: str = Field(default=EVENTS_LIST_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: EventsListData


class EventsStreamEventData(BaseModel):
    """A single SSE event emitted by ``/events/stream``."""

    event: PlatformEvent
    emitted_at: Timestamp


class EventsStreamEventEnvelope(BaseModel):
    kind: str = Field(default=EVENTS_STREAM_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: EventsStreamEventData


__all__ = [
    "EVENTS_LIST_KIND",
    "EVENTS_STREAM_KIND",
    "EventsListData",
    "EventsListEnvelope",
    "EventsStreamEventData",
    "EventsStreamEventEnvelope",
    "PlatformEvent",
]
