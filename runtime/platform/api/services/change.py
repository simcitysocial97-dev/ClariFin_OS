"""Change intelligence service adapter (Phase 2 — ``/platform/v1/change/intelligence``).

Aggregates the live C50 blast-radius + change-surface + evidence-integrity
chain into the Phase 1 ``ChangeIntelligence`` contract.

The adapter is read-only and deterministic; it produces the same payload
for the same working tree. Phase 10 will add the diagnostic reasoning
that consumes this contract.
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.verification.blast_radius import compute_blast_radius
from runtime.foundation.verification.change_surface import (
    SurfaceKind,
    discover_working_tree_changes,
)
from runtime.foundation.verification.control_plane_facade import (
    ControlPlane,
    _collect_changed_files,
)
from runtime.platform.api.contracts import change as change_contract
from runtime.platform.api.contracts._primitives import Timestamp
from runtime.platform.api.services._helpers import envelope, now_iso

__all__ = ["build_change_intelligence"]


def _risk_from_contract(contract: Any) -> str:
    """Translate blast-radius signals into a coarse ``risk`` value."""

    if contract.is_fail_closed:
        return "HIGH"
    escalations = list(contract.escalation_conditions or [])
    if escalations:
        return "HIGH"
    directly = len(contract.directly_affected_capabilities or [])
    transitively = len(contract.transitively_affected_capabilities or [])
    if directly + transitively == 0:
        return "LOW"
    if directly + transitively > 5:
        return "MEDIUM"
    return "LOW"


def build_change_intelligence() -> dict[str, Any]:
    """Build the ``platform.change_intelligence`` envelope from live state."""

    contract = compute_blast_radius()
    files = _collect_changed_files()
    cp = ControlPlane()
    plan = cp.planner.plan(files)
    cap_res = plan.capability_resolution

    # Discover per-file change-type classification.
    changed_files: list[dict[str, Any]] = []
    for path in discover_working_tree_changes():
        change_type = "modified"
        try:
            from runtime.foundation.verification.change_surface import (
                _classify_path,
            )

            surface_kind, _added, _removed, _is_test, _reason = _classify_path(path)
            if surface_kind == SurfaceKind.ADDED:
                change_type = "added"
            elif surface_kind == SurfaceKind.REMOVED:
                change_type = "removed"
        except Exception:
            # The classifier is private — if its signature changes we
            # fall back to "modified" rather than blowing up the API.
            pass
        changed_files.append({"path": path, "change_type": change_type})

    affected_caps = sorted(
        set(
            list(cap_res.directly_affected_capabilities or [])
            + list(cap_res.transitively_affected_capabilities or [])
        )
    )
    stale_evidence = sorted(
        str(inv) for inv in (contract.evidence_invalidations or [])
    )
    affected_tests = sorted(
        str(req) for req in (contract.required_tests or [])
    )
    affected_workflows = sorted(contract.affected_workflows or [])
    recommended = sorted(contract.minimum_safe_verification or [])

    data = {
        "changed_files": changed_files,
        "affected_capabilities": affected_caps,
        "stale_evidence": stale_evidence,
        "affected_tests": affected_tests,
        "affected_workflows": affected_workflows,
        "recommended_verification": recommended,
        "risk": _risk_from_contract(contract),
        "generated_from": Timestamp(contract.generated_at) if contract.generated_at else now_iso(),
    }
    return envelope(kind=change_contract.CHANGE_INTELLIGENCE_KIND, data=data)
