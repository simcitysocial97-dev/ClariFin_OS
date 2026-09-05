"""Evidence service adapter (Phase 2 — ``/platform/v1/evidence/*``).

Aggregates the live C50 obligation set's evidence references into the
Phase 1 ``EvidenceList``, ``EvidenceDetail``, and ``EvidenceCompare``
contracts.

No new evidence model is introduced. Evidence identity remains the
canonical ``EvidenceContract`` from C50; this adapter projects it into
the typed list/detail payloads Phase 3 will expose.

Compare is a deliberate structural projection: ``delta`` returns the
fingerprint difference between the two evidence payloads so that the GUI
can render a meaningful diff without the API pretending to know what
matters semantically (semantic comparison belongs to Phase 8).
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.verification.control_plane_facade import (
    ControlPlane,
    _collect_changed_files,
)
from runtime.platform.api.contracts import evidence as evidence_contract
from runtime.platform.api.contracts._primitives import Status
from runtime.platform.api.services._helpers import envelope, now_iso

__all__ = [
    "build_evidence_list",
    "build_evidence_detail",
    "build_evidence_compare",
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
    """

    items, _ = _list_items()
    known = {row["id"] for row in items}
    if left_id not in known or right_id not in known:
        return None

    # Phase 2 comparison is structural: clients receive a delta dict
    # with the *raw* differences between the two list rows. Semantic
    # comparison (test failures, durations, recovered failures, …) lives
    # in Phase 8 — see ``IMPLEMENTATION_ROADMAP.md``.
    left = next(row for row in items if row["id"] == left_id)
    right = next(row for row in items if row["id"] == right_id)

    delta: dict[str, Any] = {}
    for key in ("status", "capability_id", "kind"):
        if left.get(key) != right.get(key):
            delta[key] = {"left": left.get(key), "right": right.get(key)}

    data = {"left_id": left_id, "right_id": right_id, "delta": delta}
    return envelope(kind=evidence_contract.EVIDENCE_COMPARE_KIND, data=data)
