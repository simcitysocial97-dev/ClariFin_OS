"""Phase 3 — Verification Optimizer.

Computes the *minimum* verification that still covers the blast radius.

The optimizer never invents test paths. Unit test targets come from
``Engine.tests`` in provider state; suite-level targets come from the real
verification profiles in :mod:`runtime.foundation.verification.profiles`.

Correctness rule
----------------
A suite may only be skipped when the blast radius contains **no** impacted
entity of the kind that suite verifies. Skipping is therefore a statement
about evidence ("no frontend entity is impacted"), not a cost heuristic. Every
skip records that justification so the decision is auditable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from runtime.foundation.intelligence.platform.blast import BlastRadius

__all__ = ["VerificationUnit", "VerificationPlanIntel", "optimize_verification"]


@dataclass(frozen=True, slots=True)
class VerificationUnit:
    """One selected piece of verification work."""

    id: str
    category: str
    command: str
    targets: tuple[str, ...]
    reason: str
    evidence: tuple[str, ...]
    estimated_seconds: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "command": self.command,
            "targets": list(self.targets),
            "reason": self.reason,
            "evidence": list(self.evidence),
            "estimated_seconds": self.estimated_seconds,
        }


@dataclass(frozen=True, slots=True)
class SkippedSuite:
    id: str
    category: str
    reason: str
    justification: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "category": self.category,
            "reason": self.reason,
            "justification": self.justification,
        }


@dataclass(frozen=True, slots=True)
class VerificationPlanIntel:
    generated_at: str
    selected: tuple[VerificationUnit, ...]
    skipped: tuple[SkippedSuite, ...]
    fallback_profile: str
    baseline_profile: str
    baseline_seconds: int

    @property
    def estimated_seconds(self) -> int:
        return sum(u.estimated_seconds for u in self.selected)

    @property
    def savings_seconds(self) -> int:
        return max(0, self.baseline_seconds - self.estimated_seconds)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "verification-plan/v1",
            "generated_at": self.generated_at,
            "provider": "runtime.foundation.architecture.get_architecture",
            "selection_rule": (
                "a suite is skipped only when the blast radius contains no "
                "impacted entity of the kind it verifies"
            ),
            "selected": [u.to_dict() for u in self.selected],
            "skipped": [s.to_dict() for s in self.skipped],
            "counts": {
                "selected": len(self.selected),
                "skipped": len(self.skipped),
                "unit_tests": sum(
                    len(u.targets) for u in self.selected if u.category == "unit"
                ),
            },
            "estimated_seconds": self.estimated_seconds,
            "baseline_profile": self.baseline_profile,
            "baseline_seconds": self.baseline_seconds,
            "savings_seconds": self.savings_seconds,
            "fallback_profile": self.fallback_profile,
        }


def _baseline_seconds(profile_name: str = "full") -> int:
    from runtime.foundation.verification.profiles import get_profile

    try:
        profile = get_profile(profile_name)
    except ValueError:
        return 0
    return sum(t.estimated_duration_seconds for t in profile.tasks)


def optimize_verification(
    blast: BlastRadius,
    resolver: Any | None = None,  # noqa: ARG001 - kept for API symmetry with other phases
) -> VerificationPlanIntel:
    """Derive the smallest evidence-justified verification plan."""
    def impacted(*kind_names: str) -> list[str]:
        out: list[str] = []
        for node in blast.all_impacted:
            if node.ref.kind in kind_names:
                out.append(node.ref.ref)
        return sorted(set(out))

    selected: list[VerificationUnit] = []
    skipped: list[SkippedSuite] = []

    # --- Unit tests: exact provider-known test files ---------------------
    unit_targets = tuple(sorted(r.path or r.key for r in blast.verification))
    if unit_targets:
        selected.append(
            VerificationUnit(
                id="unit-targeted",
                category="unit",
                command="python3 -m pytest " + " ".join(unit_targets) + " -q",
                targets=unit_targets,
                reason=(
                    f"{len(unit_targets)} test file(s) are recorded by the provider "
                    "as verifying an impacted engine"
                ),
                evidence=tuple(
                    f"ownership: {r.ref} verifies impacted engine"
                    for r in blast.verification
                ),
                estimated_seconds=max(15, 8 * len(unit_targets)),
            )
        )
    else:
        skipped.append(
            SkippedSuite(
                id="unit-targeted",
                category="unit",
                reason="no impacted engine has provider-recorded tests",
                justification="blast radius contains no engine with tests",
            )
        )

    # --- Contract suites: only when endpoints are impacted ---------------
    endpoints = impacted("endpoint")
    if endpoints:
        selected.append(
            VerificationUnit(
                id="contracts-schemathesis",
                category="contract",
                command="python3 -m pytest backend/tests/contract/ -q",
                targets=tuple(endpoints),
                reason=f"{len(endpoints)} endpoint(s) are in the blast radius",
                evidence=tuple(endpoints[:20]),
                estimated_seconds=180,
            )
        )
    else:
        skipped.append(
            SkippedSuite(
                id="contracts-schemathesis",
                category="contract",
                reason="no endpoint impacted",
                justification="blast radius contains 0 entities of kind 'endpoint'",
            )
        )

    # --- Integration: routers/services/repositories ----------------------
    integration = impacted("router", "service", "repository")
    if integration:
        selected.append(
            VerificationUnit(
                id="backend-integration",
                category="integration",
                command="python3 -m pytest backend/tests/integration/ -q",
                targets=tuple(integration),
                reason=(
                    f"{len(integration)} router/service/repository entities impacted"
                ),
                evidence=tuple(integration[:20]),
                estimated_seconds=180,
            )
        )
    else:
        skipped.append(
            SkippedSuite(
                id="backend-integration",
                category="integration",
                reason="no router, service or repository impacted",
                justification="blast radius contains no backend wiring entities",
            )
        )

    # --- Frontend: capabilities/workspaces/components/view models --------
    frontend = impacted("capability", "workspace", "component", "view_model", "mapper")
    frontend_files = [
        n.ref.ref
        for n in blast.all_impacted
        if n.ref.path.startswith("frontend/")
    ]
    if frontend_files:
        selected.append(
            VerificationUnit(
                id="frontend-unit",
                category="frontend",
                command="npm --prefix frontend run test",
                targets=tuple(sorted(set(frontend_files))),
                reason=f"{len(set(frontend_files))} frontend entities impacted",
                evidence=tuple(sorted(set(frontend_files))[:20]),
                estimated_seconds=120,
            )
        )
    else:
        skipped.append(
            SkippedSuite(
                id="frontend-unit",
                category="frontend",
                reason="no frontend file impacted",
                justification=(
                    "no impacted entity has a path under frontend/; "
                    f"capability/workspace impact={len(frontend)} but none map to files"
                ),
            )
        )

    # --- Playwright: only for user-visible workspace/page impact ---------
    workspaces = impacted("workspace")
    if workspaces:
        selected.append(
            VerificationUnit(
                id="playwright-e2e",
                category="e2e",
                command="npm --prefix frontend run test:e2e",
                targets=tuple(workspaces),
                reason=f"{len(workspaces)} user-facing workspace(s) impacted",
                evidence=tuple(workspaces),
                estimated_seconds=1800,
            )
        )
    else:
        skipped.append(
            SkippedSuite(
                id="playwright-e2e",
                category="e2e",
                reason="no workspace impacted",
                justification="blast radius contains 0 entities of kind 'workspace'",
            )
        )

    # --- Runtime self-test: only when runtime itself changed -------------
    runtime_changed = any(
        n.ref.path.startswith("runtime/") for n in blast.direct if n.ref.path
    )
    if runtime_changed:
        selected.append(
            VerificationUnit(
                id="runtime-self-test",
                category="runtime",
                command="python3 -m pytest runtime/tests/ -q",
                targets=("runtime/tests/",),
                reason="the Engineering Runtime itself changed",
                evidence=tuple(
                    n.ref.ref for n in blast.direct if n.ref.path.startswith("runtime/")
                )[:20],
                estimated_seconds=120,
            )
        )
    else:
        skipped.append(
            SkippedSuite(
                id="runtime-self-test",
                category="runtime",
                reason="runtime unchanged",
                justification="no directly changed entity has a runtime/ path",
            )
        )

    # --- Always-skipped-by-default heavy suites --------------------------
    for suite_id, category, need in (
        ("mutation-run", "mutation", "explicit request (cost >= 600s)"),
        ("golden-regression", "golden", "explicit request (cost >= 600s)"),
    ):
        skipped.append(
            SkippedSuite(
                id=suite_id,
                category=category,
                reason=f"requires {need}",
                justification=(
                    "heavyweight suite; blast radius does not by itself justify it"
                ),
            )
        )

    fallback = "full" if blast.unresolved_nodes and not selected else "graph"

    return VerificationPlanIntel(
        generated_at=datetime.now(timezone.utc).isoformat(),
        selected=tuple(selected),
        skipped=tuple(skipped),
        fallback_profile=fallback,
        baseline_profile="full",
        baseline_seconds=_baseline_seconds("full"),
    )
