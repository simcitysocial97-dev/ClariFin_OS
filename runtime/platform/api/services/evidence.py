"""Evidence service adapter (Phase 2 — ``/platform/v1/evidence/*``).

Aggregates the live C50 obligation set's evidence references into the
Phase 1 ``EvidenceList``, ``EvidenceDetail``, and ``EvidenceCompare``
contracts.

No new evidence model is introduced. Evidence identity remains the
canonical ``EvidenceContract`` from C50; this adapter projects it into
the typed list/detail payloads Phase 3 will expose.

Phase 8 adds:
* ``build_evidence_by_execution`` — evidence scoped to one execution.
* Enhanced ``build_evidence_compare`` — semantic delta across all
  required dimensions.
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.verification.control_plane_facade import (
    ControlPlane,
    _collect_changed_files,
)
from runtime.platform.api.contracts import evidence as evidence_contract
from runtime.platform.api.contracts._primitives import Status
from runtime.platform.api.services._comparison import compute_evidence_delta
from runtime.platform.api.services._helpers import envelope, now_iso
from runtime.system.observability.event_store import EngineeringEventStore

__all__ = [
    "build_evidence_list",
    "build_evidence_detail",
    "build_evidence_compare",
    "build_evidence_by_execution",
]


def _evidence_for_obligation(obl: Any) -> list[str]:
    """Return the list of evidence ids attached to one obligation."""

    refs = []
    for ev in getattr(obl, "evidence", []) or []:
        if isinstance(ev, str):
            if ev:
                refs.append(ev)
        elif isinstance(ev, dict):
            for key in ("evidence_id", "id", "fingerprint"):
                value = ev.get(key)
                if value:
                    refs.append(str(value))
                    break
        else:
            obj_id = getattr(ev, "evidence_id", None) or getattr(ev, "fingerprint", None)
            if obj_id:
                refs.append(str(obj_id))
    return refs


def _list_items() -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Walk the live obligation set, returning a list row and an id→capability map."""

    cp = ControlPlane()
    files = _collect_changed_files()
    plan = cp.planner.plan(files)
    oset = cp._plan_to_obligations(plan, files)

    items: list[dict[str, Any]] = []
    cap_by_id: dict[str, str] = {}
    for obl in oset.obligations:
        cap_id = obl.capability.capability_id if obl.capability else "unknown"
        evidence_ids = _evidence_for_obligation(obl)
        for eid in evidence_ids:
            cap_by_id[eid] = cap_id
            items.append(
                {
                    "id": eid,
                    "kind": "verification",
                    "capability_id": cap_id,
                    "execution_id": obl.task_id or obl.obligation_id,
                    "collected_at": now_iso(),
                    "status": (
                        Status.CLOSED.value
                        if obl.disposition.value == "closed"
                        else Status.OPEN.value
                    ),
                    "summary": (
                        obl.requirement.description
                        if obl.requirement
                        else obl.obligation_id
                    ),
                }
            )
    return items, cap_by_id


def build_evidence_list() -> dict[str, Any]:
    """Build the ``platform.evidence_list`` envelope from live obligations."""

    items, _ = _list_items()
    data = {"count": len(items), "items": items}
    return envelope(kind=evidence_contract.EVIDENCE_LIST_KIND, data=data)


def build_evidence_detail(evidence_id: str) -> dict[str, Any] | None:
    """Build the ``platform.evidence_detail`` envelope for one evidence id.

    Returns ``None`` when the id is not present in the live obligation
    set — the caller converts that to ``NOT_FOUND``.
    """

    items, cap_by_id = _list_items()
    for row in items:
        if row["id"] == evidence_id:
            data = {
                **row,
                "payload": {},
                "references": [],
            }
            # Remove the execution_id field that is not in EvidenceDetailData
            data.pop("execution_id", None)
            cap_id = data.get("capability_id")
            return envelope(
                kind=evidence_contract.EVIDENCE_DETAIL_KIND,
                data=data,
            )
    # We also want to return NOT_FOUND when the id exists only in cap_by_id
    # (i.e. it was attached but did not yield a list row for any reason).
    if evidence_id in cap_by_id:
        data = {
            "id": evidence_id,
            "kind": "verification",
            "capability_id": cap_by_id[evidence_id],
            "execution_id": None,
            "collected_at": now_iso(),
            "status": Status.UNKNOWN.value,
            "summary": "evidence reference without full payload",
            "payload": {},
            "references": [],
        }
        return envelope(
            kind=evidence_contract.EVIDENCE_DETAIL_KIND,
            data=data,
        )
    return None


def build_evidence_compare(left_id: str, right_id: str) -> dict[str, Any] | None:
    """Build the ``platform.evidence_compare`` envelope for two evidence ids.

    Returns ``None`` when either id is not present in the live set.

    Phase 8: semantic delta computed via :func:`compute_evidence_delta`.
    """

    items, _ = _list_items()
    known = {row["id"] for row in items}
    if left_id not in known or right_id not in known:
        return None

    left = next(row for row in items if row["id"] == left_id)
    right = next(row for row in items if row["id"] == right_id)

    delta = compute_evidence_delta(left, right)

    data = {"left_id": left_id, "right_id": right_id, "delta": delta}
    return envelope(kind=evidence_contract.EVIDENCE_COMPARE_KIND, data=data)


def build_evidence_by_execution(execution_id: str) -> dict[str, Any] | None:
    """Build the ``platform.evidence_list`` envelope scoped to one execution.

    Queries the ``EngineeringEventStore`` for all events whose metadata
    carries the given ``execution_id``.  Projects those events into
    evidence-like list rows so the GUI can display every event that
    belongs to a single run.

    Returns ``None`` when no events reference the execution id.
    """

    store = EngineeringEventStore()
    matching = [
        e
        for e in store.iter_events()
        if (e.metadata or {}).get("execution_id") == execution_id
    ]
    if not matching:
        return None

    items: list[dict[str, Any]] = []
    for event in matching:
        payload = event.payload or {}
        items.append(
            {
                "id": event.event_id,
                "kind": event.event_type,
                "capability_id": (event.metadata or {}).get("capability_id", "unknown"),
                "execution_id": execution_id,
                "collected_at": now_iso(),
                "status": (
                    Status.CLOSED.value
                    if event.event_type == "VerificationCompleted"
                    else Status.OPEN.value
                ),
                "summary": payload.get("final_decision")
                or event.event_type,
            }
        )

    data = {"count": len(items), "items": items}
    return envelope(kind=evidence_contract.EVIDENCE_LIST_KIND, data=data)
