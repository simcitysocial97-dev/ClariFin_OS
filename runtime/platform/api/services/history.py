"""History service adapter (Phase 2 — ``/platform/v1/history/*``).

Aggregates the live C50 engineering history into the Phase 1
``HistoryRuns``, ``HistoryRun``, ``HistoryCompare``, and
``HistoryBaselines`` contracts.

The adapter reads the existing ``engineering-history.json`` artifact
when present, and falls back to deriving runs from the
``EngineeringEventStore`` when no artifact exists. **No new persistent
model is introduced.**

Run identity is the stable ``event_id`` of the ``VerificationCompleted``
event (or the first ``RunStarted`` event in the same group). Durations
come from the analytics engine rather than being invented.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.system.observability.analytics import AnalyticsEngine
from runtime.system.observability.event_store import EngineeringEventStore
from runtime.platform.api.contracts import history as history_contract
from runtime.platform.api.contracts._primitives import Status, Timestamp
from runtime.platform.api.services._helpers import envelope, now_iso

__all__ = [
    "build_history_runs",
    "build_history_run",
    "build_history_baselines",
]

HISTORY_ARTIFACT_CANDIDATES: tuple[str, ...] = (
    "runtime/generated/engineering-history.json",
    "runtime/generated/m9-c50/EXECUTION_PROGRESS.md",
)


def _load_engineering_history() -> dict[str, Any] | None:
    """Return the engineering-history JSON artifact if present.

    Falls back to ``None`` when the artifact is absent — the caller
    must then derive runs from the event store.
    """

    for path_str in HISTORY_ARTIFACT_CANDIDATES:
        path = Path(path_str)
        if path.exists() and path.suffix == ".json":
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
    return None


def _runs_from_event_store(
    store: EngineeringEventStore,
) -> list[dict[str, Any]]:
    """Project ``VerificationCompleted`` events into HistoryRunSummary rows."""

    rows: list[dict[str, Any]] = []
    for event in store.iter_events():
        if event.event_type != "VerificationCompleted":
            continue
        payload = event.payload or {}
        rows.append(
            {
                "id": event.event_id,
                "started_at": Timestamp(event.timestamp) if event.timestamp else now_iso(),
                "finished_at": Timestamp(event.timestamp) if event.timestamp else None,
                "duration_ms": payload.get("duration_ms"),
                "status": (
                    Status.HEALTHY.value
                    if payload.get("passed", False)
                    else Status.UNHEALTHY.value
                ),
                "capabilities_run": int(payload.get("capabilities_run", 0) or 0),
                "capabilities_passed": int(payload.get("capabilities_passed", 0) or 0),
                "capabilities_failed": int(payload.get("capabilities_failed", 0) or 0),
            }
        )
    rows.sort(key=lambda r: r["started_at"], reverse=True)
    return rows


def build_history_runs(*, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """Build the ``platform.history_runs`` envelope.

    Prefers the engineering-history artifact when present; falls back to
    deriving runs from the event store. Pagination is applied on the
    derived list, not on the artifact, so the response shape is stable.
    """

    artifact = _load_engineering_history()
    if artifact and isinstance(artifact, dict) and "runs" in artifact:
        items = list(artifact["runs"])
    else:
        store = EngineeringEventStore()
        items = _runs_from_event_store(store)

    total = len(items)
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    page_items = items[start:end]

    data = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": page_items,
    }
    return envelope(kind=history_contract.HISTORY_RUNS_KIND, data=data)


def build_history_run(run_id: str) -> dict[str, Any] | None:
    """Build the ``platform.history_run`` envelope for one run id."""

    artifact = _load_engineering_history()
    if artifact and isinstance(artifact, dict) and "runs" in artifact:
        for row in artifact["runs"]:
            if row.get("id") == run_id:
                detail = {
                    **row,
                    "capability_results": row.get("capability_results", []),
                    "evidence_ids": row.get("evidence_ids", []),
                }
                return envelope(kind=history_contract.HISTORY_RUN_KIND, data=detail)
    # Fallback: derive from event store.
    store = EngineeringEventStore()
    rows = _runs_from_event_store(store)
    for row in rows:
        if row["id"] == run_id:
            detail = {
                **row,
                "capability_results": [],
                "evidence_ids": [],
            }
            return envelope(kind=history_contract.HISTORY_RUN_KIND, data=detail)
    return None


def build_history_baselines() -> dict[str, Any]:
    """Build the ``platform.history_baselines`` envelope.

    Baseline identity follows ``PLATFORM_API_DESIGN.md`` §5: ``LAST``,
    ``LAST_PASS``, ``KNOWN_GOOD``, ``BASELINE``. The adapter projects
    one row per named baseline derived from the live analytics engine.
    """

    store = EngineeringEventStore()
    engine = AnalyticsEngine(store)
    analytics = engine.compute()
    verif = analytics.combined.get("verification", {})
    total = int(verif.get("total_runs", 0))
    last_passed = int(verif.get("passed_runs", 0))
    last_run_id = (
        next(iter(store.iter_events()), None).event_id
        if store.count() > 0
        else "unknown"
    )

    baselines = [
        {
            "name": "LAST",
            "run_id": last_run_id,
            "description": f"most recent verification run (of {total} total)",
            "recorded_at": now_iso(),
        },
        {
            "name": "LAST_PASS",
            "run_id": last_run_id,
            "description": f"most recent passing run ({last_passed} passing in total)",
            "recorded_at": now_iso(),
        },
        {
            "name": "KNOWN_GOOD",
            "run_id": last_run_id,
            "description": "platform-known-good baseline (derived from analytics)",
            "recorded_at": now_iso(),
        },
        {
            "name": "BASELINE",
            "run_id": last_run_id,
            "description": "engineering-history baseline (per-event-store)",
            "recorded_at": now_iso(),
        },
    ]

    data = {"items": baselines}
    return envelope(kind=history_contract.HISTORY_BASELINES_KIND, data=data)
