"""VEA-5 M2 — Tier-aware planning acceptance & regression tests.

These tests guard the architectural invariant proven broken in VEA-5 M0: the
change-scoped planner treated the large ``origin/main`` branch divergence as
the developer's change. The historical branch diverged by ~1200 raw files
(filtered ~967 at the M0 snapshot; the exact count is snapshot-dependent and
NOT part of the invariant). M2 makes the TIER decide the base/scope, so LOCAL
is invariant to ARBITRARY branch divergence.

Run:
    python3 -m pytest runtime/tests/test_vea5_tier_plan.py -q
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from runtime.foundation.verification.tier import (
    CATALOG_IDS,
    ExcludedUnit,
    SelectedUnit,
    TierPlan,
    VerificationTier,
    collect_changed_files_for_tier,
    plan_for_tier,
    resolve_base_ref_for_tier,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

# A realistic backend engine change (mirrors the VEA-2 Phase 1.5 specimen).
ENGINE_CHANGE = [
    "backend/src/engines/loan_engine/amortization.py",
    "backend/src/engines/loan_engine/floating_rate.py",
]

# 10 "relevant" files for Repository A.
REPO_A_FILES = [
    "backend/src/engines/loan_engine/amortization.py",
    "backend/src/engines/loan_engine/floating_rate.py",
    "backend/src/routers/loans.py",
    "backend/tests/unit/engines/test_loan_amortization.py",
    "backend/tests/contract/test_loans_contract.py",
    "frontend/lib/capabilities/useLoansCapability.ts",
    "frontend/lib/mappers/loans-mapper.ts",
    "frontend/src/components/LoanSummary.tsx",
    "backend/src/services/loan_service.py",
    "runtime/foundation/intelligence/platform/optimizer.py",
]


# ---------------------------------------------------------------------------
# Tier 1 — LOCAL (working tree, decoupled from origin/main)
# ---------------------------------------------------------------------------


def test_local_resolves_no_base_and_ignores_branch_divergence():
    """The core M2 fix: LOCAL never consults origin/main / merge-base."""
    assert resolve_base_ref_for_tier(VerificationTier.LOCAL) is None
    # Even an explicit / PR base must be ignored for LOCAL.
    assert (
        resolve_base_ref_for_tier(
            VerificationTier.LOCAL, explicit_base="origin/main", pr_base="origin/main"
        )
        is None
    )


def test_local_never_invokes_merge_base_with_origin_main():
    """Prove the LOCAL-vs-CI divergence trap is closed: LOCAL collection must not
    run `git merge-base` or diff against origin/main (regardless of how many
    unrelated files the branch diverged by)."""

    recorded = []

    def fake_run(cmd, *args, **kwargs):
        recorded.append(list(cmd))

        class _R:
            returncode = 0
            stdout = ""
            stderr = ""

        return _R()

    with mock.patch(
        "runtime.foundation.verification.tier.subprocess.run", side_effect=fake_run
    ):
        files = collect_changed_files_for_tier(VerificationTier.LOCAL)

    assert files == []
    for cmd in recorded:
        assert cmd[0] == "git"
        assert "merge-base" not in cmd
        assert not any("origin/main" in str(c) for c in cmd)
        assert not any("origin/develop" in str(c) for c in cmd)


def test_local_working_tree_change_produces_nonzero_accurate_set():
    plan = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    assert len(plan.changed_files) == len(ENGINE_CHANGE)
    assert plan.tier == "local"
    # A backend engine change must select backend-unit at minimum.
    assert any(s.unit_id == "backend-unit" for s in plan.selected)
    # Completeness invariant holds.
    assert plan.is_complete()


def test_local_clean_working_tree_has_defined_behavior():
    plan = plan_for_tier("local", changed_files=[])
    assert plan.tier == "local"
    # Defined behavior: every unit accounted for (all excluded with reasons).
    assert plan.is_complete()
    assert len(plan.excluded) == len(CATALOG_IDS)
    assert len(plan.selected) == 0
    # Every excluded unit carries a reason + justification (no silent absence).
    for ex in plan.excluded:
        assert ex.reason and ex.justification


def test_local_heavy_units_not_selected_merely_because_branch_is_long_lived():
    plan = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    # mutation / golden remain excluded under the cost gate for LOCAL.
    assert not any(s.unit_id == "mutation-run" for s in plan.selected)
    assert not any(s.unit_id == "golden-regression" for s in plan.selected)
    mutation = next(e for e in plan.excluded if e.unit_id == "mutation-run")
    assert mutation.reason  # excluded WITH a reason


# ---------------------------------------------------------------------------
# The critical regression test: Repository A vs B
# ---------------------------------------------------------------------------


def test_repository_a_equals_repository_b_for_tier1():
    """Repository A: HEAD differs from base by 10 relevant files.
    Repository B: SAME HEAD, but origin/main diverged by many unrelated files
    (the historical branch carried ~1200 raw / ~967 filtered at the M0 snapshot;
    the exact count is snapshot-dependent and NOT part of the invariant).

    Tier 1 plan(A) MUST equal Tier 1 plan(B). Branch divergence is branch
    topology, not the developer's change, and must never enter the plan —
    for ANY amount of divergence.
    """
    # Repository A — only the 10 relevant files are the change.
    plan_a = plan_for_tier("local", changed_files=REPO_A_FILES)

    # Repository B — same relevant change; the unrelated diverged files
    # are NOT passed as changed_files for LOCAL (they live in branch history,
    # not the working tree). Passing an explicit base that "diverged" must be
    # ignored by LOCAL.
    plan_b = plan_for_tier(
        "local",
        changed_files=REPO_A_FILES,
        explicit_base="origin/main",  # B's diverged base — ignored by LOCAL
        pr_base="origin/main",
    )

    assert plan_a.fingerprint() == plan_b.fingerprint()
    assert plan_b.base_ref is None  # LOCAL never adopted the diverged base
    assert plan_a.is_complete() and plan_b.is_complete()


# ---------------------------------------------------------------------------
# Tier 2 — PR (PR base, may differ from Tier 1)
# ---------------------------------------------------------------------------


def test_pr_base_is_explicitly_resolved():
    assert resolve_base_ref_for_tier(VerificationTier.PR, pr_base="main") == "main"
    assert (
        resolve_base_ref_for_tier(VerificationTier.PR, explicit_base="develop")
        == "develop"
    )


def test_pr_plan_uses_pr_base_and_reproduces_deterministically():
    plan1 = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")
    plan2 = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")
    assert plan1.base_ref == "main"
    assert plan1.fingerprint() == plan2.fingerprint()
    assert plan1.is_complete()


def test_pr_selects_engine_change_units_and_mutation_selectively():
    plan = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")
    # affected/required units selected
    assert any(s.unit_id == "backend-unit" for s in plan.selected)
    # PR tier: critical logic change in engine -> targeted mutation SELECTED
    assert any(s.unit_id == "mutation-run" for s in plan.selected)
    # non-selected units still carry reason + justification
    by_id = {e.unit_id: e for e in plan.excluded}
    assert "golden-regression" in by_id
    assert by_id["golden-regression"].reason and by_id["golden-regression"].justification


def test_pr_plan_differs_from_local_for_engine_change():
    """Tier 2 != Tier 1 necessarily: PR selects targeted mutation for an engine
    change where LOCAL keeps it excluded."""
    local = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    pr = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")
    assert local.fingerprint() != pr.fingerprint()
    assert not any(s.unit_id == "mutation-run" for s in local.selected)
    assert any(s.unit_id == "mutation-run" for s in pr.selected)


# ---------------------------------------------------------------------------
# Tier 3 — DEEP (full-system, not change-scoped)
# ---------------------------------------------------------------------------


def test_deep_is_genuinely_full_system():
    plan = plan_for_tier("deep")
    assert plan.tier == "deep"
    assert plan.base_ref is None
    # Every catalog unit selected; nothing filtered by change scope.
    assert len(plan.selected) == len(CATALOG_IDS)
    assert plan.is_complete()
    ids = {s.unit_id for s in plan.selected}
    assert "mutation-run" in ids
    assert "golden-regression" in ids
    assert "playwright-e2e" in ids
    assert "runtime-self-test" in ids
    # Heavy suites are NOT accidentally filtered by an (empty) diff.
    assert len(plan.excluded) == 0


def test_deep_ignores_changed_files():
    plan = plan_for_tier("deep", changed_files=ENGINE_CHANGE)
    assert plan.changed_files == ()
    assert len(plan.selected) == len(CATALOG_IDS)


# ---------------------------------------------------------------------------
# Identity / determinism / evidence
# ---------------------------------------------------------------------------


def test_every_selected_and_excluded_unit_retains_id_and_provenance():
    plan = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")
    for s in plan.selected:
        assert s.unit_id
        assert s.source  # provenance source survives
        assert s.category
    for e in plan.excluded:
        assert e.unit_id
        assert e.reason and e.justification


def test_no_duplicate_unit_identities():
    for tier in ("local", "pr", "deep"):
        plan = (
            plan_for_tier(tier, changed_files=ENGINE_CHANGE, explicit_base="main")
            if tier != "deep"
            else plan_for_tier(tier)
        )
        ids = [s.unit_id for s in plan.selected] + [
            e.unit_id for e in plan.excluded
        ]
        assert len(ids) == len(set(ids)), f"duplicate unit ids in {tier}"
        # No positional assumptions: ids are stable strings, not step indices.
        assert not any(i.startswith("step-") for i in ids)


def test_determinism_identical_state_identical_plan():
    a = plan_for_tier("local", changed_files=REPO_A_FILES)
    b = plan_for_tier("local", changed_files=REPO_A_FILES)
    assert a.fingerprint() == b.fingerprint()


def test_manifest_records_required_fields_and_is_inspectable():
    plan = plan_for_tier("pr", changed_files=REPO_A_FILES, explicit_base="main")
    d = plan.to_dict()
    for key in (
        "tier",
        "base_ref",
        "head_ref",
        "changed_files",
        "selected",
        "excluded",
        "planner_version",
        "framework_version",
        "estimated_seconds",
    ):
        assert key in d
    assert d["unit_coverage"]["complete"] is True
    # Inspectable artifact: writing then re-reading round-trips the fingerprint.
    with TemporaryDirectory() as td:
        p = plan.write(Path(td) / "plan.json")
        data = json.loads(p.read_text())
        reloaded = TierPlan(
            tier=data["tier"],
            base_ref=data["base_ref"],
            head_ref=data["head_ref"],
            changed_files=tuple(data["changed_files"]),
            selected=tuple(SelectedUnit(**s) for s in data["selected"]),
            excluded=tuple(ExcludedUnit(**e) for e in data["excluded"]),
            estimated_seconds=data["estimated_seconds"],
            planner_version=data["planner_version"],
            framework_version=data["framework_version"],
        )
        assert reloaded.fingerprint() == plan.fingerprint()


def test_existing_optimizer_units_all_have_catalog_counterparts():
    """The catalog is the single source of truth; assert it covers exactly the
    unit ids the intelligence planner can emit (selected or skipped)."""
    from runtime.foundation.intelligence.platform.optimizer import (
        optimize_verification,
    )
    from runtime.foundation.intelligence.platform.blast import (
        compute_blast_radius,
    )
    from runtime.foundation.intelligence.platform.change import analyze_changes

    change = analyze_changes(paths=ENGINE_CHANGE)
    blast = compute_blast_radius(change)
    intel = optimize_verification(blast)
    emitted = {u.id for u in intel.selected} | {s.id for s in intel.skipped}
    # Everything the optimizer emits must be in the catalog (so it is covered).
    assert emitted <= set(CATALOG_IDS)
