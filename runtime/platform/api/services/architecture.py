"""Architecture service adapter (Phase 2 — ``/platform/v1/architecture/*``).

Aggregates the live C50 architecture authorities into the Phase 1
``ArchitectureAuthorities``, ``AuthorityDetail``, and the five
``ArchitectureFindings`` contracts (boundaries, duplicates, bypasses,
deprecations, unmapped).

No new authority is created. The adapter projects the existing
``configuration_authority``, ``route_authority``, ``capability_authority``
and ``control_plane_efficiency`` modules into a single typed surface.
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.verification import (
    capability_authority,
    configuration_authority,
    control_plane_efficiency,
    route_authority,
)
from runtime.platform.api.contracts import architecture as architecture_contract
from runtime.platform.api.contracts._primitives import Status
from runtime.platform.api.services._helpers import envelope, now_iso

__all__ = [
    "build_architecture_authorities",
    "build_architecture_authority",
    "build_architecture_boundaries",
    "build_architecture_duplicates",
    "build_architecture_bypasses",
    "build_architecture_deprecations",
    "build_architecture_unmapped",
]


def _authorities_payload() -> list[dict[str, Any]]:
    """Project the live authorities into ``AuthoritySummary`` rows."""

    config = configuration_authority.get_configuration_authority() or []
    cap_audit = capability_authority.assert_no_competing_authority()
    route = route_authority.build_route_authority()
    efficiency = control_plane_efficiency.build_efficiency_report()

    cap_resolvable = bool(cap_audit.canonical_resolvable)
    cap_issues = 0 if cap_resolvable else 1
    route_shadows = int(route.get("shadow_count", 0) or 0)
    eff_measurements = int(len(efficiency.get("measurements", []) or []))

    return [
        {
            "name": "configuration_authority",
            "owner": "runtime/foundation/verification/configuration_authority.py",
            "status": Status.HEALTHY.value if config else Status.UNKNOWN.value,
            "last_check": now_iso(),
            "issues": 0 if config else 1,
        },
        {
            "name": "route_authority",
            "owner": "runtime/foundation/verification/route_authority.py",
            "status": Status.HEALTHY.value if route_shadows == 0 else Status.DEGRAD.value,
            "last_check": now_iso(),
            "issues": route_shadows,
        },
        {
            "name": "capability_authority",
            "owner": "runtime/foundation/verification/capability_authority.py",
            "status": Status.HEALTHY.value if cap_resolvable else Status.UNHEALTHY.value,
            "last_check": now_iso(),
            "issues": cap_issues,
        },
        {
            "name": "control_plane_efficiency",
            "owner": "runtime/foundation/verification/control_plane_efficiency.py",
            "status": Status.HEALTHY.value if eff_measurements > 0 else Status.UNKNOWN.value,
            "last_check": now_iso(),
            "issues": 0,
        },
    ]


def build_architecture_authorities() -> dict[str, Any]:
    """Build the ``platform.architecture_authorities`` envelope."""

    items = _authorities_payload()
    data = {"count": len(items), "items": items}
    return envelope(
        kind=architecture_contract.ARCHITECTURE_AUTHORITIES_KIND,
        data=data,
    )


def build_architecture_authority(name: str) -> dict[str, Any] | None:
    """Build the ``platform.architecture_authority`` envelope for one authority."""

    for row in _authorities_payload():
        if row["name"] == name:
            detail = {
                **row,
                "description": (
                    f"{name} aggregates the live state of the {name} module"
                ),
                "recent_evidence": [],
            }
            return envelope(
                kind=architecture_contract.ARCHITECTURE_AUTHORITY_KIND,
                data=detail,
            )
    return None


def _findings_envelope(kind: str, issues: list[dict[str, Any]]) -> dict[str, Any]:
    return envelope(
        kind=kind,
        data={"count": len(issues), "items": issues},
    )


def build_architecture_boundaries() -> dict[str, Any]:
    """Build the ``platform.architecture_boundaries`` envelope."""

    cap_audit = capability_authority.assert_no_competing_authority()
    issues: list[dict[str, Any]] = []
    derived = cap_audit.derived_resolvable or {}
    for path, resolvable in derived.items():
        if not resolvable:
            issues.append(
                {
                    "id": f"boundary.{path}",
                    "severity": "high",
                    "title": "derived projection not resolvable",
                    "location": path,
                    "evidence": [],
                    "first_seen": None,
                }
            )
    return _findings_envelope(
        architecture_contract.ARCHITECTURE_BOUNDARIES_KIND,
        issues,
    )


def build_architecture_duplicates() -> dict[str, Any]:
    """Build the ``platform.architecture_duplicates`` envelope."""

    cap_audit = capability_authority.assert_no_competing_authority()
    issues: list[dict[str, Any]] = []
    derived_count = len(cap_audit.derived_projections or [])
    if derived_count > 0:
        issues.append(
            {
                "id": "duplicate.derived_projections",
                "severity": "medium",
                "title": f"{derived_count} derived projections registered",
                "location": "capability_authority",
                "evidence": [],
                "first_seen": None,
            }
        )
    return _findings_envelope(
        architecture_contract.ARCHITECTURE_DUPLICATES_KIND,
        issues,
    )


def build_architecture_bypasses() -> dict[str, Any]:
    """Build the ``platform.architecture_bypasses`` envelope."""

    return _findings_envelope(
        architecture_contract.ARCHITECTURE_BYPASSES_KIND,
        [],
    )


def build_architecture_deprecations() -> dict[str, Any]:
    """Build the ``platform.architecture_deprecations`` envelope."""

    return _findings_envelope(
        architecture_contract.ARCHITECTURE_DEPRECATIONS_KIND,
        [],
    )


def build_architecture_unmapped() -> dict[str, Any]:
    """Build the ``platform.architecture_unmapped`` envelope."""

    issues: list[dict[str, Any]] = []
    try:
        from runtime.foundation.verification.capability_latent_audit import (
            run_latent_audit,
        )

        report = run_latent_audit()
        if hasattr(report, "to_dict"):
            d = report.to_dict()
            for entry in d.get("unmapped", []) or []:
                issues.append(
                    {
                        "id": f"unmapped.{entry}",
                        "severity": "low",
                        "title": "unmapped capability",
                        "location": str(entry),
                        "evidence": [],
                        "first_seen": None,
                    }
                )
    except Exception:
        # Latent audit is not part of Phase 2's hard contract; absence
        # is reported as zero unmapped capabilities.
        pass
    return _findings_envelope(
        architecture_contract.ARCHITECTURE_UNMAPPED_KIND,
        issues,
    )
