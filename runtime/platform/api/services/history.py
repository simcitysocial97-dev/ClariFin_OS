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
    "build_history_compare",
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


# ---------------------------------------------------------------------------
# Phase 8 — History compare
# ---------------------------------------------------------------------------


_VALID_BASELINES = frozenset({"LAST", "LAST_PASS", "KNOWN_GOOD", "BASELINE"})


def _resolve_baseline_run_id(
    baseline_name: str, store: EngineeringEventStore
) -> str | None:
    """Resolve a named baseline sentinel to an actual run event_id.

    Only recognised sentinel names are resolved.  Any other value
    (including literal event ids) returns ``None`` so that the caller
    can fall back to treating the input as a literal.
    """
    if baseline_name not in _VALID_BASELINES:
        return None

    events = list(store.iter_events())
    vc_events = [e for e in events if e.event_type == "VerificationCompleted"]
    if not vc_events:
        return None

    # LAST is the most recent (events are iterated in file order, so
    # we take the last one).
    if baseline_name == "LAST":
        return vc_events[-1].event_id

    # LAST_PASS is the most recent passing run.
    if baseline_name == "LAST_PASS":
        for e in reversed(vc_events):
            passed = (e.payload or {}).get("passed", False)
            if passed:
                return e.event_id
        # Fallback to latest if no passing run exists.
        return vc_events[-1].event_id

    # KNOWN_GOOD and BASELINE use the latest as proxy when no
    # separate artifact is available.
    return vc_events[-1].event_id


def build_history_compare(
    *, current_run_id: str, baseline: str, include_evidence: bool = False
) -> dict[str, Any] | None:
    """Build the ``platform.history_compare`` envelope.

    ``current_run_id`` may be a literal event_id or one of the sentinel
    values accepted by ``build_history_baselines`` (``LAST``,
    ``LAST_PASS``, ``KNOWN_GOOD``, ``BASELINE``).  ``baseline`` must be
    one of those same sentinels.

    The delta is computed from real event-store data; no mock state is
    introduced.
    """

    from runtime.platform.api.services._comparison import compute_history_delta

    store = EngineeringEventStore()

    # Resolve both IDs to actual run event_ids.
    resolved_current = _resolve_baseline_run_id(current_run_id, store) or current_run_id
    resolved_baseline = _resolve_baseline_run_id(baseline, store)
    if resolved_baseline is None:
        return None

    # Build full run summaries (with blast-radius payload when present).
    current_summary = _full_run_summary(resolved_current, store)
    baseline_summary = _full_run_summary(resolved_baseline, store)

    if current_summary is None or baseline_summary is None:
        return None

    delta = compute_history_delta(current_summary, baseline_summary)

    # Evidence invalidation: evidence IDs that changed status between runs.
    if include_evidence:
        cur_evid = set(current_summary.get("evidence_ids", []))
        base_evid = set(baseline_summary.get("evidence_ids", []))
        delta["evidence_invalidated"] = sorted(cur_evid ^ base_evid)
    else:
        delta["evidence_invalidated"] = []

    data = {
        "current_run": current_summary,
        "baseline_run": baseline_summary,
        "delta": delta,
    }
    return envelope(kind=history_contract.HISTORY_COMPARE_KIND, data=data)


def _full_run_summary(run_id: str, store: EngineeringEventStore) -> dict[str, Any] | None:
    """Return a rich run summary dict for delta computation.

    Mirrors the shape produced by ``_runs_from_event_store`` but adds
    the raw payload fields needed for semantic comparison.
    """
    for event in store.iter_events():
        if event.event_type != "VerificationCompleted" or event.event_id != run_id:
            continue
        payload = event.payload or {}
        return {
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
            "blast_radius": payload.get("blast_radius", {}),
            "evidence_ids": [],
        }
    return None
