"""
M9-C42.29 — M29.6 End-to-end CI evidence scenarios (CI-A … CI-H).

Each scenario builds canonical CIEvidenceRecords against the *real*
repository fingerprints, then deterministically perturbs either the
record or the repository context and validates the framework's
behaviour:

  CI-A  unchanged CI evidence          -> REUSABLE, no execution needed
  CI-B  source change                  -> affected targeted, rest reused,
                                          aggregate derived where valid
  CI-C  test-only change               -> test evidence revalidation;
                                          mutation evidence with intact
                                          fingerprint NOT discarded
  CI-D  verification config change     -> only config-dependent evidence
                                          invalidated (no repo-wide
                                          escalation)
  CI-E  toolchain change               -> mutation measurement invalidated
                                          per R-CFG-002
  CI-F  corrupt/missing CI artifact    -> evidence_failure (NOT
                                          verification_failure)
  CI-G  CI verification actually fails -> verification_failure
  CI-H  infrastructure failure         -> infrastructure_failure

Run with:
    .venv/bin/python runtime/generated/m9-c42.29/m29_6_scenarios.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c42.29"
OUT_DIR.mkdir(parents=True, exist_ok=True)

from runtime.foundation.verification.ci_evidence import (  # noqa: E402
    CIEvidenceRecord,
    CIRepositoryContext,
    FailureKind,
    build_ci_bindings,
    classify_ci_failure,
    validate_and_decide,
    validate_ci_evidence,
    verification_bindings,
)
from runtime.foundation.verification.executor_pipeline import (  # noqa: E402
    TaskFingerprints,
    collect_repo_fingerprints,
)

# collect_repo_fingerprints resolves the full environment on every call
# (~1.4s). Scenario determinism does not require re-resolution within a
# single process, so results are memoized here.
_FP_CACHE: dict[str, TaskFingerprints] = {}


def _fps(component: str) -> TaskFingerprints:
    if component not in _FP_CACHE:
        _FP_CACHE[component] = collect_repo_fingerprints(component)
    return _FP_CACHE[component]


def _context_from(
    *,
    sha: str | None = None,
    components: tuple[str, ...],
    population_fingerprint: str,
) -> CIRepositoryContext:
    base = _fps(components[0])
    return CIRepositoryContext(
        repository_sha=sha or "",
        component_source_fingerprints={c: _fps(c).source for c in components},
        component_test_fingerprints={c: _fps(c).test for c in components},
        configuration_fingerprint=base.config,
        toolchain_fingerprint=base.toolchain,
        population_fingerprint=population_fingerprint,
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _make_record(
    component: str,
    *,
    repository_sha: str = "084359346b3b14792c5bd38e159932f6c42922fd",
    exit_status: int = 0,
    workflow: str = "mutation.yml",
    job: str = "mutation",
    step: str = "run-mutation",
    notes: str = "",
    summary: dict | None = None,
) -> CIEvidenceRecord:
    """Build a realistic targeted-CI mutation record for a component."""
    fps = _fps(component)
    counts = {"generated": 582, "killed": 440, "survived": 142}
    effective = summary if summary is not None else {"counts": counts}
    return CIEvidenceRecord(
        record_id=f"ci-{component}-{hashlib.sha1(component.encode()).hexdigest()[:8]}",
        repository_sha=repository_sha,
        workflow=workflow,
        job=job,
        step=step,
        verification_task="task::mutation::targeted",
        component=component,
        capability=component.replace("_engine", "").replace("_", "-"),
        evidence_kind="mutation-summary",
        execution_mode="targeted",
        source_fingerprint=fps.source,
        test_fingerprint=fps.test,
        configuration_fingerprint=fps.config,
        toolchain_fingerprint=fps.toolchain,
        population_fingerprint="pop-14-fingerprint",
        evidence_artifact_fingerprint=hashlib.sha256(
            json.dumps(effective.get("counts", {}), sort_keys=True).encode()
        ).hexdigest(),
        artifact_path="",  # synthetic artifact; bytes supplied at validation
        started_at=_now(),
        ended_at=_now(),
        exit_status=exit_status,
        failure_classification=None,
        summary=effective,
        notes=notes,
    )


def _context(sha: str | None = None, **overrides) -> CIRepositoryContext:
    """Capture a repository context for the population (memoized fps)."""
    from runtime.foundation.verification.evidence_reuse import C42_26_COMPONENTS

    ctx = _context_from(
        sha=sha,
        components=C42_26_COMPONENTS,
        population_fingerprint="pop-14-fingerprint",
    )
    if overrides:
        ctx = CIRepositoryContext(
            repository_sha=overrides.get("sha", ctx.repository_sha),
            component_source_fingerprints=overrides.get(
                "src", ctx.component_source_fingerprints
            ),
            component_test_fingerprints=overrides.get(
                "tst", ctx.component_test_fingerprints
            ),
            configuration_fingerprint=overrides.get("cfg", ctx.configuration_fingerprint),
            toolchain_fingerprint=overrides.get("tool", ctx.toolchain_fingerprint),
            population_fingerprint=ctx.population_fingerprint,
        )
    return ctx


def _artifact_bytes(record: CIEvidenceRecord) -> bytes:
    return json.dumps(record.summary.get("counts", {}), sort_keys=True).encode()


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def scenario_ci_a() -> dict:
    """Unchanged CI evidence remains reusable; no execution needed."""
    comp = "credit_card_engine"
    record = _make_record(comp)
    ctx = _context()
    report, decision = validate_and_decide(
        record, ctx, expected_artifact_bytes=_artifact_bytes(record)
    )
    return {
        "scenario": "CI-A",
        "name": "unchanged_ci_evidence",
        "expected": "reusable; no unnecessary execution",
        "disposition": decision.disposition,
        "reusable": decision.reusable,
        "drifts": [d.drift_kind for d in report.drifts],
        "pass": decision.reusable and decision.disposition == "reusable" and not report.drifts,
    }


def scenario_ci_b() -> dict:
    """Source change invalidates only the affected component's evidence."""
    changed_comp = "credit_card_engine"
    untouched_comp = "loan_engine"

    record_changed = _make_record(changed_comp)
    record_untouched = _make_record(untouched_comp)

    # Simulate a source change to credit_card_engine only.
    ctx = _context()
    mutated_src = dict(ctx.component_source_fingerprints)
    mutated_src[changed_comp] = hashlib.sha256(b"AFTER-CHANGE").hexdigest()
    ctx_after = CIRepositoryContext(
        repository_sha=ctx.repository_sha,
        component_source_fingerprints=mutated_src,
        component_test_fingerprints=ctx.component_test_fingerprints,
        configuration_fingerprint=ctx.configuration_fingerprint,
        toolchain_fingerprint=ctx.toolchain_fingerprint,
        population_fingerprint=ctx.population_fingerprint,
    )

    _, dec_changed = validate_and_decide(
        record_changed, ctx_after, expected_artifact_bytes=_artifact_bytes(record_changed)
    )
    _, dec_untouched = validate_and_decide(
        record_untouched, ctx_after, expected_artifact_bytes=_artifact_bytes(record_untouched)
    )

    # Aggregate derivation over unaffected components stays mathematically valid.
    aggregate_derivable = dec_untouched.reusable

    return {
        "scenario": "CI-B",
        "name": "source_change_scope",
        "expected": (
            "affected component -> targeted verification; "
            "unaffected -> reused; aggregate derived where valid"
        ),
        "changed_disposition": dec_changed.disposition,
        "unchanged_disposition": dec_untouched.disposition,
        "aggregate_derivable": aggregate_derivable,
        "pass": (
            dec_changed.disposition == "invalidated_component"
            and not dec_changed.reusable
            and dec_untouched.disposition == "reusable"
            and dec_untouched.reusable
            and aggregate_derivable
        ),
    }


def scenario_ci_c() -> dict:
    """Test-only change: test evidence requires revalidation; mutation
    evidence whose own validity fingerprint remains intact is kept."""
    comp = "credit_card_engine"
    other = "account_engine"

    mutation_record = _make_record(comp)
    # The mutation record's test surface fingerprint still matches the
    # CURRENT surface for its component (the changed tests belong to a
    # different component), so it must NOT be discarded.
    ctx = _context()
    mutated_tst = dict(ctx.component_test_fingerprints)
    mutated_tst[other] = hashlib.sha256(b"TESTS-CHANGED").hexdigest()
    ctx_after = CIRepositoryContext(
        repository_sha=ctx.repository_sha,
        component_source_fingerprints=ctx.component_source_fingerprints,
        component_test_fingerprints=mutated_tst,
        configuration_fingerprint=ctx.configuration_fingerprint,
        toolchain_fingerprint=ctx.toolchain_fingerprint,
        population_fingerprint=ctx.population_fingerprint,
    )

    # A behavioral (test-report) record bound to the changed test surface.
    fps_other = _fps(other)
    suite_record = CIEvidenceRecord(
        record_id="ci-backend-suite-old",
        repository_sha=ctx.repository_sha,
        workflow="backend-verify.yml",
        job="backend",
        step="verify",
        verification_task="task::unit::backend-suite",
        component=None,
        capability=None,
        evidence_kind="test-report",
        execution_mode="observational",
        source_fingerprint="",
        test_fingerprint=hashlib.sha256(b"OLD-SUITE-FINGERPRINT").hexdigest(),
        configuration_fingerprint="",
        toolchain_fingerprint=fps_other.toolchain,
        population_fingerprint="pop-14-fingerprint",
        evidence_artifact_fingerprint="",
        artifact_path="",
        started_at=_now(),
        ended_at=_now(),
        exit_status=0,
        failure_classification=None,
    )

    _, dec_mutation = validate_and_decide(
        mutation_record, ctx_after, expected_artifact_bytes=_artifact_bytes(mutation_record)
    )
    report_suite = validate_ci_evidence(suite_record, ctx_after)
    # Suite-level observational evidence sees global test drift.
    test_drift_present = any(d.drift_kind == "test_drift" for d in report_suite.drifts)

    return {
        "scenario": "CI-C",
        "name": "test_only_change",
        "expected": (
            "test evidence stale/revalidation-required; mutation evidence "
            "with intact validity fingerprint NOT discarded"
        ),
        "mutation_disposition": dec_mutation.disposition,
        "mutation_reusable": dec_mutation.reusable,
        "suite_test_drift_detected": test_drift_present,
        "pass": (
            dec_mutation.disposition == "reusable"
            and dec_mutation.reusable
            and test_drift_present
        ),
    }


def scenario_ci_d() -> dict:
    """Verification configuration change: only config-semantics-dependent
    evidence becomes invalid; no repository-wide escalation."""
    comp_mutation = "credit_card_engine"

    mutation_record = _make_record(comp_mutation)

    # A behavioral suite record whose semantics do NOT depend on the
    # mutation configuration: no config fingerprint, no artifact claim.
    suite = CIEvidenceRecord(
        record_id="ci-backend-suite-cfg",
        repository_sha=mutation_record.repository_sha,
        workflow="backend-verify.yml",
        job="backend",
        step="verify",
        verification_task="task::unit::backend-suite",
        component=None,
        capability=None,
        evidence_kind="test-report",
        execution_mode="observational",
        source_fingerprint="",
        test_fingerprint="",
        configuration_fingerprint="",
        toolchain_fingerprint=_fps("loan_engine").toolchain,
        population_fingerprint="pop-14-fingerprint",
        evidence_artifact_fingerprint="",
        artifact_path="",
        started_at=_now(),
        ended_at=_now(),
        exit_status=0,
        failure_classification=None,
    )

    ctx = _context()
    ctx_after_cfg = CIRepositoryContext(
        repository_sha=ctx.repository_sha,
        component_source_fingerprints=ctx.component_source_fingerprints,
        component_test_fingerprints=ctx.component_test_fingerprints,
        configuration_fingerprint=hashlib.sha256(b"NEW-MUTATION-CONFIG").hexdigest(),
        toolchain_fingerprint=ctx.toolchain_fingerprint,
        population_fingerprint=ctx.population_fingerprint,
    )

    _, dec_mutation = validate_and_decide(
        mutation_record, ctx_after_cfg, expected_artifact_bytes=_artifact_bytes(mutation_record)
    )
    report_suite = validate_ci_evidence(suite, ctx_after_cfg)
    _, dec_suite = validate_and_decide(suite, ctx_after_cfg)
    cfg_drift_on_suite = any(
        d.drift_kind == "configuration_drift" for d in report_suite.drifts
    )

    return {
        "scenario": "CI-D",
        "name": "verification_configuration_change",
        "expected": "only config-dependent evidence invalidated; no silent expansion",
        "mutation_disposition": dec_mutation.disposition,
        "suite_disposition": dec_suite.disposition,
        "suite_config_drift": cfg_drift_on_suite,
        "pass": (
            dec_mutation.disposition in ("invalidated_task", "invalidated_component")
            and not dec_mutation.reusable
            and dec_suite.disposition == "reusable"
            and not cfg_drift_on_suite
        ),
    }


def scenario_ci_e() -> dict:
    """Toolchain change invalidates mutation measurement per hierarchy."""
    comp = "credit_card_engine"
    record = _make_record(comp)
    ctx = _context()
    ctx_new_tool = CIRepositoryContext(
        repository_sha=ctx.repository_sha,
        component_source_fingerprints=ctx.component_source_fingerprints,
        component_test_fingerprints=ctx.component_test_fingerprints,
        configuration_fingerprint=ctx.configuration_fingerprint,
        toolchain_fingerprint=hashlib.sha256(b"mutmut-4.0|pytest-9").hexdigest(),
        population_fingerprint=ctx.population_fingerprint,
    )
    report, decision = validate_and_decide(
        record, ctx_new_tool, expected_artifact_bytes=_artifact_bytes(record)
    )
    rule_ids = {d.rule_id for d in report.drifts}
    return {
        "scenario": "CI-E",
        "name": "toolchain_change",
        "expected": "invalidated per existing invalidation hierarchy (R-CFG-002)",
        "disposition": decision.disposition,
        "rule_ids": sorted(r for r in rule_ids if r),
        "pass": (
            not decision.reusable
            and "R-CFG-002" in rule_ids
            and decision.disposition in ("invalidated_component", "invalidated_capability", "invalidated_task")
        ),
    }


def scenario_ci_f() -> dict:
    """Corrupt/missing CI artifact classifies as evidence_failure."""
    comp = "credit_card_engine"
    record_missing = _make_record(comp)
    record_corrupt = _make_record(comp)

    ctx = _context()

    report_missing, dec_missing = validate_and_decide(
        record_missing, ctx, expected_artifact_bytes=None  # nothing supplied, path empty->missing
    )
    # Force 'missing': give the record a declared artifact fingerprint but no bytes.
    rec = record_missing.to_dict()
    rec["artifact_path"] = "runtime/generated/m9-c42.29/does-not-exist.json"
    from runtime.foundation.verification.ci_evidence import CIEvidenceRecord as R

    missing = R.from_dict(rec)
    report_missing, dec_missing = validate_and_decide(missing, ctx)

    bad_bytes = b"CORRUPTED"
    report_corrupt, dec_corrupt = validate_and_decide(
        record_corrupt, ctx, expected_artifact_bytes=bad_bytes
    )

    fk_missing = classify_ci_failure(missing, artifact_state=report_missing.artifact_state)
    fk_corrupt = classify_ci_failure(record_corrupt, artifact_state=report_corrupt.artifact_state)
    ok = (
        fk_missing == FailureKind.EVIDENCE
        and fk_corrupt == FailureKind.EVIDENCE
        and not dec_missing.reusable
        and not dec_corrupt.reusable
    )
    return {
        "scenario": "CI-F",
        "name": "corrupt_or_missing_artifact",
        "expected": "classified evidence_failure, NOT verification_failure",
        "missing_state": report_missing.artifact_state,
        "corrupt_state": report_corrupt.artifact_state,
        "missing_classification": fk_missing.value,
        "corrupt_classification": fk_corrupt.value,
        "pass": ok,
    }


def scenario_ci_g() -> dict:
    """A genuinely failing verification classifies as verification_failure."""
    comp = "credit_card_engine"
    counts = {"generated": 100, "killed": 60, "survived": 40}
    record = _make_record(comp, exit_status=1, summary={"counts": counts})
    ctx = _context()
    report, decision = validate_and_decide(
        record, ctx, expected_artifact_bytes=_artifact_bytes(record)
    )
    fk = classify_ci_failure(record, artifact_state=report.artifact_state)
    ok = (
        fk == FailureKind.VERIFICATION
        and decision.failure_classification == "verification_failure"
        and not decision.reusable
    )
    return {
        "scenario": "CI-G",
        "name": "verification_failure",
        "expected": "classified verification_failure",
        "classification": fk.value,
        "decision_failure": decision.failure_classification,
        "pass": ok,
    }


def scenario_ci_h() -> dict:
    """Infrastructure failure classifies distinctly."""
    comp = "credit_card_engine"
    record = _make_record(
        comp,
        exit_status=-1,
        notes="runner lost power mid-job",
        summary={"counts": {}, "error": "The runner running this job lost power"},
    )
    ctx = _context()
    report, decision = validate_and_decide(
        record, ctx, expected_artifact_bytes=_artifact_bytes(record)
    )
    fk = classify_ci_failure(record, artifact_state=report.artifact_state)
    ok = (
        fk == FailureKind.INFRASTRUCTURE
        and decision.failure_classification == "infrastructure_failure"
        and not decision.reusable
    )
    return {
        "scenario": "CI-H",
        "name": "infrastructure_failure",
        "expected": "classified infrastructure_failure (machine-readable distinction)",
        "classification": fk.value,
        "decision_failure": decision.failure_classification,
        "distinct_from_verification": fk != FailureKind.VERIFICATION,
        "pass": ok,
    }


def main() -> int:
    results = [
        scenario_ci_a(),
        scenario_ci_b(),
        scenario_ci_c(),
        scenario_ci_d(),
        scenario_ci_e(),
        scenario_ci_f(),
        scenario_ci_g(),
        scenario_ci_h(),
    ]
    out = OUT_DIR / "m9-c42.29-scenarios.json"
    out.write_text(json.dumps(results, indent=2))

    passed = sum(1 for r in results if r["pass"])
    print(f"C42.29 CI scenarios: {passed}/{len(results)} pass")
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  [{status}] {r['scenario']} — {r['name']}")

    # M29.2 — persist the binding inventory alongside.
    bindings = build_ci_bindings()
    ver = verification_bindings(bindings)
    inv = {
        "total_steps_considered": len(bindings),
        "verification_bindings": len(ver),
        "non_verification_steps": len(bindings) - len(ver),
        "bindings": [b.to_dict() for b in bindings],
    }
    (OUT_DIR / "m9-c42.29-ci-binding-inventory.json").write_text(
        json.dumps(inv, indent=2)
    )
    print(f"Binding inventory: {len(ver)} verification bindings "
          f"of {len(bindings)} considered steps")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
