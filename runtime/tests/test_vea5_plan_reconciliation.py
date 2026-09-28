"""VEA-5 M4 — Plan Reconciliation acceptance & regression tests.

Guards the M4 invariant: equivalent normalized inputs + equivalent tier policy
=> deterministic equivalent plans (fingerprint-stable); any divergence between
two plans must be *explainable* by exactly one classified cause.

Run:
    python3 -m pytest runtime/tests/test_vea5_plan_reconciliation.py -q
"""

from __future__ import annotations

from runtime.foundation.verification.reconciliation import (
    POLICY_VERSION,
    ReconciliationStatus,
    UnitExecution,
    build_evidence_identity,
    change_set_diff,
    change_set_fingerprint,
    normalize_change_set,
    plan_fingerprint,
    reconcile,
)
from runtime.foundation.verification.tier import (
    TierPlan,
    plan_for_tier,
)

ENGINE_CHANGE = [
    "backend/src/engines/loan_engine/amortization.py",
    "backend/src/engines/loan_engine/floating_rate.py",
]


# ---------------------------------------------------------------------------
# Change-set normalization + fingerprint determinism.
# ---------------------------------------------------------------------------


def test_normalize_change_set_is_order_and_dup_insensitive():
    a = ["backend/a.py", "frontend/b.ts"]
    b = ["frontend/b.ts", "backend/a.py", "backend/a.py"]
    assert normalize_change_set(a) == normalize_change_set(b)
    assert normalize_change_set(a) == ("backend/a.py", "frontend/b.ts")


def test_change_set_fingerprint_deterministic():
    fp1 = change_set_fingerprint(ENGINE_CHANGE)
    fp2 = change_set_fingerprint(list(reversed(ENGINE_CHANGE)))
    fp3 = change_set_fingerprint(tuple(sorted(ENGINE_CHANGE)))
    assert fp1 == fp2 == fp3
    assert len(fp1) == 12


def test_change_set_diff_symdiff():
    only_a, only_b = change_set_diff(["a.py", "b.py"], ["b.py", "c.py"])
    assert only_a == ("a.py",)
    assert only_b == ("c.py",)


# ---------------------------------------------------------------------------
# Plan fingerprint determinism.
# ---------------------------------------------------------------------------


def test_plan_fingerprint_deterministic_for_same_inputs():
    p1 = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    p2 = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    assert plan_fingerprint(p1).digest() == plan_fingerprint(p2).digest()


def test_plan_fingerprint_ignores_base_ref_when_change_set_equal():
    """A change-set-equal plan must fingerprint identically regardless of an
    unrelated base ref the tier ignored (the M2 LOCAL guarantee carried into
    reconciliation)."""
    p1 = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    p2 = plan_for_tier(
        "local", changed_files=ENGINE_CHANGE, explicit_base="origin/main"
    )
    assert plan_fingerprint(p1).digest() == plan_fingerprint(p2).digest()


def test_plan_fingerprint_differs_on_changed_files():
    a = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    b = plan_for_tier("local", changed_files=["frontend/src/App.tsx"])
    assert plan_fingerprint(a).digest() != plan_fingerprint(b).digest()


# ---------------------------------------------------------------------------
# Reconciliation classifications.
# ---------------------------------------------------------------------------


def test_reconcile_same_plan():
    local = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    ci = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    report = reconcile(local, ci)
    assert report.classification.status == ReconciliationStatus.SAME_PLAN.value
    assert report.classification.planning_diverges is False
    assert report.classification.tier_differs is False


def test_reconcile_expected_tier_difference():
    """Local vs PR for an engine change: PR selects mutation-run, local keeps
    it excluded. This is EXPECTED_TIER_DIFFERENCE, NOT planning divergence."""
    local = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    ci = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")
    report = reconcile(local, ci)
    assert (
        report.classification.status
        == ReconciliationStatus.EXPECTED_TIER_DIFFERENCE.value
    )
    assert report.classification.tier_differs is True
    assert report.classification.planning_diverges is False
    assert "mutation-run" in report.classification.diverging_units


def test_reconcile_environment_divergence():
    """Same plan, but recorded execution/evidence differs -> environment."""
    local = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    ci = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    local_res = {
        "backend-unit": UnitExecution("backend-unit", "pass", 0),
    }
    ci_res = {
        "backend-unit": UnitExecution("backend-unit", "fail", 1),
    }
    report = reconcile(local, ci, local_results=local_res, ci_results=ci_res)
    assert (
        report.classification.status
        == ReconciliationStatus.ENVIRONMENT_DIVERGENCE.value
    )
    assert report.classification.environment_diverges is True
    assert report.classification.planning_diverges is False


def test_reconcile_planning_divergence_on_changed_files():
    """Different change sets (not just tier) -> planning divergence, because the
    difference is not explainable by tier policy alone."""
    local = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    ci = plan_for_tier("local", changed_files=["frontend/src/App.tsx"])
    report = reconcile(local, ci)
    assert (
        report.classification.status == ReconciliationStatus.PLANNING_DIVERGENCE.value
    )
    assert report.classification.planning_diverges is True


def test_reconcile_planning_divergence_unexplained_unit_change():
    """If a non-tier-eligible unit differs between tiers, that is planning
    divergence (a real defect to investigate), not expected tier difference."""
    local = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    # Simulate a CI plan where a unit outside the tier-eligible set was dropped.
    ci = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")
    # Remove a non-eligible unit from CI selected/excluded to force divergence.
    mutated = TierPlan(
        tier=ci.tier,
        base_ref=ci.base_ref,
        head_ref=ci.head_ref,
        changed_files=ci.changed_files,
        selected=tuple(s for s in ci.selected if s.unit_id != "backend-unit"),
        excluded=tuple(
            list(ci.excluded)
            + [
                type(ci.excluded[0])(
                    unit_id="backend-unit",
                    category="unit",
                    reason="simulated-unexplained-drop",
                    justification="test",
                    estimated_seconds=120,
                )
            ]
        ),
        estimated_seconds=ci.estimated_seconds,
        planner_version=ci.planner_version,
        framework_version=ci.framework_version,
    )
    report = reconcile(local, mutated)
    assert (
        report.classification.status == ReconciliationStatus.PLANNING_DIVERGENCE.value
    )
    assert "backend-unit" in report.classification.diverging_units


# ---------------------------------------------------------------------------
# Base-resolution invariant for reconciliation inputs.
# ---------------------------------------------------------------------------


def test_base_resolution_invariance_for_tier1_reconciliation():
    """Repository A (10 relevant files) must reconcile as SAME_PLAN against
    Repository B (same HEAD, origin/main diverged) because LOCAL ignores the
    diverged base entirely."""
    repo_a_files = [
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
    a = plan_for_tier("local", changed_files=repo_a_files)
    b = plan_for_tier(
        "local",
        changed_files=repo_a_files,
        explicit_base="origin/main",
        pr_base="origin/main",
    )
    report = reconcile(a, b)
    assert report.classification.status == ReconciliationStatus.SAME_PLAN.value
    assert report.local_fingerprint.digest() == report.ci_fingerprint.digest()


# ---------------------------------------------------------------------------
# Evidence identity spine.
# ---------------------------------------------------------------------------


def test_build_evidence_identity_spine():
    identity = build_evidence_identity(
        commit="abc123",
        change_set=change_set_fingerprint(ENGINE_CHANGE),
        tier="local",
        plan_digest="deadbeef" * 2,
        unit_executions=[
            UnitExecution("backend-unit", "pass", 0, "ev/backend.json"),
            UnitExecution("mutation-run", "skipped", None, None),
        ],
    )
    assert identity["commit"] == "abc123"
    assert identity["tier"] == "local"
    assert identity["plan_fingerprint"] == "deadbeef" * 2
    assert len(identity["units"]) == 2
    assert identity["units"][0]["evidence_ref"] == "ev/backend.json"


def test_reconciliation_report_to_dict_is_machine_readable():
    local = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    ci = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")
    report = reconcile(local, ci, commit="sha")
    d = report.to_dict()
    assert d["schema"] == "vea5-reconciliation/v1"
    assert d["policy_version"] == POLICY_VERSION
    assert d["classification"]["status"] == (
        ReconciliationStatus.EXPECTED_TIER_DIFFERENCE.value
    )
    assert "digest" in d["local_fingerprint"]
    assert "digest" in d["ci_fingerprint"]
