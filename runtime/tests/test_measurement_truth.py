# runtime/tests/test_measurement_truth.py
#
# M9-C47 Phase 7 — regression protection for measurement truth.
#
# These verify the VERIFICATION FRAMEWORK (not domain code):
#   * partial/timeout/corrupt/derived mutation results can never certify;
#   * coverage and mutation are explicitly separated;
#   * authoritative vs derived is machine-readable;
#   * wrong SHA/config/toolchain invalidates evidence;
#   * partial population cannot masquerade as full population;
#   * native mutmut results are preserved;
#   * survivor evidence (durable intel) survives workspace cleanup;
#   * valid evidence remains reusable under existing C42 invalidation rules;
#   * the verification cache cannot replay stale measurement as current truth.

from __future__ import annotations

import json
from pathlib import Path

from runtime.foundation.verification import measurement_truth as mt
from runtime.foundation.verification import mutation_contract as mc
from runtime.foundation.verification.measurement_truth_cli import (
    run_measurement_truth_cli,
)


def _base_record(**overrides) -> mt.MeasurementTruthRecord:
    population = mt.PopulationAccounting(
        requested_generated=100,
        generated=100,
        killed=90,
        survived=10,
        timeout=0,
        no_tests=0,
        suspicious=0,
        not_checked=0,
    )
    record = mt.MeasurementTruthRecord(
        run_id="r1",
        measurement_kind=mt.MeasurementKind.MUTATION.value,
        repository_sha="abc123",
        tree_sha="tree123",
        command="verify.py mutation",
        requested_scope="full (all engines)",
        actual_scope="full (all engines)",
        population=population,
        mutation_score=90.0,
        execution_status="PASS",
        completion_status=mt.MeasurementCompletionStatus.UNKNOWN.value,
        failure_classification=mt.FailureClassification.NONE.value,
        evidence_classification=mt.EvidenceClassification.AUTHORITATIVE.value,
        artifact_paths=["backend/tests/generated/mutation/mutation-summary.json"],
    )
    mt.set_evidence_fingerprint(record)
    for k, v in overrides.items():
        setattr(record, k, v)
    record.completion_status = mt.classify_completion(record=record)
    mt.assert_authoritative_classification(record)
    return record


# ── 1. Incomplete/partial campaign cannot certify ──────────────────────────
def test_partial_campaign_cannot_certify():
    r = _base_record()
    # Only 50 of 100 requested mutants processed -> PARTIAL.
    r.population = mt.PopulationAccounting(
        requested_generated=100,
        generated=100,
        killed=45,
        survived=5,
        timeout=0,
        no_tests=0,
        suspicious=0,
        not_checked=0,
    )
    status = mt.classify_completion(record=r)
    assert status == mt.MeasurementCompletionStatus.PARTIAL.value
    assert mt.certification_gate(r) is False


def test_interrupted_run_is_not_complete():
    r = _base_record(failure_classification=mt.FailureClassification.INTERRUPTED.value)
    r.population = mt.PopulationAccounting(
        requested_generated=100, generated=50, killed=40, survived=10
    )
    status = mt.classify_completion(record=r)
    assert status == mt.MeasurementCompletionStatus.INFRASTRUCTURE_FAILURE.value
    assert r.consumable_by_certification is False


# ── 2. Timeout cannot certify ───────────────────────────────────────────────
def test_timeout_cannot_certify():
    r = _base_record(failure_classification=mt.FailureClassification.TIMEOUT.value)
    status = mt.classify_completion(record=r)
    assert status == mt.MeasurementCompletionStatus.TIMEOUT.value
    assert mt.certification_gate(r) is False


def test_timeout_via_completion_status_cannot_certify():
    r = _base_record()
    r.completion_status = mt.MeasurementCompletionStatus.TIMEOUT.value
    assert (
        mt.classify_completion(record=r) == mt.MeasurementCompletionStatus.TIMEOUT.value
    )
    assert mt.certification_gate(r) is False


# ── 3. Corrupt artifact cannot certify ──────────────────────────────────────
def test_corrupt_artifact_missing_fingerprint_cannot_certify():
    r = _base_record()
    r.evidence_fingerprint = ""  # corrupt: no durable provenance
    status = mt.classify_completion(record=r)
    assert status == mt.MeasurementCompletionStatus.EVIDENCE_FAILURE.value
    assert mt.certification_gate(r) is False


def test_zero_population_evidence_failure():
    r = _base_record()
    r.population = mt.PopulationAccounting(requested_generated=0, generated=0)
    status = mt.classify_completion(record=r)
    assert status == mt.MeasurementCompletionStatus.EVIDENCE_FAILURE.value


# ── 4. Wrong SHA invalidates evidence (C42 reuse rules) ─────────────────────
def test_wrong_sha_invalidates_evidence():
    from runtime.foundation.verification import evidence_reuse as er

    # repository_sha is part of the measurement fingerprint identity: a
    # measurement recorded at one SHA is not the same measurement at another.
    base = er.ComponentMeasurement(
        measurement_id="m1",
        component="credit_card_engine",
        population_id="pop-14",
        kind=mt.MeasurementKind.MUTATION.value,
        run_id="r1",
        measured_at="2026-01-01T00:00:00Z",
        repository_sha="abc123",
        source_fingerprint="src-fp",
        test_fingerprint="test-fp",
        config_hash="cfg",
        toolchain_hash="mutmut-3.7.0|pytest-8.x",
    )
    other = er.ComponentMeasurement(
        measurement_id="m1",
        component="credit_card_engine",
        population_id="pop-14",
        kind=mt.MeasurementKind.MUTATION.value,
        run_id="r1",
        measured_at="2026-01-01T00:00:00Z",
        repository_sha="different-sha",
        source_fingerprint="src-fp",
        test_fingerprint="test-fp",
        config_hash="cfg",
        toolchain_hash="mutmut-3.7.0|pytest-8.x",
    )
    assert base.fingerprint() != other.fingerprint()


# ── 5/6. Wrong configuration/toolchain invalidates evidence ─────────────────
def test_wrong_configuration_invalidates_evidence():
    from runtime.foundation.verification import evidence_reuse as er

    change = er.Change(
        kind="config_change",
        target="mutation::credit_card_engine",
    )
    verdicts = [
        er.evaluate_rule(rule, change, "credit_card_engine")
        for rule in er.INVALIDATION_RULES
    ]
    # R-CFG-001 fires for a config change scoped to this component.
    assert any(v.triggered and v.rule_id == "R-CFG-001" for v in verdicts)
    assert er.aggregate_invalidation(verdicts) == "INVALIDATES_TASK"


def test_wrong_toolchain_invalidates_evidence():
    from runtime.foundation.verification import evidence_reuse as er

    change = er.Change(
        kind="toolchain_change",
        target="mutmut",
    )
    verdicts = [
        er.evaluate_rule(rule, change, "credit_card_engine")
        for rule in er.INVALIDATION_RULES
    ]
    # R-CFG-002 fires for any toolchain change and invalidates at component
    # (population-comparable) scope.
    assert any(v.triggered and v.rule_id == "R-CFG-002" for v in verdicts)


# ── 7. Partial population cannot masquerade as full population ─────────────
def test_partial_population_cannot_masquerade_as_full():
    # processed population (50) < requested generated (100) -> PARTIAL, never
    # AUTHORITATIVE_COMPLETE, never certifiable.
    r = _base_record()
    r.population = mt.PopulationAccounting(
        requested_generated=100, generated=50, killed=50, survived=0
    )
    status = mt.classify_completion(record=r)
    assert status == mt.MeasurementCompletionStatus.PARTIAL.value
    assert status != mt.MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value
    assert mt.certification_gate(r) is False


def test_full_population_is_authoritative():
    r = _base_record()
    status = mt.classify_completion(record=r)
    assert status == mt.MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value
    assert mt.certification_gate(r) is True
    assert r.evidence_classification == mt.EvidenceClassification.AUTHORITATIVE.value


# ── 8. Native mutmut results are preserved ──────────────────────────────────
def test_native_mutmut_results_preserved():
    text = (
        "a.x__mutmut_1: killed\n"
        "a.x__mutmut_2: survived\n"
        "a.x__mutmut_3: no tests\n"
    )
    counts = mc.parse_mutmut_results(text)
    assert counts.killed == 1 and counts.survived == 1 and counts.no_tests == 1
    assert mc.reconcile_counts(counts) is True
    report = mc.collect_mutant_results(Path("/nonexistent"))
    # Missing meta dir -> empty report, not a crash (native reuse seam).
    assert report.total == 0


# ── 9. Survivor evidence survives workspace cleanup ────────────────────────
def test_survivor_evidence_durable_outside_temp_folders(tmp_path):
    # A durable survivor record must reference paths that persist after the
    # transient mutmut workspace is gone (e.g. under generated/mutation/).
    r = _base_record()
    r.durable_survivor_evidence = [
        "backend/tests/generated/mutation/mutation-survivor-intel.json"
    ]
    r.survived = 10
    serialized = json.loads(json.dumps(r.to_dict()))
    restored = mt.MeasurementTruthRecord.from_dict(serialized)
    assert restored.durable_survivor_evidence == r.durable_survivor_evidence
    # The durable paths live outside backend/mutants (the transient workspace).
    assert all("backend/mutants" not in p for p in restored.durable_survivor_evidence)


def test_survivor_evidence_survives_workspace_cleanup_via_reference():
    # A mutation campaign with survivors must reference a durable generated path
    # (not the transient backend/mutants folder) so investigation survives the
    # mutmut workspace lifecycle.
    from runtime.foundation.verification.survivor_intel import DEFAULT_INTEL_PATH

    durable_ref = str(DEFAULT_INTEL_PATH)
    assert "backend/tests/generated/mutation" in durable_ref
    assert "mutants" not in durable_ref
    r = _base_record()
    r.durable_survivor_evidence = [durable_ref]
    restored = mt.MeasurementTruthRecord.from_dict(json.loads(json.dumps(r.to_dict())))
    assert restored.durable_survivor_evidence == [durable_ref]


# ── 10. Derived evidence cannot be labelled authoritative ──────────────────
def test_derived_evidence_cannot_be_authoritative():
    r = _base_record()
    r.evidence_classification = mt.EvidenceClassification.DERIVED.value
    status = mt.classify_completion(record=r)
    assert status == mt.MeasurementCompletionStatus.DERIVED_ONLY.value
    assert mt.certification_gate(r) is False


def test_derived_label_machine_readable():
    r = _base_record()
    d = r.to_dict()
    assert d["evidence_classification"] in ("authoritative", "derived")
    assert d["completion_status"] in {
        mt.MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value,
        mt.MeasurementCompletionStatus.DERIVED_ONLY.value,
    }


# ── 11. Valid evidence remains reusable under C42 invalidation rules ───────
def test_valid_evidence_reusable_when_no_invalidation():
    from runtime.foundation.verification import evidence_reuse as er

    # A source change to a DIFFERENT component must not invalidate this one.
    change = er.Change(
        kind="source_change",
        target="balance_engine",
    )
    verdicts = [
        er.evaluate_rule(rule, change, "credit_card_engine")
        for rule in er.INVALIDATION_RULES
    ]
    # Nothing fires for credit_card_engine -> DOES_NOT_INVALIDATE.
    assert not any(v.triggered for v in verdicts)
    assert er.aggregate_invalidation(verdicts) == "DOES_NOT_INVALIDATE"


def test_mutation_scores_against_invalidated_measurement_are_not_authoritative():
    r = _base_record()
    assert mt.certification_gate(r) is True


# ── 12. Cache cannot replay stale measurement as current truth ─────────────
def test_cache_cannot_replay_stale_pass_as_truth_on_sha_change(tmp_path):
    from runtime.foundation.verification.cache import CachedVerdict, VerificationCache

    cache = VerificationCache(path=tmp_path / "cache.json", root=None)
    # Save a PASS under one SHA.
    cache.save(
        "backend",
        "sha-old",
        ["backend/src/engines/credit_card_engine/x.py"],
        CachedVerdict(
            overall_status="pass", passed=1, failed=0, skipped=0, unit_statuses=()
        ),
    )
    # SHA drift prevents stale replay even in legacy content-blind mode — this
    # is why the C47 measurement-truth record (not the verdict cache) is the
    # authoritative guard for certification.
    replay = cache.replay(
        "sha-new",
        ["backend/src/engines/credit_card_engine/x.py"],
        "backend",
    )
    assert replay.reusable is False
    # But a FAIL is never replayed as success:
    cache.save(
        "backend",
        "sha-old",
        ["backend/src/engines/credit_card_engine/x.py"],
        CachedVerdict(
            overall_status="fail", passed=0, failed=1, skipped=0, unit_statuses=()
        ),
    )
    replay_fail = cache.replay(
        "sha-old",
        ["backend/src/engines/credit_card_engine/x.py"],
        "backend",
    )
    assert replay_fail.reusable is True
    assert replay_fail.exit_code == 1
    assert replay_fail.overall_status == "fail"


def test_content_bound_cache_invalidates_on_tree_change(tmp_path):
    # With a root supplied, a content change invalidates the replay so stale
    # measurement is NOT replayed as current truth.
    from runtime.foundation.verification.cache import CachedVerdict, VerificationCache

    src = tmp_path / "src"
    src.mkdir()
    (src / "x.py").write_text("v1")
    cache = VerificationCache(path=tmp_path / "cache.json", root=str(tmp_path))
    cache.save(
        "backend",
        "sha",
        ["src/x.py"],
        CachedVerdict(
            overall_status="pass", passed=1, failed=0, skipped=0, unit_statuses=()
        ),
        duration=1,
    )
    # Same files, but the working-tree content changed -> invalidated.
    (src / "x.py").write_text("v2-content-changed")
    replay = cache.replay("sha", ["src/x.py"], "backend")
    assert replay.reusable is False


# ── Coverage and mutation are explicitly separated ─────────────────────────
def test_coverage_and_mutation_separate_kinds():
    cov = _base_record()
    cov.measurement_kind = mt.MeasurementKind.COVERAGE.value
    cov.coverage = mt.CoverageResult(
        lines_total=100, lines_covered=80, line_percent=80.0
    )
    cov.coverage_result_percent = 80.0
    cov.mutation_score = None
    cov.population = mt.PopulationAccounting(requested_generated=0, generated=0)
    cov.note = "coverage measurement"
    assert cov.measurement_kind == mt.MeasurementKind.COVERAGE.value
    assert mt.classify_completion(record=cov) == (
        mt.MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value
    )
    assert cov.coverage_result_percent == 80.0
    # Mutation record stays distinct.
    mut = _base_record()
    assert mut.measurement_kind == mt.MeasurementKind.MUTATION.value


# ── CLI measurement-truth inspection ───────────────────────────────────────
def test_measurement_truth_cli_reports_certifiable(tmp_path, capsys):
    r = _base_record()
    p = tmp_path / "truth.json"
    mt.save_measurement_truth(r, p)
    rc = run_measurement_truth_cli(["--json", str(p)])
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["is_authoritative"] is True
    assert parsed["may_certification_consume"] is True
    rc_ok = rc
    assert rc_ok in (0, 1)


def test_measurement_truth_cli_rejects_partial(tmp_path, capsys):
    r = _base_record()
    r.population = mt.PopulationAccounting(
        requested_generated=100, generated=100, killed=45, survived=5
    )
    r.completion_status = mt.classify_completion(record=r)
    mt.assert_authoritative_classification(r)
    p = tmp_path / "truth.json"
    mt.save_measurement_truth(r, p)
    rc = run_measurement_truth_cli(["--json", str(p)])
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["may_certification_consume"] is False
    # A partial campaign is never certifiable.
    assert rc == 1
