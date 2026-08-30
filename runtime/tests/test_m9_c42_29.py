"""
M9-C42.29 — Test suite for CI Evidence Fingerprinting & Correlation.

Covers:
  M29.1 — canonical CI evidence contract (fields, identity stability)
  M29.2 — CI → Verification Graph binding with documented derivations
  M29.3 — deterministic fingerprint validation (all 8 drift kinds,
          green-≠-reusable rule)
  M29.4 — ingestion into the canonical local representation
  M29.5 — local/CI semantic equivalence
  Scenario coverage CI-A … CI-H via the scenario harness

Run with:
    .venv/bin/python -m pytest runtime/tests/test_m9_c42_29.py -v
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification.ci_evidence import (  # noqa: E402
    CI_EVIDENCE_SCHEMA,
    DRIFT_KINDS,
    EQUIVALENCE_DIMENSIONS,
    CIEvidenceRecord,
    CIRepositoryContext,
    FailureKind,
    bind_into_graph,
    build_ci_bindings,
    ci_measurement,
    classify_ci_failure,
    ingest_ci_evidence,
    load_ci_evidence,
    resolve_command_semantics,
    save_ci_evidence,
    semantic_equivalence,
    validate_and_decide,
    validate_ci_evidence,
    verification_bindings,
)
from runtime.foundation.verification.executor_pipeline import (  # noqa: E402
    TaskFingerprints,
    collect_repo_fingerprints,
)
from runtime.foundation.verification.graph_model import VerificationGraph

_FP_CACHE: dict[str, TaskFingerprints] = {}


def _fps(component: str) -> TaskFingerprints:
    if component not in _FP_CACHE:
        _FP_CACHE[component] = collect_repo_fingerprints(component)
    return _FP_CACHE[component]


def _record(
    component: str | None = "credit_card_engine",
    *,
    sha: str = "084359346b3b",
    exit_status: int = 0,
    evidence_kind: str = "mutation-summary",
    task: str = "task::mutation::targeted",
    mode: str = "targeted",
    test_fp: str | None = None,
    cfg_fp: str | None = None,
    tool_fp: str | None = None,
    artifact_bytes: bytes | None = b"{}",
) -> CIEvidenceRecord:
    fps = _fps("credit_card_engine")
    ab = artifact_bytes if artifact_bytes is not None else b""
    return CIEvidenceRecord(
        record_id="ci-test-record",
        repository_sha=sha,
        workflow="mutation.yml",
        job="mutation",
        step="run",
        verification_task=task,
        component=component,
        capability="credit-card-risk" if component else None,
        evidence_kind=evidence_kind,
        execution_mode=mode,  # type: ignore[arg-type]
        source_fingerprint=fps.source if component else "",
        test_fingerprint=test_fp if test_fp is not None else fps.test,
        configuration_fingerprint=(
            cfg_fp
            if cfg_fp is not None
            else (fps.config if evidence_kind.startswith("mutation") else "")
        ),
        toolchain_fingerprint=tool_fp if tool_fp is not None else fps.toolchain,
        population_fingerprint="pop-fp",
        evidence_artifact_fingerprint=(
            hashlib.sha256(ab).hexdigest() if artifact_bytes is not None else ""
        ),
        artifact_path="",
        started_at="2026-08-26T00:00:00+00:00",
        ended_at="2026-08-26T00:01:00+00:00",
        exit_status=exit_status,
        failure_classification=None,
        summary={"counts": {"generated": 10, "killed": 8}},
    )


def _ctx(**kw) -> CIRepositoryContext:
    base_src = {c: _fps(c).source for c in ("credit_card_engine", "loan_engine")}
    base_tst = {c: _fps(c).test for c in ("credit_card_engine", "loan_engine")}
    defaults: dict[str, Any] = {
        "repository_sha": "084359346b3b",
        "component_source_fingerprints": base_src,
        "component_test_fingerprints": base_tst,
        "configuration_fingerprint": _fps("credit_card_engine").config,
        "toolchain_fingerprint": _fps("credit_card_engine").toolchain,
        "population_fingerprint": "pop-fp",
    }
    defaults.update(kw)
    return CIRepositoryContext(**defaults)


# ---------------------------------------------------------------------------
# M29.1 — Contract
# ---------------------------------------------------------------------------


class TestCIEvidenceContract:
    def test_schema_version(self) -> None:
        assert CI_EVIDENCE_SCHEMA == "m9-ci-evidence/v1"

    def test_record_has_all_required_identity_fields(self) -> None:
        d = _record().to_dict()
        required = [
            "repository_sha",
            "workflow",
            "job",
            "step",
            "verification_task",
            "component",
            "capability",
            "evidence_kind",
            "execution_mode",
            "source_fingerprint",
            "test_fingerprint",
            "configuration_fingerprint",
            "toolchain_fingerprint",
            "population_fingerprint",
            "evidence_artifact_fingerprint",
            "started_at",
            "ended_at",
            "exit_status",
            "failure_classification",
            "certification_disposition",
        ]
        missing = [k for k in required if k not in d]
        assert not missing, f"missing fields: {missing}"

    def test_roundtrip_preserves_identity(self) -> None:
        r = _record()
        r2 = CIEvidenceRecord.from_dict(r.to_dict())
        assert r.fingerprint() == r2.fingerprint()

    def test_identity_changes_with_each_semantic_field(self) -> None:
        base = _record()
        variants = [
            ("repository_sha", "different"),
            ("workflow", "other.yml"),
            ("evidence_kind", "test-report"),
            ("execution_mode", "authoritative"),
            ("source_fingerprint", "zzz"),
            ("exit_status", 1),
            ("failure_classification", "verification_failure"),
        ]
        for field, value in variants:
            d = base.to_dict()
            d[field] = value
            mutated = CIEvidenceRecord.from_dict(d)
            assert mutated.fingerprint() != base.fingerprint(), field

    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        records = [_record(), _record("loan_engine")]
        p = save_ci_evidence(records, tmp_path / "ci.json")
        loaded = load_ci_evidence(p)
        assert [r.fingerprint() for r in loaded] == [r.fingerprint() for r in records]


# ---------------------------------------------------------------------------
# M29.2 — Graph binding
# ---------------------------------------------------------------------------


class TestGraphBinding:
    def test_bindings_have_derivation_sources(self) -> None:
        bindings = verification_bindings(build_ci_bindings())
        assert bindings, "expected real workflow bindings"
        for b in bindings:
            assert b.derivation.startswith(".github/workflows/")
            assert f"#jobs.{b.job}.steps[" in b.derivation
            assert b.command, "literal command must be preserved"

    def test_target_binding_resolves_component(self) -> None:
        verification_bindings(build_ci_bindings())
        # The repo's mutation workflow does not use --target today; the
        # matcher table must still resolve one synthetically.
        from runtime.foundation.verification.ci_evidence import (
            normalize_component,
        )

        sem = resolve_command_semantics(
            ".venv/bin/python runtime/verify.py mutation --target credit_card --json"
        )
        assert sem is not None
        assert sem.scope == "component"
        assert sem.execution_mode == "targeted"
        assert normalize_component("credit_card") == "credit_card_engine"

    def test_smoke_is_observational_not_reusable(self) -> None:
        sem = resolve_command_semantics("python runtime/verify.py mutation --smoke")
        assert sem is not None
        assert sem.reusable_evidence is False
        assert sem.scope == "infra_health"

    def test_non_verification_commands_resolve_to_none(self) -> None:
        for cmd in (
            "actions/checkout@v4",
            "pip install -e '.[all]'",
            "docker compose up -d",
            "echo done",
        ):
            assert resolve_command_semantics(cmd) is None, cmd

    def test_bind_into_graph_adds_tasks_and_edges(self) -> None:
        g = VerificationGraph()
        g.add_capability(
            __import__(
                "runtime.foundation.verification.graph_model",
                fromlist=["CapabilityNode"],
            ).CapabilityNode(
                id="cap::credit-card-risk",
                name="Credit Card Risk",
                layer="domain",
            )
        )
        bindings = verification_bindings(build_ci_bindings())
        g2 = bind_into_graph(g, bindings)
        ci_tasks = [
            t for t in g2.tasks.values() if t.metadata.get("origin") == "ci-binding"
        ]
        assert ci_tasks, "CI tasks must be bound into the graph"
        # No duplication on rebind.
        count_before = len(g2.tasks)
        g2 = bind_into_graph(g2, bindings)
        assert len(g2.tasks) == count_before


# ---------------------------------------------------------------------------
# M29.3 — Fingerprint validation + reuse decision
# ---------------------------------------------------------------------------


class TestFingerprintValidation:
    def test_intact_record_is_reusable(self) -> None:
        report, decision = validate_and_decide(
            _record(), _ctx(), expected_artifact_bytes=b"{}"
        )
        assert not report.drifts
        assert decision.reusable
        assert decision.disposition == "reusable"

    def test_repository_drift_detected(self) -> None:
        report = validate_ci_evidence(_record(), _ctx(repository_sha="ffffff"))
        assert any(d.drift_kind == "repository_drift" for d in report.drifts)

    def test_source_drift_invalidates_only_component(self) -> None:
        ctx = _ctx(
            component_source_fingerprints={
                "credit_card_engine": "CHANGED",
                "loan_engine": _fps("loan_engine").source,
            }
        )
        _, dec = validate_and_decide(_record(), ctx, expected_artifact_bytes=b"{}")
        assert dec.disposition == "invalidated_component"
        assert not dec.reusable

    def test_green_is_not_sufficient_for_reuse(self) -> None:
        # Green workflow + source drift must still NOT be reusable.
        ctx = _ctx(
            component_source_fingerprints={
                "credit_card_engine": "CHANGED",
                "loan_engine": _fps("loan_engine").source,
            }
        )
        record = _record(exit_status=0)
        report, dec = validate_and_decide(record, ctx, expected_artifact_bytes=b"{}")
        assert report.exit_status == 0
        assert not dec.reusable

    def test_configuration_drift_scoped_to_config_dependent_evidence(self) -> None:
        ctx = _ctx(configuration_fingerprint="NEWCONFIG")
        _, dec_mut = validate_and_decide(_record(), ctx, expected_artifact_bytes=b"{}")
        assert not dec_mut.reusable
        # A behavioral suite record without config semantics stays valid.
        suite = _record(
            component=None,
            evidence_kind="test-report",
            task="task::unit::backend-suite",
            mode="observational",
            test_fp="",
            cfg_fp="",
            artifact_bytes=None,
        )
        report_suite, dec_suite = validate_and_decide(suite, ctx)
        assert not any(
            d.drift_kind == "configuration_drift" for d in report_suite.drifts
        )
        assert dec_suite.disposition == "reusable"

    def test_toolchain_drift_triggers_rcfg002(self) -> None:
        ctx = _ctx(toolchain_fingerprint="mutmut-99")
        report, dec = validate_and_decide(_record(), ctx, expected_artifact_bytes=b"{}")
        assert "R-CFG-002" in {d.rule_id for d in report.drifts}
        assert not dec.reusable

    def test_missing_artifact_is_corruption_drift(self) -> None:
        rec_d = _record(artifact_bytes=None).to_dict()
        rec_d["artifact_path"] = "runtime/generated/nope.json"
        rec = CIEvidenceRecord.from_dict(rec_d)
        report, dec = validate_and_decide(rec, _ctx())
        assert report.artifact_state == "missing"
        assert any(d.drift_kind == "artifact_corruption" for d in report.drifts)
        assert not dec.reusable

    def test_checksum_mismatch_is_corrupt(self) -> None:
        report, dec = validate_and_decide(
            _record(), _ctx(), expected_artifact_bytes=b"TAMPERED"
        )
        assert report.artifact_state == "corrupt"
        assert not dec.reusable

    def test_all_drift_kinds_enumerated(self) -> None:
        assert len(DRIFT_KINDS) == 8


class TestFailureClassification:
    def test_verification_failure_distinct_from_infrastructure(self) -> None:
        rec_v = _record(exit_status=1)
        rec_i = _record(exit_status=-1, artifact_bytes=None)
        rec_i_d = rec_i.to_dict()
        rec_i_d["notes"] = "runner lost power"
        rec_i = CIEvidenceRecord.from_dict(rec_i_d)
        assert classify_ci_failure(rec_v, artifact_state="present") == (
            FailureKind.VERIFICATION
        )
        assert classify_ci_failure(rec_i, artifact_state="present") == (
            FailureKind.INFRASTRUCTURE
        )

    def test_artifact_problems_are_evidence_failures(self) -> None:
        rec = _record(exit_status=1)
        assert classify_ci_failure(rec, artifact_state="missing") == (
            FailureKind.EVIDENCE
        )
        assert classify_ci_failure(rec, artifact_state="corrupt") == (
            FailureKind.EVIDENCE
        )


# ---------------------------------------------------------------------------
# M29.4 — Ingestion
# ---------------------------------------------------------------------------


class TestIngestion:
    def test_ingested_record_is_canonical_execution_evidence(self) -> None:
        record = _record()
        report, decision = validate_and_decide(
            record, _ctx(), expected_artifact_bytes=b"{}"
        )
        ev = ingest_ci_evidence(record, decision=decision)
        assert ev.component == "credit_card_engine"
        assert ev.failure_kind is None
        assert ev.repository_sha == record.repository_sha
        assert ev.source_fingerprint == record.source_fingerprint
        assert ev.notes.startswith("ingested from CI")

    def test_ingested_failure_keeps_classification(self) -> None:
        record = _record(exit_status=1)
        ev = ingest_ci_evidence(record)
        assert ev.failure_kind == FailureKind.VERIFICATION

    def test_mutation_promotion_to_component_measurement(self) -> None:
        record = _record()
        m = ci_measurement(record, population_id="pop-14-c42.26")
        assert m is not None
        assert m.component == "credit_card_engine"
        assert m.summary["scored"] == 10
        assert m.summary["killed"] == 8

    def test_non_mutation_records_do_not_promote(self) -> None:
        record = _record(evidence_kind="test-report")
        assert ci_measurement(record, population_id="pop") is None


# ---------------------------------------------------------------------------
# M29.5 — Semantic equivalence
# ---------------------------------------------------------------------------


class TestSemanticEquivalence:
    def _pair(self):
        record = _record()
        ingested = ingest_ci_evidence(record)
        local = ingest_ci_evidence(record)  # same canonical shape locally
        return local, record, ingested

    def test_equivalent_pair_passes_all_dimensions(self) -> None:
        local, record, ingested = self._pair()
        rep = semantic_equivalence(local, record, ingested)
        assert rep.semantically_equivalent
        assert {d.dimension for d in rep.dimensions} == set(EQUIVALENCE_DIMENSIONS)

    def test_result_divergence_breaks_equivalence(self) -> None:
        local, record, ingested = self._pair()
        failed = ingest_ci_evidence(_record(exit_status=1))
        rep = semantic_equivalence(local, record, failed)
        assert not rep.semantically_equivalent
        result_dim = next(d for d in rep.dimensions if d.dimension == "result")
        assert not result_dim.equivalent

    def test_validity_dimension_tracks_repository_sha(self) -> None:
        local, record, ingested = self._pair()
        drifted = ingest_ci_evidence(_record(sha="deadbeef"))
        rep = semantic_equivalence(local, record, drifted)
        validity = next(d for d in rep.dimensions if d.dimension == "validity")
        assert not validity.equivalent


# ---------------------------------------------------------------------------
# Scenario harness integration (CI-A … CI-H)
# ---------------------------------------------------------------------------

_SCENARIO_RESULTS: list[dict] | None = None


def _scenario_results() -> list[dict]:
    global _SCENARIO_RESULTS
    if _SCENARIO_RESULTS is None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "m29_6_scenarios",
            REPO_ROOT / "runtime/generated/m9-c42.29/m29_6_scenarios.py",
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        _SCENARIO_RESULTS = [
            mod.scenario_ci_a(),
            mod.scenario_ci_b(),
            mod.scenario_ci_c(),
            mod.scenario_ci_d(),
            mod.scenario_ci_e(),
            mod.scenario_ci_f(),
            mod.scenario_ci_g(),
            mod.scenario_ci_h(),
        ]
    return _SCENARIO_RESULTS


class TestScenarioHarness:
    def test_ci_a_unchanged_reusable(self) -> None:
        s = _scenario_results()[0]
        assert s["pass"] and s["disposition"] == "reusable"

    def test_ci_b_source_change_scope(self) -> None:
        s = _scenario_results()[1]
        assert s["pass"]
        assert s["changed_disposition"] == "invalidated_component"
        assert s["unchanged_disposition"] == "reusable"

    def test_ci_c_test_change_keeps_intact_mutation_evidence(self) -> None:
        s = _scenario_results()[2]
        assert s["pass"]
        assert s["mutation_reusable"]
        assert s["suite_test_drift_detected"]

    def test_ci_d_config_change_exact_scope(self) -> None:
        s = _scenario_results()[3]
        assert s["pass"]
        assert not s["suite_config_drift"]

    def test_ci_e_toolchain_hierarchy(self) -> None:
        s = _scenario_results()[4]
        assert s["pass"] and "R-CFG-002" in s["rule_ids"]

    def test_ci_f_evidence_failure_not_verification(self) -> None:
        s = _scenario_results()[5]
        assert s["pass"]
        assert s["missing_classification"] == "evidence_failure"
        assert s["corrupt_classification"] == "evidence_failure"

    def test_ci_g_verification_failure(self) -> None:
        s = _scenario_results()[6]
        assert s["pass"]
        assert s["classification"] == "verification_failure"

    def test_ci_h_infrastructure_failure(self) -> None:
        s = _scenario_results()[7]
        assert s["pass"]
        assert s["classification"] == "infrastructure_failure"
