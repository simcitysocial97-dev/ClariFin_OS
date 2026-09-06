"""Tasks service adapter (Phase 2 — ``/platform/v1/tasks``).

Aggregates the real C50 obligation set into the Phase 1 ``TaskList``,
``TaskDetail``, and ``TaskCancel`` contracts.

The adapter is **read-only**. Cancelling a task is intentionally out of
scope for Phase 2 — Phase 3 (FastAPI mount) will route the cancel
operation through ``ControlPlaneFacade`` so that the canonical control
plane remains the single authority for state-changing operations.
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.verification.control_plane_facade import (
    ControlPlane,
    _collect_changed_files,
)
from runtime.foundation.verification.obligation import Disposition, ObligationSet
from runtime.platform.api.contracts import tasks as tasks_contract
from runtime.platform.api.contracts._primitives import Status
from runtime.platform.api.services._helpers import envelope, now_iso

__all__ = [
    "build_task_list",
    "build_task_detail",
]


def _build_obligation_set() -> ObligationSet:
    """Return the live obligation set derived from the canonical planner."""

    cp = ControlPlane()
    files = _collect_changed_files()
    plan = cp.planner.plan(files)
    return cp._plan_to_obligations(plan, files)


def _iso(dt: Any) -> str:
    """Convert a datetime-like to ISO-8601 UTC ``Z`` form.

    Accepts either ``datetime`` instances or pre-formatted strings.
    Falls back to ``now_iso()`` when the input is ``None``.
    """

    if dt is None:
        return now_iso()
    if isinstance(dt, str):
        # Already a string — normalize trailing ``+00:00`` to ``Z``.
        if dt.endswith("+00:00"):
            return dt[:-6] + "Z"
        return dt
    iso = dt.isoformat()
    # Normalize ``+00:00`` to ``Z`` so we satisfy the Phase 1 Timestamp
    # contract primitive.
    if iso.endswith("+00:00"):
        return iso[:-6] + "Z"
    return iso


def _obligation_to_task_item(o: Any) -> dict[str, Any]:
    """Project one :class:`VerificationObligation` to a Phase 1 task item."""

    status_value = (
        Status.CLOSED.value
        if o.disposition == Disposition.CLOSED
        else Status.OPEN.value
    )
    req = getattr(o, "requirement", None)
    cap = getattr(o, "capability", None)
    return {
        "id": o.obligation_id,
        "name": (req.rationale if req else o.obligation_id),
        "capability_id": (cap.capability_id if cap else "unknown"),
        "status": status_value,
        "created_at": _iso(o.created_at),
        "closed_at": _iso(o.closed_at) if o.closed_at else None,
    }


def build_task_list() -> dict[str, Any]:
    """Build the ``platform.task_list`` envelope from the live obligation set."""

    oset = _build_obligation_set()
    items = [_obligation_to_task_item(o) for o in oset.obligations]
    open_count = sum(1 for o in oset.obligations if o.disposition == Disposition.OPEN)
    closed_count = sum(
        1 for o in oset.obligations if o.disposition == Disposition.CLOSED
    )
    data = {
        "open_count": open_count,
        "closed_count": closed_count,
        "items": items,
    }
    return envelope(kind=tasks_contract.TASK_LIST_KIND, data=data)


def build_task_detail(task_id: str) -> dict[str, Any] | None:
    """Build the ``platform.task_detail`` envelope for one obligation id.

    Returns ``None`` when the obligation is not in the live set — the
    caller (Phase 3 router) is responsible for converting that into a
    ``NOT_FOUND`` error envelope.
    """

    oset = _build_obligation_set()
    target = None
    for o in oset.obligations:
        if o.obligation_id == task_id:
            target = o
            break
    if target is None:
        return None

    status_value = (
        Status.CLOSED.value
        if target.disposition == Disposition.CLOSED
        else Status.OPEN.value
    )

    data = {
        "id": target.obligation_id,
        "name": (
            target.requirement.rationale if target.requirement else target.obligation_id
        ),
        "capability_id": (
            target.capability.capability_id if target.capability else "unknown"
        ),
        "status": status_value,
        "created_at": _iso(target.created_at),
        "closed_at": _iso(target.closed_at) if target.closed_at else None,
        "plan": [],
        "obligations": [target.obligation_id],
        "evidence_ids": [e for e in (target.evidence or []) if e],
        "decision_id": None,
    }
    return envelope(kind=tasks_contract.TASK_DETAIL_KIND, data=data)
