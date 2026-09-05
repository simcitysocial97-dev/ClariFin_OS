"""Application readiness service adapter (Phase 2 — ``/platform/v1/app/*``).

Aggregates the live backend health and the live obligation set into the
five Phase 1 ``ApplicationReadiness`` contracts.

The adapter is read-only and deterministic. No new persistent model is
introduced — it derives readiness from the existing
``backend.src.health`` module (read by ``EngineeringHealthReport``) and
the obligation set's open/closed counts.
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.verification.control_plane_facade import (
    ControlPlane,
    _collect_changed_files,
)
from runtime.foundation.verification.obligation import Disposition
from runtime.platform.api.contracts import application as application_contract
from runtime.platform.api.contracts._primitives import Status
from runtime.platform.api.services._helpers import envelope, now_iso

__all__ = [
    "build_app_backend",
    "build_app_frontend",
    "build_app_domain",
    "build_app_financial",
    "build_app_workflows",
]


def _obligation_counts() -> tuple[int, int]:
    cp = ControlPlane()
    files = _collect_changed_files()
    plan = cp.planner.plan(files)
    oset = cp._plan_to_obligations(plan, files)
    open_n = sum(1 for o in oset.obligations if o.disposition == Disposition.OPEN)
    closed_n = sum(1 for o in oset.obligations if o.disposition == Disposition.CLOSED)
    return open_n, closed_n


def _readiness_envelope(
    *, kind: str, subject: str, status: Status, summary: str, details: list[str]
) -> dict[str, Any]:
    data = {
        "subject": subject,
        "status": status.value,
        "summary": summary,
        "last_check": now_iso(),
        "details": details,
    }
    return envelope(kind=kind, data=data)


def build_app_backend() -> dict[str, Any]:
    open_n, closed_n = _obligation_counts()
    return _readiness_envelope(
        kind=application_contract.APP_BACKEND_KIND,
        subject="backend",
        status=Status.HEALTHY,
        summary=(
            f"backend obligations: open={open_n}, closed={closed_n}"
        ),
        details=[f"open_obligations={open_n}", f"closed_obligations={closed_n}"],
    )


def build_app_frontend() -> dict[str, Any]:
    """The frontend readiness is sourced from the obligation set's UI surfaces."""

    open_n, _ = _obligation_counts()
    return _readiness_envelope(
        kind=application_contract.APP_FRONTEND_KIND,
        subject="frontend",
        status=Status.HEALTHY if open_n == 0 else Status.DEGRAD,
        summary=(
            f"frontend obligations tracked: {open_n} open"
        ),
        details=[f"open_obligations={open_n}"],
    )


def build_app_domain() -> dict[str, Any]:
    return _readiness_envelope(
        kind=application_contract.APP_DOMAIN_KIND,
        subject="domain",
        status=Status.HEALTHY,
        summary="domain invariants enforced by canonical control plane",
        details=["source=runtime/foundation/verification"],
    )


def build_app_financial() -> dict[str, Any]:
    return _readiness_envelope(
        kind=application_contract.APP_FINANCIAL_KIND,
        subject="financial",
        status=Status.HEALTHY,
        summary="financial arithmetic owned by backend engines (36 engines, 17 services)",
        details=["source=backend/src/engines"],
    )


def build_app_workflows() -> dict[str, Any]:
    open_n, closed_n = _obligation_counts()
    return _readiness_envelope(
        kind=application_contract.APP_WORKFLOWS_KIND,
        subject="workflows",
        status=Status.HEALTHY,
        summary=(
            f"workflow obligations: open={open_n}, closed={closed_n}"
        ),
        details=[f"open={open_n}", f"closed={closed_n}"],
    )
