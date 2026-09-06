"""Verification service adapter (Phase 2 — ``/platform/v1/verification/*``).

Aggregates the real C50 capability catalog and the live planner into the
Phase 1 ``VerificationRunRequest``, ``VerificationRunResult``, and
``VerificationRecommendation`` contracts.

Phase 2 is **read-mostly**. The actual run is delegated to the canonical
control plane (Phase 3 FastAPI mount will use ``ControlPlaneFacade.run``
and ``ControlPlaneFacade.plan`` for write endpoints).
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.verification.capability_catalog import get_capability_catalog
from runtime.foundation.verification.control_plane_facade import (
    ControlPlane,
    _collect_changed_files,
)
from runtime.platform.api.contracts import verification as verification_contract
from runtime.platform.api.contracts._primitives import Status
from runtime.platform.api.services._helpers import envelope, now_iso

__all__ = [
    "build_verification_run_request",
    "build_verification_run_result",
    "build_verification_recommendation",
]


def build_verification_run_request(
    *,
    capability_id: str,
    group: str | None = None,
    authorization_token: str | None = None,
) -> dict[str, Any]:
    """Build a ``platform.verification_run_request`` envelope.

    The request payload mirrors what Phase 3's FastAPI mount will accept.
    """

    data = {
        "capability_id": capability_id,
        "group": group,
        "authorization_token": authorization_token,
    }
    return envelope(
        kind=verification_contract.VERIFICATION_RUN_REQUEST_KIND,
        data=data,
    )


def build_verification_run_result(
    *,
    capability_id: str,
    status_value: Status,
    task_id: str | None = None,
    execution_id: str | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
    duration_ms: int | None = None,
    message: str,
) -> dict[str, Any]:
    """Build a ``platform.verification_run_result`` envelope."""

    data = {
        "capability_id": capability_id,
        "status": status_value.value,
        "task_id": task_id,
        "execution_id": execution_id,
        "started_at": started_at or now_iso(),
        "finished_at": finished_at,
        "duration_ms": duration_ms,
        "message": message,
    }
    return envelope(
        kind=verification_contract.VERIFICATION_RUN_RESULT_KIND,
        data=data,
    )


def build_verification_recommendation() -> dict[str, Any]:
    """Build a ``platform.verification_recommendation`` envelope.

    Uses the live blast-radius + planner chain to decide which
    capabilities should be run given the current working-tree changes.
    """

    catalog = get_capability_catalog()
    cp = ControlPlane()
    files = _collect_changed_files()
    plan = cp.planner.plan(files)
    directly_affected = sorted(
        plan.capability_resolution.directly_affected_capabilities
    )
    transitively = sorted(plan.capability_resolution.transitively_affected_capabilities)
    recommended = sorted(set(directly_affected + transitively))
    # Filter to capabilities that exist in the catalog (defensive: the
    # planner may reference capability IDs that are not yet registered).
    catalog_ids = {e.capability_id for e in catalog.entries}
    recommended = [c for c in recommended if c in catalog_ids]

    rationale = (
        f"derived from {len(files)} working-tree change(s); "
        f"{len(directly_affected)} direct, {len(transitively)} transitive"
    )
    data = {"recommended": recommended, "rationale": rationale}
    return envelope(
        kind=verification_contract.VERIFICATION_RECOMMENDATION_KIND,
        data=data,
    )
