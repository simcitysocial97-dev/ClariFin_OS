"""
M9-C42.30 — Test suite for the Diagnostic & Forensic Agent.

Covers:
  * ForensicExecutionRecord causal-chain validation (no silent stages)
  * Canonicalization (explicit emptiness markers)
  * The nine canonical diagnostic questions
  * Verdict taxonomy (CERTIFIABLE / NOT_CERTIFIABLE /
    CERTIFICATION_BLOCKED / INSUFFICIENT_EVIDENCE)
  * Failure-classification distinctions (incl. mixed kinds)
  * First-class uncertainty (equivalent mutant, insufficient surface,
    nondeterministic, drift, incomplete CI evidence)
  * Deterministic conclusions (identical input -> identical decision)
  * Explainability completeness

Run with:
    .venv/bin/python -m pytest runtime/tests/test_m9_c42_30.py -v
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

from runtime.foundation.verification.diagnostic_agent import (  # noqa: E402
    CAUSAL_CHAIN_STAGES,
    DIAGNOSTIC_REPORT_SCHEMA,
    UNCERTAINTY_KINDS,
    DiagnosticForensicAgent,
    canonicalize_forensic_record,
    validate_forensic_record,
)

_HARNESS = None


def _harness():
    global _HARNESS
    if _HARNESS is None:
        spec = importlib.util.spec_from_file_location(
            "m30_9_scenarios",
            REPO_ROOT / "runtime/generated/m9-c42.30/m30_9_scenarios.py",
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        _HARNESS = mod
    return _HARNESS


@pytest.fixture(scope="module")
def agent() -> DiagnosticForensicAgent:
    return DiagnosticForensicAgent()


# ---------------------------------------------------------------------------
# Record validation + canonicalization
# ---------------------------------------------------------------------------


class TestRecordValidation:
    def test_canonical_record_is_complete(self) -> None:
        _, _, _, _, forensic = _harness()._run_pipeline(
            ("backend/src/engines/credit_card_engine/risk.py",),
            fresh_outcomes={"credit_card_engine": {"outcome": "pass"}},
        )
        canonical = canonicalize_forensic_record(forensic.to_dict())
        validation = validate_forensic_record(canonical)
        assert validation.complete

    def test_all_causal_chain_stages_enumerated(self) -> None:
        assert len(CAUSAL_CHAIN_STAGES) == 12
        assert "certification_decision" in CAUSAL_CHAIN_STAGES

    def test_missing_stage_detected(self) -> None:
        record = {"record_id": "x", "change": {"changed_files": ["a.py"]}}
        validation = validate_forensic_record(record)
        assert not validation.complete
        assert "certification_decision" in validation.missing

    def test_silent_empty_stage_detected(self) -> None:
        record: dict[str, Any] = {stage: {} for stage in CAUSAL_CHAIN_STAGES}
        record["record_id"] = "x"
        validation = validate_forensic_record(record)
        assert not validation.complete
        assert "failures" in validation.silently_empty

    def test_explicit_emptiness_marker_accepted(self) -> None:
        record: dict[str, Any] = {
            stage: {"empty_because": "nothing happened"}
            for stage in CAUSAL_CHAIN_STAGES
        }
        record["record_id"] = "x"
        validation = validate_forensic_record(record)
        assert validation.complete
        assert not validation.silently_empty

    def test_canonicalization_does_not_mutate_input(self) -> None:
        record: dict[str, Any] = {
            stage: {} for stage in ("change", "failures", "uncertainties")
        }
        frozen = json.dumps(record, sort_keys=True)
        canonicalize_forensic_record(record)
        assert json.dumps(record, sort_keys=True) == frozen


# ---------------------------------------------------------------------------
# Nine questions + verdicts (via scenario pipeline)
# ---------------------------------------------------------------------------


class TestNineQuestions:
    def test_all_nine_answered_for_source_change(self, agent) -> None:
        plan, _, fresh, reconciled, forensic = _harness()._run_pipeline(
            ("backend/src/engines/credit_card_engine/risk.py",),
            fresh_outcomes={"credit_card_engine": {"outcome": "pass"}},
        )
        report = agent.diagnose(forensic.to_dict())
        assert report.schema == DIAGNOSTIC_REPORT_SCHEMA
        # Q1 — what changed
        assert report.q1_what_changed["file_count"] == 1
        assert report.q1_what_changed["files_by_kind"]["source"]
        # Q2 — what is affected
        assert report.q2_what_is_affected["components"] == ["credit_card"]
        # Q3 — valid evidence
        q3 = report.q3_valid_evidence
        assert len(q3["reused"]) == 13
        assert "credit_card_engine" in q3["revalidated"]
        # Q4 — planner authority
        assert "never invents scope" in report.q4_required_execution["authority"]
        assert report.q4_required_execution["required_tasks"] == ["credit_card_engine"]
        # Q5 — actual execution
        assert report.q5_actual_execution["executed"] == ["credit_card_engine"]
        assert not report.q5_actual_execution["failed"]
        # Q6 — outcomes classified
        assert report.q6_what_happened["by_kind"] == {}
        # Q7 — what was NOT tested
        q7 = report.q7_what_was_not_tested
        assert len(q7["covered_by_reused_evidence"]) == 13
        # Q8 — uncertainties first-class
        assert isinstance(report.q8_uncertainties, tuple)
        # Q9 — verdict with rationale
        assert report.q9_verdict["verdict"] == "CERTIFIABLE"
        assert report.q9_verdict["rationale"]

    def test_explainability_completeness(self, agent) -> None:
        _, _, _, _, forensic = _harness()._run_pipeline(())
        report = agent.diagnose(forensic.to_dict())
        ex = report.explainability.to_dict()
        required = [
            "why_did_you_run_this",
            "why_did_you_not_run_that",
            "which_evidence_did_you_reuse",
            "why_was_that_evidence_still_valid",
            "what_evidence_became_invalid",
            "what_failed",
            "was_the_failure_actually_a_verification_failure",
            "what_remains_unverified",
            "what_prevents_certification",
        ]
        for key in required:
            assert key in ex and ex[key], key
        # No-change: nothing ran because everything was reusable.
        assert "nothing required execution" in ex["why_did_you_run_this"]

    def test_uncertainty_taxonomy_closed(self) -> None:
        assert set(UNCERTAINTY_KINDS) == {
            "nondeterministic_mutation",
            "equivalent_mutant",
            "insufficient_test_surface",
            "stale_evidence",
            "incomplete_ci_evidence",
            "unmapped_capability",
            "ambiguous_behavior",
        }


class TestVerdicts:
    def test_no_change_certifiable_with_derived_aggregate(self, agent) -> None:
        r = _harness().scenario_fa()
        assert r["pass"]
        assert r["aggregate_label"] == "MATHEMATICALLY_RECONCILED"

    def test_discovery_drift_blocks(self, agent) -> None:
        r = _harness().scenario_ff()
        assert r["verdict"] == "CERTIFICATION_BLOCKED"

    def test_infrastructure_failure_insufficient_not_verification(self, agent) -> None:
        r = _harness().scenario_fe()
        assert r["pass"]
        assert r["by_kind"]["infrastructure_failure"] == ["account_engine"]

    def test_verification_failure_not_certifiable(self, agent) -> None:
        plan, _, fresh, reconciled, forensic = _harness()._run_pipeline(
            ("backend/src/engines/loan_engine/schedule.py",),
            fresh_outcomes={"loan_engine": {"outcome": "verification_failure"}},
        )
        report = agent.diagnose(forensic.to_dict())
        assert report.q9_verdict["verdict"] == "NOT_CERTIFIABLE"


class TestUncertaintyDetection:
    def test_behavioral_gap_diagnosed_without_score_chasing(self, agent) -> None:
        r = _harness().scenario_fg()
        assert r["pass"]
        for gap in r["gaps"]:
            assert gap["kind"] == "insufficient_test_surface"
            assert gap["gates_certification"] is False
            assert "strengthening" in gap["recommendation"]

    def test_equivalent_mutant_preserved_not_targeted(self, agent) -> None:
        r = _harness().scenario_fh()
        assert r["pass"]
        for eq in r["equivalent"]:
            assert eq["gates_certification"] is False
            assert "do not target" in eq["recommendation"].lower()

    def test_incomplete_ci_evidence_recorded(self, agent) -> None:
        _, _, _, _, forensic = _harness()._run_pipeline(())
        ci_correlation = {
            "records": [
                {
                    "record_id": "ci-broken-artifact",
                    "component": None,
                    "executed": True,
                    "reusable": False,
                    "failure_classification": "evidence_failure",
                    "reasons": ["artifact state=missing; evidence_failure"],
                }
            ]
        }
        report = agent.diagnose(forensic.to_dict(), ci_correlation=ci_correlation)
        kinds = [u.kind for u in report.q8_uncertainties]
        assert "incomplete_ci_evidence" in kinds


class TestDeterminism:
    def test_identical_input_identical_decisions(self, agent) -> None:
        _, _, _, _, forensic = _harness()._run_pipeline(
            ("backend/src/engines/balance_engine/ledger.py",),
            fresh_outcomes={"balance_engine": {"outcome": "pass"}},
        )
        r1 = agent.diagnose(forensic.to_dict())
        r2 = agent.diagnose(forensic.to_dict())
        assert r1.decision_fingerprint() == r2.decision_fingerprint()

    def test_different_input_different_decisions(self, agent) -> None:
        _, _, _, _, f1 = _harness()._run_pipeline(())
        _, _, _, _, f2 = _harness()._run_pipeline(
            ("backend/src/engines/cashflow_engine/flow.py",),
            fresh_outcomes={"cashflow_engine": {"outcome": "verification_failure"}},
        )
        r1 = agent.diagnose(f1.to_dict())
        r2 = agent.diagnose(f2.to_dict())
        assert r1.decision_fingerprint() != r2.decision_fingerprint()


# ---------------------------------------------------------------------------
# Scenario suite FA–FH
# ---------------------------------------------------------------------------


class TestScenarioSuiteFAtoFH:
    def test_full_suite_passes_and_is_deterministic(self) -> None:
        payload = (
            json.loads(
                (
                    REPO_ROOT / "runtime/generated/m9-c42.30/m9-c42.30-scenarios.json"
                ).read_text()
            )
            if (
                REPO_ROOT / "runtime/generated/m9-c42.30/m9-c42.30-scenarios.json"
            ).exists()
            else None
        )
        if payload is None:
            import subprocess

            result = subprocess.run(
                [".venv/bin/python", "runtime/generated/m9-c42.30/m30_9_scenarios.py"],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, result.stderr
            payload = json.loads(
                (
                    REPO_ROOT / "runtime/generated/m9-c42.30/m9-c42.30-scenarios.json"
                ).read_text()
            )
        scenarios = payload["scenarios"]
        assert len(scenarios) == 8
        assert all(s["pass"] for s in scenarios)
        assert payload["determinism_check_pass"] is True
