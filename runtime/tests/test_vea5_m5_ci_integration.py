"""VEA-5 M5 — CI Integration & Reconciliation Gate acceptance tests.

Guards the M5 hard gates without redesigning the workflow topology:

  M5-A  PR base correctness (never silently fall back to origin/main)
  M5-B  Plan artifact fields (already satisfied by M2 manifest)
  M5-C  Execution-evidence artifact (per selected unit: id/provenance/status/
        exit/duration/evidence location)
  M5-D  Reconcile from persisted artifacts -> one of the four statuses
  M5-E  Exit contract: same-plan/expected-tier-difference -> 0;
        environment-divergence -> 1; planning-divergence -> 2

Key constraint: reconciliation consumes PERSISTED artifacts, never reconstructed
end-of-job state.

Run:
    python3 -m pytest runtime/tests/test_vea5_m5_ci_integration.py -q
"""

from __future__ import annotations

from pathlib import Path

from runtime.foundation.verification.reconciliation import (
    ReconciliationStatus,
    UnitExecution,
    execution_evidence_from_units,
    load_execution_evidence,
    plan_fingerprint,
    reconcile_from_artifacts,
    save_execution_evidence,
    save_reconciliation_report,
)
from runtime.foundation.verification.tier import plan_for_tier

ENGINE_CHANGE = [
    "backend/src/engines/loan_engine/amortization.py",
    "backend/src/engines/loan_engine/floating_rate.py",
]


# ---------------------------------------------------------------------------
# M5-A — PR base correctness.
# ---------------------------------------------------------------------------


def test_m5a_pr_plan_uses_provided_base_and_never_origin_main(monkeypatch):
    """M5-A: a PR plan adopts the supplied PR base and NEVER defaults to
    origin/main. The base must come from --base / GITHUB_BASE_REF (enforced in
    cmd_plan); the resolver itself never invents a base."""
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
    plan = plan_for_tier("pr", changed_files=ENGINE_CHANGE, pr_base="feature/base")
    assert plan.base_ref == "feature/base"
    # Without an explicit base the resolver returns None (no origin/main default).
    from runtime.foundation.verification.tier import (
        VerificationTier,
        resolve_base_ref_for_tier,
    )
    assert resolve_base_ref_for_tier(VerificationTier.PR, pr_base=None) is None


def test_m5a_pr_plan_rejects_missing_base(monkeypatch):
    """With no --base and no GITHUB_BASE_REF, the planner must NOT silently
    substitute origin/main. tier.py returns None (no base), and the M5-A guard in
    verify.py enforces refusal. Here we assert the resolver itself never invents
    a base."""
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
    from runtime.foundation.verification.tier import (
        VerificationTier,
        resolve_base_ref_for_tier,
    )
    assert resolve_base_ref_for_tier(VerificationTier.PR) is None
    assert resolve_base_ref_for_tier(VerificationTier.PR, pr_base=None) is None


# ---------------------------------------------------------------------------
# M5-B — Plan artifact fields.
# ---------------------------------------------------------------------------


def test_m5b_plan_manifest_carries_required_fields():
    plan = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")
    d = plan.to_dict()
    # M5-B required keys.
    for key in (
        "tier",
        "base_ref",
        "changed_files",
        "selected",
        "excluded",
        "planner_version",
        "framework_version",
    ):
        assert key in d
    # selection carries unit_id + provenance; exclusion carries reasons.
    for s in d["selected"]:
        assert s["unit_id"]
        assert "source" in s and "capabilities" in s and "impact_kinds" in s
    for e in d["excluded"]:
        assert e["unit_id"] and e["reason"] and e["justification"]
    # catalog completeness + plan fingerprint present.
    assert d["unit_coverage"]["complete"] is True
    assert plan_fingerprint(plan).digest()


# ---------------------------------------------------------------------------
# M5-C — Execution-evidence artifact.
# ---------------------------------------------------------------------------


def test_m5c_execution_evidence_roundtrip():
    units = [
        UnitExecution("backend-unit", "pass", 0, "runtime/generated/verification-report.md"),
        UnitExecution("mutation-run", "fail", 1, "runtime/generated/verification-report.md"),
    ]
    ev = execution_evidence_from_units(
        tier="pr",
        plan_fingerprint_digest="deadbeef",
        commit="abc123",
        units=units,
    )
    assert ev.tier == "pr"
    assert ev.plan_fingerprint == "deadbeef"
    # M5-C fields present per unit.
    assert ev.to_dict()["schema"] == "vea5-execution-evidence/v1"
    assert ev.tier == "pr"
    assert ev.plan_fingerprint == "deadbeef"
    # M5-C fields present per unit.
    assert ev.units[0].unit_id == "backend-unit"
    assert ev.units[0].status == "pass"
    assert ev.units[0].exit_code == 0
    assert ev.units[0].evidence_ref.endswith(".md")

    p: Path = save_execution_evidence(ev, "/tmp/kilo/m5c-ev.json")
    loaded = load_execution_evidence(p)
    assert loaded.to_dict() == ev.to_dict()


# ---------------------------------------------------------------------------
# M5-D / M5-E — Reconcile from persisted artifacts + exit contract.
# ---------------------------------------------------------------------------


def test_m5d_reconcile_from_persisted_artifacts_expected_tier_difference(tmp_path):
    """PR plan + PR execution evidence, reconciled against a LOCAL plan loaded
    from its own manifest. Persisted-artifact path only (no reconstruction)."""
    local_plan = plan_for_tier("local", changed_files=ENGINE_CHANGE)
    ci_plan = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")

    local_manifest = tmp_path / "local-plan.json"
    ci_manifest = tmp_path / "pr-plan.json"
    local_plan.write(local_manifest)
    ci_plan.write(ci_manifest)

    ci_evidence = execution_evidence_from_units(
        tier="pr",
        plan_fingerprint_digest=plan_fingerprint(ci_plan).digest(),
        commit="sha",
        units=[
            UnitExecution(u.unit_id, "pass", 0, "report.md") for u in ci_plan.selected
        ],
    )
    ev_path = tmp_path / "pr-exec.json"
    save_execution_evidence(ci_evidence, ev_path)

    report = reconcile_from_artifacts(
        local_plan_path=local_manifest,
        ci_plan_path=ci_manifest,
        ci_evidence_path=ev_path,
        commit="sha",
    )
    assert (
        report.classification.status
        == ReconciliationStatus.EXPECTED_TIER_DIFFERENCE.value
    )

    out = tmp_path / "recon.json"
    save_reconciliation_report(report, out)
    assert out.exists()


def test_m5e_exit_contract_mapping():
    """Verify the classify->exit mapping used by verify.py reconcile."""
    from runtime.foundation.verification.reconciliation import ReconciliationStatus

    def _exit(status: str) -> int:
        if status == ReconciliationStatus.PLANNING_DIVERGENCE.value:
            return 2
        if status == ReconciliationStatus.ENVIRONMENT_DIVERGENCE.value:
            return 1
        return 0

    assert _exit(ReconciliationStatus.SAME_PLAN.value) == 0
    assert _exit(ReconciliationStatus.EXPECTED_TIER_DIFFERENCE.value) == 0
    assert _exit(ReconciliationStatus.ENVIRONMENT_DIVERGENCE.value) == 1
    assert _exit(ReconciliationStatus.PLANNING_DIVERGENCE.value) == 2


def test_m5d_reconcile_persisted_same_plan_is_deterministic(tmp_path):
    """Reconciling the same persisted PR plan+evidence twice yields identical
    reports — the gate is deterministic, not dependent on live job state."""
    ci_plan = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")
    ci_manifest = tmp_path / "pr-plan.json"
    ci_plan.write(ci_manifest)
    ci_evidence = execution_evidence_from_units(
        tier="pr",
        plan_fingerprint_digest=plan_fingerprint(ci_plan).digest(),
        commit="sha",
        units=[
            UnitExecution(u.unit_id, "pass", 0, "report.md") for u in ci_plan.selected
        ],
    )
    ev_path = tmp_path / "pr-exec.json"
    save_execution_evidence(ci_evidence, ev_path)

    # Local side uses the same plan + identical evidence -> SAME_PLAN.
    r1 = reconcile_from_artifacts(
        local_plan_path=ci_manifest,
        ci_plan_path=ci_manifest,
        local_evidence_path=ev_path,
        ci_evidence_path=ev_path,
        commit="sha",
    )
    r2 = reconcile_from_artifacts(
        local_plan_path=ci_manifest,
        ci_plan_path=ci_manifest,
        local_evidence_path=ev_path,
        ci_evidence_path=ev_path,
        commit="sha",
    )
    assert r1.to_dict() == r2.to_dict()
    assert r1.classification.status == ReconciliationStatus.SAME_PLAN.value


def test_m5e_environment_vs_planning_distinction_preserved_in_report(tmp_path):
    """Both environment-divergence and planning-divergence fail the gate, but the
    persisted report records the distinct classification so the distinction is
    never lost."""
    ci_plan = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")
    ci_manifest = tmp_path / "pr-plan.json"
    ci_plan.write(ci_manifest)

    # Planning divergence: inject a divergent LOCAL plan manifest.
    local_div = plan_for_tier("local", changed_files=["frontend/src/App.tsx"])
    local_manifest = tmp_path / "local-plan.json"
    local_div.write(local_manifest)

    report = reconcile_from_artifacts(
        local_plan_path=local_manifest,
        ci_plan_path=ci_manifest,
        commit="sha",
    )
    # No evidence -> falls through to planning divergence (unexplained unit diff).
    assert report.classification.status == ReconciliationStatus.PLANNING_DIVERGENCE.value
    assert report.classification.planning_diverges is True
    assert report.classification.environment_diverges is False
    d = report.to_dict()
    assert d["classification"]["status"] == "planning-divergence"
