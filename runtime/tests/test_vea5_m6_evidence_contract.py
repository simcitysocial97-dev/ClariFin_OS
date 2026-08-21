"""VEA-5 M6 — Deep Verification & Evidence Contract acceptance tests.

Guards the M6 hard invariant and the Deep tier contract without turning M6 into a
large implementation batch. Focus: workstreams A (finer per-unit evidence
correlation, v2 schema) and B (Deep tier ownership contract). C/D/E are exercised
as versioned *interfaces* only.

Run:
    python3 -m pytest runtime/tests/test_vea5_m6_evidence_contract.py -q
"""

from __future__ import annotations


from runtime.foundation.verification.evidence_contract import (
    EVIDENCE_V2_SCHEMA,
    DeepVerificationDomain,
    DeepVerificationSurface,
    EvidenceArtifactRef,
    ExecutionAttempt,
    ExecutionEvidenceV2,
    FailureNormalizationNode,
    TestQualitySignal,
    UnitExecutionRecord,
    build_unit_execution_record,
    deep_catalog_coverage,
    deep_contract_manifest,
    deep_surfaces_by_domain,
    execution_evidence_v2_from_plan,
    load_execution_evidence_any,
    load_execution_evidence_v2,
    save_execution_evidence_v2,
)
from runtime.foundation.verification.reconciliation import (
    ExecutionEvidence,
    reconcile_from_artifacts,
)
from runtime.foundation.verification.tier import plan_for_tier

ENGINE_CHANGE = [
    "backend/src/engines/loan_engine/amortization.py",
    "backend/src/engines/loan_engine/floating_rate.py",
]


# ---------------------------------------------------------------------------
# M6-A — v2 per-unit evidence correlation.
# ---------------------------------------------------------------------------


def test_m6a_v2_schema_and_unit_attempt_artifact_path():
    """Hard invariant: unit_id -> attempts -> artifacts, unambiguously."""
    artifacts = [
        EvidenceArtifactRef(kind="test-report", ref="ev/backend-unit/junit.xml"),
        EvidenceArtifactRef(kind="coverage", ref="ev/backend-unit/coverage.json"),
    ]
    attempt = ExecutionAttempt(
        attempt_index=0,
        command="pytest backend/tests/unit",
        started_at="2026-08-12T00:00:00Z",
        ended_at="2026-08-12T00:01:00Z",
        duration_seconds=60.0,
        exit_code=0,
        status="pass",
        artifacts=tuple(artifacts),
    )
    rec = UnitExecutionRecord(
        unit_id="backend-unit",
        provenance={"category": "unit", "source": "blast-radius"},
        attempts=(attempt,),
    )
    assert rec.primary_status() == "pass"
    assert rec.primary_exit_code() == 0
    assert rec.to_dict()["attempts"][0]["artifacts"][0]["kind"] == "test-report"


def test_m6a_roundtrip_persisted_v2(tmp_path):
    artifacts = [EvidenceArtifactRef(kind="report", ref="ev/r.md")]
    rec = build_unit_execution_record(
        unit_id="mutation-run",
        provenance={"category": "mutation"},
        command="bash run_mutation.sh",
        status="fail",
        exit_code=1,
        duration_seconds=10.0,
        artifacts=artifacts,
    )
    ev = ExecutionEvidenceV2(
        tier="pr",
        plan_fingerprint="deadbeef",
        commit="sha",
        units=(rec,),
    )
    p = save_execution_evidence_v2(ev, tmp_path / "ev.json")
    loaded = load_execution_evidence_v2(p)
    assert loaded.to_dict()["schema"] == EVIDENCE_V2_SCHEMA
    assert loaded.units[0].unit_id == "mutation-run"
    assert loaded.units[0].attempts[0].status == "fail"
    assert loaded.units[0].attempts[0].artifacts[0].kind == "report"
    assert loaded.to_dict() == ev.to_dict()


def test_m6a_load_accepts_v1_and_normalizes_to_v2(tmp_path):
    """Back-compat: a legacy v1 artifact loads and normalizes to v2."""
    v1 = ExecutionEvidence(
        tier="pr",
        plan_fingerprint="abc",
        commit="sha",
        units=[
            __import__(
                "runtime.foundation.verification.reconciliation",
                fromlist=["UnitExecution"],
            ).UnitExecution("backend-unit", "pass", 0, "report.md")
        ],
    )
    p = tmp_path / "v1.json"
    p.write_text(__import__("json").dumps(v1.to_dict(), indent=2), encoding="utf-8")
    normalized = load_execution_evidence_any(p)
    assert normalized.to_dict()["schema"] == EVIDENCE_V2_SCHEMA
    assert normalized.units[0].unit_id == "backend-unit"
    assert normalized.units[0].attempts[0].status == "pass"


def test_m6a_every_selected_unit_has_record(tmp_path):
    """Hard invariant: every selected unit has an unambiguous evidence path; a
    missing record is surfaced as an explicit 'no-evidence' attempt, never silent."""
    plan = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")
    # Provide records only for a subset.
    recs = {
        "backend-unit": build_unit_execution_record(
            unit_id="backend-unit",
            provenance={},
            command="x",
            status="pass",
            exit_code=0,
        )
    }
    ev = execution_evidence_v2_from_plan(plan=plan, commit="sha", records=recs)
    by_id = {u.unit_id: u for u in ev.units}
    assert set(by_id) == {s.unit_id for s in plan.selected}
    # Units without a supplied record are explicit 'no-evidence', not dropped.
    missing = [u for u in ev.units if u.attempts[0].status == "no-evidence"]
    assert missing  # backend-unit is present; others flagged
    assert "backend-unit" not in {m.unit_id for m in missing}


# ---------------------------------------------------------------------------
# M6-B — Deep tier ownership contract.
# ---------------------------------------------------------------------------


def test_m6b_deep_contract_has_six_domains_and_surfaces():
    manifest = deep_contract_manifest()
    assert manifest["schema"] == "vea5-deep-contract/v1"
    assert set(manifest["domains"]) == {d.value for d in DeepVerificationDomain}
    assert len(manifest["surfaces"]) >= 10
    # The two questions are distinct and explicit.
    assert "is the entire system still healthy?" in manifest["question"]
    assert "what does this change require?" in manifest["pr_question"]


def test_m6b_deep_owns_all_expensive_catalog_units():
    """DEEP must own the heavy catalog units (mutation, golden, playwright,
    backend/frontend/runtime suites) per the contract."""
    covered = deep_catalog_coverage()
    for uid in (
        "mutation-run",
        "golden-regression",
        "playwright-e2e",
        "backend-unit",
        "frontend-unit",
        "runtime-self-test",
        "contracts-schemathesis",
        "backend-integration",
        "frontend-typecheck-build",
    ):
        assert uid in covered


def test_m6b_heavy_surfaces_excluded_from_pr_trigger():
    """Heavy surfaces must NOT be scheduled on every PR; their trigger cadence is
    schedule/manual/release (and merge only for security)."""
    for s in deep_surfaces_by_domain(DeepVerificationDomain.TEST_EFFECTIVENESS.value):
        assert "pr" not in s.trigger
    for s in deep_surfaces_by_domain(DeepVerificationDomain.REGRESSION.value):
        assert "pr" not in s.trigger


def test_m6b_surface_shape_is_pluggable():
    s = DeepVerificationSurface(
        surface_id="x",
        domain=DeepVerificationDomain.UI.value,
        description="d",
        command="c",
        catalog_units=("playwright-e2e",),
        trigger=("schedule",),
        evidence_kinds=("screenshots", "video"),
    )
    d = s.to_dict()
    assert d["domain"] == "ui"
    assert d["catalog_units"] == ["playwright-e2e"]
    assert d["trigger"] == ["schedule"]


# ---------------------------------------------------------------------------
# M6-C/D/E — evidence interfaces are defined (not fully implemented).
# ---------------------------------------------------------------------------


def test_m6c_test_quality_signal_is_versioned_interface():
    sig = TestQualitySignal(
        level="mutation",
        metric="mutation_score",
        value=0.82,
        evidence_ref="ev/mutation.json",
        unit="score",
    )
    assert sig.level == "mutation"
    assert sig.value == 0.82


def test_m6e_failure_normalization_node_shape():
    node = FailureNormalizationNode(
        failure_id="f1",
        unit_id="backend-unit",
        capability="engine:loan_engine",
        impact_kind="engine",
        dependency_ref="chain-map:router",
        affected_units=("contracts-schemathesis",),
        execution_evidence_ref="ev/backend-unit",
        normalized_signature="LoanEngine.amortization.regression",
    )
    assert node.unit_id == "backend-unit"
    assert node.capability and node.impact_kind
    assert node.affected_units


# ---------------------------------------------------------------------------
# M6-A + M5-E integration: v2 evidence feeds reconcile deterministically.
# ---------------------------------------------------------------------------


def test_m6a_v2_evidence_feeds_reconcile(tmp_path):
    ci_plan = plan_for_tier("pr", changed_files=ENGINE_CHANGE, explicit_base="main")
    ci_manifest = tmp_path / "pr-plan.json"
    ci_plan.write(ci_manifest)

    records = {
        s.unit_id: build_unit_execution_record(
            unit_id=s.unit_id,
            provenance={"category": s.category},
            command=s.command,
            status="pass",
            exit_code=0,
        )
        for s in ci_plan.selected
    }
    ev = execution_evidence_v2_from_plan(plan=ci_plan, commit="sha", records=records)
    ev_path = tmp_path / "pr-exec.json"
    save_execution_evidence_v2(ev, ev_path)

    # Same plan + same evidence on both sides -> SAME_PLAN (deterministic).
    report = reconcile_from_artifacts(
        local_plan_path=ci_manifest,
        ci_plan_path=ci_manifest,
        local_evidence_path=ev_path,
        ci_evidence_path=ev_path,
        commit="sha",
    )
    assert report.classification.status == "same-plan"
    d = report.to_dict()
    assert d["classification"]["status"] == "same-plan"
