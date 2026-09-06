"""Executions service adapter (Phase 2 — ``/platform/v1/executions/*``).

Aggregates the live C50 ``EngineeringEventStore`` into the Phase 1
``ExecutionDetail`` and ``ExecutionStreamEvent`` contracts.

The execution-detail projection is event-driven: each event whose
``event_type`` references an ``execution_id`` contributes one row to the
detail payload's ``events`` list. No new persistent model is introduced
(per ``IMPLEMENTATION_ROADMAP.md`` Phase 2 "Do not introduce a new
persistent model for any of those domains").
"""

from __future__ import annotations

from typing import Any

from runtime.platform.api.contracts import executions as executions_contract
from runtime.platform.api.contracts._primitives import Status
from runtime.platform.api.services._helpers import envelope, now_iso
from runtime.system.observability.event_store import (
    EngineeringEvent,
    EngineeringEventStore,
)

__all__ = [
    "build_execution_detail",
    "build_execution_stream_event",
]


def _event_to_stream_event_payload(
    execution_id: str, event: EngineeringEvent
) -> dict[str, Any]:
    """Project one ``EngineeringEvent`` into a stream-event payload."""

    return {
        "execution_id": execution_id,
        "event_type": event.event_type,
        "payload": dict(event.payload or {}),
        "emitted_at": now_iso(),
    }


def build_execution_detail(execution_id: str) -> dict[str, Any] | None:
    """Build the ``platform.execution_detail`` envelope for one execution.

    Returns ``None`` when no event references the requested execution
    id. The caller is responsible for converting that to ``NOT_FOUND``.
    """

    store = EngineeringEventStore()
    matching: list[EngineeringEvent] = []
    for event in store.iter_events():
        meta = event.metadata or {}
        if meta.get("execution_id") == execution_id:
            matching.append(event)

    if not matching:
        return None

    # Sort by timestamp ascending; fall back to lexical order if timestamp
    # is unavailable.
    matching.sort(key=lambda e: (e.timestamp or "", e.event_id))

    capability_id = (
        matching[-1].metadata.get("capability_id") if matching[-1].metadata else None
    )
    task_id = matching[-1].metadata.get("task_id") if matching[-1].metadata else None

    started = (
        matching[0].timestamp.isoformat().replace("+00:00", "Z")
        if matching[0].timestamp
        else None
    )
    finished = (
        matching[-1].timestamp.isoformat().replace("+00:00", "Z")
        if matching[-1].timestamp and matching[-1].event_type.endswith("Completed")
        else None
    )

    data = {
        "id": execution_id,
        "task_id": task_id or execution_id,
        "capability_id": capability_id or "unknown",
        "status": Status.CLOSED.value if finished else Status.OPEN.value,
        "started_at": started or now_iso(),
        "finished_at": finished,
        "phase": "execution",
        "current_state": matching[-1].event_type,
        "events": [e.event_id for e in matching],
        "stdout_ref": None,
        "stderr_ref": None,
        "evidence_ids": [],
        "decision_id": None,
    }
    return envelope(kind=executions_contract.EXECUTION_DETAIL_KIND, data=data)


def build_execution_stream_event(
    execution_id: str, event: EngineeringEvent
) -> dict[str, Any]:
    """Build one ``platform.execution_stream_event`` envelope.

    Phase 3's SSE mount will wrap this in ``data: <json>\\n\\n`` lines.
    """

    data = _event_to_stream_event_payload(execution_id, event)
    return envelope(
        kind=executions_contract.EXECUTION_STREAM_EVENT_KIND,
        data=data,
    )
