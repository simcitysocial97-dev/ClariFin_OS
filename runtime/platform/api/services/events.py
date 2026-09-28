"""Events service adapter (Phase 2 — ``/platform/v1/events*``).

Aggregates the live C50 ``EngineeringEventStore`` into the Phase 1
``EventsList`` and ``EventsStreamEvent`` contracts.

The SSE envelope is a superset of the existing ``EngineeringEvent``
record so that Phase 3 can stream events without re-serialization. No
new persistent model is introduced.
"""

from __future__ import annotations

from typing import Any

from runtime.platform.api.contracts import events as events_contract
from runtime.platform.api.contracts._primitives import Timestamp
from runtime.platform.api.services._helpers import envelope, now_iso
from runtime.system.observability.event_store import (
    EngineeringEvent,
    EngineeringEventStore,
)

__all__ = [
    "build_events_list",
    "build_events_stream_event",
]


def _event_to_platform_event(event: EngineeringEvent) -> dict[str, Any]:
    """Project an :class:`EngineeringEvent` to the Phase 1 ``PlatformEvent`` shape."""

    meta = event.metadata or {}
    return {
        "id": event.event_id,
        "event_type": event.event_type,
        "task_id": meta.get("task_id"),
        "execution_id": meta.get("execution_id"),
        "capability_id": meta.get("capability_id"),
        "emitted_at": Timestamp(event.timestamp) if event.timestamp else now_iso(),
        "payload": dict(event.payload or {}),
    }


def build_events_list(*, limit: int = 100) -> dict[str, Any]:
    """Build the ``platform.events_list`` envelope.

    The ``window`` field is intentionally coarse (``recent``) because the
    underlying event store does not yet index by time range — Phase 3's
    SSE mount will provide true live streaming.
    """

    store = EngineeringEventStore()
    events = list(store.iter_events())
    # Sort descending by timestamp so callers see the newest first.
    events.sort(key=lambda e: (e.timestamp or "", e.event_id), reverse=True)
    if limit > 0:
        events = events[:limit]
    items = [_event_to_platform_event(e) for e in events]
    data = {"window": "recent", "count": len(items), "items": items}
    return envelope(kind=events_contract.EVENTS_LIST_KIND, data=data)


def build_events_stream_event(event: EngineeringEvent) -> dict[str, Any]:
    """Build one ``platform.events_stream`` envelope.

    Phase 3's SSE mount will wrap this in ``data: <json>\\n\\n`` lines.
    """

    data = {
        "event": _event_to_platform_event(event),
        "emitted_at": now_iso(),
    }
    return envelope(kind=events_contract.EVENTS_STREAM_KIND, data=data)
