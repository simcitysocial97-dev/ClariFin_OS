"""VEA-5 M2 — Tier-aware verification planning.

Builds on the existing intelligence planner
(``analyze_changes`` -> ``compute_blast_radius`` -> ``optimize_verification``),
which already emits ``selected`` + ``skipped`` (``SkippedSuite``) units, each
with a ``reason`` and ``justification``. M2 adds an explicit **tier** that
decides the base/scope, so ``origin/main`` branch divergence can never become
the developer's change for Tier 1 (local) — for ANY amount of divergence.

Critical invariant (the whole point of M2)
------------------------------------------
A verification unit is **never silently absent** from a plan. Every unit in the
canonical catalog is present as either ``selected`` or ``excluded`` with a
machine-readable reason. This closes the structural defect proven in VEA-5 M0:
the change-scoped planner treated the entire ``origin/main`` branch divergence
(whatever its size: ~1200 raw / ~967 filtered at the M0 snapshot) as the
change, selected a maximal blast radius, and ran heavy units that failed.

Tier semantics (see ``docs/verification/VEA5_EXECUTION_MODEL.md`` §3-§6)
----------------------------------------------------------------------
* Tier 1 (LOCAL): the developer's **working-tree** delta (staged + unstaged +
  untracked). It NEVER diffs against ``origin/main``/merge-base, so branch
  divergence cannot inflate the plan.
* Tier 2 (PR): the **actual PR base/diff** (``GITHUB_BASE_REF`` or explicit
  override). Independent of how far the branch has diverged from ``origin/main``.
* Tier 3 (DEEP): **explicit full-system** execution. Not change-scoped; mutation,
  golden, E2E and performance are selected regardless of any diff.

Reused, not re-invented
-----------------------
* ``optimize_verification`` for LOCAL/PR selection + existing ``SkippedSuite``
  exclusion reasons.
* ``UNIT`` provenance (``capabilities`` / ``impact_kinds`` / ``source``) from the
  intelligence pipeline is carried onto every selected unit.
* The orchestrator's ``_filter_changed_files`` for artifact filtering.
* ``SkippedSuite`` shape (``id`` / ``category`` / ``reason`` / ``justification``)
  for excluded units.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.foundation.intelligence.platform.blast import compute_blast_radius
from runtime.foundation.intelligence.platform.change import analyze_changes
from runtime.foundation.intelligence.platform.optimizer import (
    VerificationPlanIntel,
    optimize_verification,
)
from runtime.foundation.verification.orchestrator import _filter_changed_files

PLANNER_VERSION = "vea5-m2-tier-planner/1.0"
FRAMEWORK_VERSION = "clari-fin-os/verify-runtime"
MANIFEST_PATH = Path("runtime/generated/vea5-tier-plan.json")


class VerificationTier(str, Enum):
    """The three VEA-5 verification tiers."""

    LOCAL = "local"  # Tier 1 — developer working tree
    PR = "pr"  # Tier 2 — pull request gate
    DEEP = "deep"  # Tier 3 — full-system scheduled / release


# ---------------------------------------------------------------------------
# Canonical verification-unit catalog.
#
# Single source of truth for the completeness invariant: every unit below MUST
# appear in a TierPlan as either selected or excluded. Ids / categories / cost
# mirror runtime/foundation/intelligence/platform/optimizer.py so the catalog
# and the intelligence planner agree on the unit universe.
# ---------------------------------------------------------------------------
UNIT_CATALOG: tuple[dict[str, Any], ...] = (
    {"id": "unit-targeted", "category": "unit", "estimated_seconds": 30},
    {"id": "backend-unit", "category": "unit", "estimated_seconds": 120},
    {"id": "backend-integration", "category": "integration", "estimated_seconds": 180},
    {"id": "contracts-schemathesis", "category": "contract", "estimated_seconds": 180},
    {"id": "frontend-unit", "category": "frontend", "estimated_seconds": 120},
    {"id": "frontend-typecheck-build", "category": "frontend", "estimated_seconds": 90},
    {"id": "playwright-e2e", "category": "e2e", "estimated_seconds": 1800},
    {"id": "runtime-self-test", "category": "runtime", "estimated_seconds": 120},
    {"id": "mutation-run", "category": "mutation", "estimated_seconds": 600},
    {"id": "golden-regression", "category": "golden", "estimated_seconds": 600},
)
CATALOG_IDS = tuple(u["id"] for u in UNIT_CATALOG)
CATALOG_BY_ID = {u["id"]: u for u in UNIT_CATALOG}


@dataclass(frozen=True, slots=True)
class SelectedUnit:
    """A verification unit that the tier planner selected to run."""

    unit_id: str
    category: str
    command: str
    reason: str
    estimated_seconds: int
    capabilities: tuple[str, ...] = ()
    impact_kinds: tuple[str, ...] = ()
    source: str = "tier-eligibility"
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExcludedUnit:
    """A verification unit the tier planner deliberately did NOT run.

    ``reason`` + ``justification`` are mandatory (the M2 no-silent-absence
    contract). This is the ``SkippedSuite`` shape from the intelligence planner.
    """

    unit_id: str
    category: str
    reason: str
    justification: str
    estimated_seconds: int = 0


@dataclass(frozen=True, slots=True)
class TierPlan:
    """A complete, machine-readable verification plan for one tier."""

    tier: str
    base_ref: str | None
    head_ref: str
    changed_files: tuple[str, ...]
    selected: tuple[SelectedUnit, ...]
    excluded: tuple[ExcludedUnit, ...]
    estimated_seconds: int
    planner_version: str
    framework_version: str
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # --- determinism helpers (timestamps excluded) -------------------------
    def fingerprint(self) -> dict[str, Any]:
        """Structural identity, ignoring ``generated_at``.

        Two plans are deterministically equal iff their fingerprints are equal.
        """
        return {
            "tier": self.tier,
            "base_ref": self.base_ref,
            "head_ref": self.head_ref,
            "changed_files": sorted(self.changed_files),
            "selected": [
                s.unit_id for s in sorted(self.selected, key=lambda s: s.unit_id)
            ],
            "excluded": [
                e.unit_id for e in sorted(self.excluded, key=lambda e: e.unit_id)
            ],
            "estimated_seconds": self.estimated_seconds,
        }

    def all_unit_ids(self) -> set[str]:
        return {s.unit_id for s in self.selected} | {e.unit_id for e in self.excluded}

    def is_complete(self) -> bool:
        """True iff every catalog unit is present (selected or excluded)."""
        return sorted(self.all_unit_ids()) == sorted(CATALOG_IDS)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "vea5-tier-plan/v1",
            "tier": self.tier,
            "base_ref": self.base_ref,
            "head_ref": self.head_ref,
            "changed_files": list(self.changed_files),
            "selected": [asdict(s) for s in self.selected],
            "excluded": [asdict(e) for e in self.excluded],
            "estimated_seconds": self.estimated_seconds,
            "planner_version": self.planner_version,
            "framework_version": self.framework_version,
            "generated_at": self.generated_at,
            "invariant": "every catalog unit is selected or excluded",
            "unit_coverage": {
                "catalog_size": len(CATALOG_IDS),
                "covered": len(self.all_unit_ids()),
                "complete": self.is_complete(),
            },
        }

    def write(self, path: Path | None = None) -> Path:
        """Persist the manifest so evidence is inspectable after execution."""
        p = Path(path) if path is not None else MANIFEST_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")
        return p


# ---------------------------------------------------------------------------
# Tier-aware base / changed-file resolution.
# ---------------------------------------------------------------------------


def _repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return Path(repo_root)
    from runtime.foundation.verification.orchestrator import _find_repo_root

    return _find_repo_root()


def resolve_base_ref_for_tier(
    tier: VerificationTier,
    *,
    explicit_base: str | None = None,
    pr_base: str | None = None,
) -> str | None:
    """Return the git ref the tier diffs against.

    LOCAL returns ``None`` (working-tree scope) and **never** consults
    ``origin/main``/merge-base — this is what decouples branch divergence from
    the developer's change, regardless of how many files have diverged.

    PR returns the PR base (``GITHUB_BASE_REF``) or an explicit override.

    DEEP returns ``None`` (not change-scoped).
    """
    if tier is VerificationTier.LOCAL:
        return None
    if tier is VerificationTier.DEEP:
        return None
    return explicit_base or pr_base


def _run_git(args: list[str], repo_root: Path) -> str:
    try:
        r = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=10,
        )
    except Exception:
        return ""
    return r.stdout if r.returncode == 0 else ""


def collect_working_tree_changes(repo_root: Path) -> list[str]:
    """Tier 1 change set: staged + unstaged + untracked vs HEAD.

    Deliberately uses the working tree (``HEAD``), NEVER merge-base vs
    ``origin/main``. This is the fix for the M0 branch-divergence
    over-selection (any number of divergent files is ignored).
    """
    diff_head = _run_git(["diff", "--name-only", "HEAD"], repo_root)
    diff_cached = _run_git(["diff", "--cached", "--name-only", "HEAD"], repo_root)
    untracked = _run_git(["ls-files", "--others", "--exclude-standard"], repo_root)
    files = [
        *diff_head.splitlines(),
        *diff_cached.splitlines(),
        *untracked.splitlines(),
    ]
    return _filter_changed_files([f.strip() for f in files if f.strip()])


def collect_pr_changes(repo_root: Path, base_ref: str | None) -> list[str]:
    """Tier 2 change set: the PR diff vs its base, plus untracked files."""
    if base_ref is None:
        return []
    diff = _run_git(["diff", "--name-only", base_ref], repo_root)
    untracked = _run_git(["ls-files", "--others", "--exclude-standard"], repo_root)
    files = [*diff.splitlines(), *untracked.splitlines()]
    return _filter_changed_files([f.strip() for f in files if f.strip()])


def collect_changed_files_for_tier(
    tier: VerificationTier,
    *,
    changed_files: list[str] | None = None,
    explicit_base: str | None = None,
    pr_base: str | None = None,
    repo_root: Path | None = None,
) -> list[str]:
    """Resolve the changed-file set for a tier.

    ``changed_files`` may be injected (tests / CI overrides) to bypass git.
    """
    if changed_files is not None:
        return list(changed_files)
    root = _repo_root(repo_root)
    if tier is VerificationTier.LOCAL:
        return collect_working_tree_changes(root)
    if tier is VerificationTier.PR:
        base = resolve_base_ref_for_tier(
            tier, explicit_base=explicit_base, pr_base=pr_base
        )
        return collect_pr_changes(root, base)
    return []  # DEEP: no change scope


def _head_ref(repo_root: Path) -> str:
    out = _run_git(["rev-parse", "HEAD"], repo_root)
    return out.strip() or "unknown"


# ---------------------------------------------------------------------------
# Plan construction.
# ---------------------------------------------------------------------------


def _finalize(
    tier: VerificationTier,
    base_ref: str | None,
    head: str,
    changed: tuple[str, ...],
    selected: list[SelectedUnit],
    excluded: list[ExcludedUnit],
) -> TierPlan:
    return TierPlan(
        tier=tier.value,
        base_ref=base_ref,
        head_ref=head,
        changed_files=changed,
        selected=tuple(selected),
        excluded=tuple(excluded),
        estimated_seconds=sum(s.estimated_seconds for s in selected),
        planner_version=PLANNER_VERSION,
        framework_version=FRAMEWORK_VERSION,
    )


def _deep_plan(head: str) -> TierPlan:
    """Tier 3 — full-system. Every catalog unit is selected; nothing is
    filtered by change scope."""
    selected: list[SelectedUnit] = []
    for unit in UNIT_CATALOG:
        selected.append(
            SelectedUnit(
                unit_id=unit["id"],
                category=unit["category"],
                command=f"verify-unit:{unit['id']}",
                reason="deep tier: full-system verification (not change-scoped)",
                estimated_seconds=unit["estimated_seconds"],
                impact_kinds=(),
                source="deep-full-system",
            )
        )
    return _finalize(VerificationTier.DEEP, None, head, (), selected, [])


def _intel_plan(
    tier: VerificationTier,
    base_ref: str | None,
    head: str,
    changed: list[str],
) -> TierPlan:
    """Tier 1 / Tier 2 — blast-radius-driven selection via the existing
    intelligence planner, reconciled against the catalog for completeness."""
    change = analyze_changes(paths=changed)
    blast = compute_blast_radius(change)
    intel: VerificationPlanIntel = optimize_verification(blast)

    sel_by_id = {u.id: u for u in intel.selected}
    skip_by_id = {s.id: s for s in intel.skipped}

    # Tier-2 selective mutation eligibility (VEA-5 M1 §8 policy matrix):
    # a critical logic change in a backend engine makes mutation-run SELECTED
    # (targeted) for PR only — local keeps the cost gate.
    mutation_selected = tier is VerificationTier.PR and any(
        f.startswith("backend/src/engines/") for f in changed
    )

    selected: list[SelectedUnit] = []
    excluded: list[ExcludedUnit] = []

    for unit in UNIT_CATALOG:
        uid = unit["id"]
        if uid in sel_by_id:
            u = sel_by_id[uid]
            selected.append(
                SelectedUnit(
                    unit_id=u.id,
                    category=u.category,
                    command=u.command,
                    reason=u.reason,
                    estimated_seconds=u.estimated_seconds,
                    capabilities=tuple(u.capabilities),
                    impact_kinds=tuple(u.impact_kinds),
                    source=u.source,
                    evidence=tuple(u.evidence),
                )
            )
        elif uid == "mutation-run" and mutation_selected:
            selected.append(
                SelectedUnit(
                    unit_id="mutation-run",
                    category="mutation",
                    command="bash .github/scripts/run_mutation_selective.sh",
                    reason=(
                        "PR tier: critical logic change in backend engine "
                        "→ targeted mutation eligible"
                    ),
                    estimated_seconds=unit["estimated_seconds"],
                    impact_kinds=("engine",),
                    source="tier-eligibility",
                )
            )
        elif uid in skip_by_id:
            s = skip_by_id[uid]
            excluded.append(
                ExcludedUnit(
                    unit_id=s.id,
                    category=s.category,
                    reason=s.reason,
                    justification=s.justification,
                    estimated_seconds=unit["estimated_seconds"],
                )
            )
        else:
            # Safety net — catalog unit not produced by the optimizer. Never
            # silently drop: record it as explicitly excluded with a reason.
            excluded.append(
                ExcludedUnit(
                    unit_id=uid,
                    category=unit["category"],
                    reason="not selected by blast-radius planner",
                    justification=(
                        "no blast-radius evidence selected this unit; "
                        "excluded by default with a reason"
                    ),
                    estimated_seconds=unit["estimated_seconds"],
                )
            )

    return _finalize(tier, base_ref, head, tuple(changed), selected, excluded)


def plan_for_tier(
    tier: VerificationTier | str,
    *,
    changed_files: list[str] | None = None,
    explicit_base: str | None = None,
    pr_base: str | None = None,
    repo_root: Path | None = None,
    head_ref: str | None = None,
) -> TierPlan:
    """Produce a complete TierPlan for the given tier.

    Parameters
    ----------
    tier:
        ``"local"`` / ``"pr"`` / ``"deep"`` (or a ``VerificationTier``).
    changed_files:
        Optional explicit change set. When provided, git is bypassed (used by
        CI overrides and by tests). For DEEP this is ignored.
    explicit_base / pr_base:
        Override the PR base ref. ``pr_base`` mirrors ``GITHUB_BASE_REF``.
    repo_root / head_ref:
        Overrides for testing / non-CWD execution.
    """
    if isinstance(tier, str):
        tier = VerificationTier(tier)

    root = _repo_root(repo_root)
    base_ref = resolve_base_ref_for_tier(
        tier, explicit_base=explicit_base, pr_base=pr_base
    )
    head = head_ref or _head_ref(root)

    if tier is VerificationTier.DEEP:
        return _deep_plan(head)

    changed = collect_changed_files_for_tier(
        tier,
        changed_files=changed_files,
        explicit_base=explicit_base,
        pr_base=pr_base,
        repo_root=root,
    )
    return _intel_plan(tier, base_ref, head, changed)


__all__ = [
    "VerificationTier",
    "SelectedUnit",
    "ExcludedUnit",
    "TierPlan",
    "UNIT_CATALOG",
    "CATALOG_IDS",
    "resolve_base_ref_for_tier",
    "collect_working_tree_changes",
    "collect_pr_changes",
    "collect_changed_files_for_tier",
    "plan_for_tier",
]
