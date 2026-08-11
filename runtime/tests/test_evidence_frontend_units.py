"""Evidence Model Carries Frontend and Unit Identity (VEA-2 Phase 2, M5)

Tests for E-2 (frontend representable) and E-3 (failures keyed by verification unit).

Why these tests exist
---------------------
**E-2.** `EvidenceSummary` was backend-only: `backend.{unit_tests, property_tests,
contract_tests, coverage, mutation}`. There was no frontend field at all — the sole
occurrence of "frontend" in the aggregator was a synthesized `suggested_layer` string.
A red frontend build was *structurally unrepresentable*, which also meant it could not
force a non-pass overall status.

**E-3.** Evidence was aggregated by *artifact type*, never keyed by `VerificationUnit.id`.
The C11 provenance added in Phase 1 lives on the plan and was discarded before evidence
aggregation, so a failure could never be traced back to the impact that selected it.

The critical negative case is `not_run` vs `pass`: missing frontend evidence must never be
reported as success. A verification system that reports green when it did not look is
worse than one that reports nothing.

**E-4 boundary.** `_find_chain_for_failure()` / `_find_dependency_chain()` are the known
keyword-attribution defect owned by Phase 3. These tests assert they remain present and
uncalled by the new code path — Phase 2 must bypass them, not rebuild or extend them.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

from runtime.system.evidence.aggregator import (
    UNMAPPED_SENTINEL,
    EvidenceAggregator,
    EvidenceSummary,
)

FRONTEND_PASS = {
    "schema": "frontend-verification/v1",
    "overall_status": "pass",
    "unit_id": "frontend-typecheck-build",
    "phases": [
        {"phase": "lint", "status": "pass", "exit_code": 0, "duration_seconds": 28,
         "log": "/tmp/lint.log"},
        {"phase": "typecheck", "status": "pass", "exit_code": 0, "duration_seconds": 7,
         "log": "/tmp/typecheck.log"},
        {"phase": "build", "status": "pass", "exit_code": 0, "duration_seconds": 49,
         "log": "/tmp/build.log"},
        {"phase": "test", "status": "pass", "exit_code": 0, "duration_seconds": 104,
         "log": "/tmp/test.log"},
    ],
}

FRONTEND_BUILD_FAILED = {
    "schema": "frontend-verification/v1",
    "overall_status": "fail",
    "unit_id": "frontend-typecheck-build",
    "phases": [
        {"phase": "lint", "status": "pass", "exit_code": 0, "duration_seconds": 28,
         "log": "/tmp/lint.log"},
        {"phase": "typecheck", "status": "pass", "exit_code": 0, "duration_seconds": 7,
         "log": "/tmp/typecheck.log"},
        {"phase": "build", "status": "fail", "exit_code": 1, "duration_seconds": 19,
         "log": "/tmp/build.log"},
        {"phase": "test", "status": "pass", "exit_code": 0, "duration_seconds": 103,
         "log": "/tmp/test.log"},
    ],
}

MANIFEST = {
    "schema": "run-manifest/v1",
    "commit": "b9074020",
    "branch": "recovery/program-r-forensic-reconstruction",
    "steps": [
        {
            "step_id": "step-0001",
            "unit_id": "frontend-typecheck-build",
            "contributing_units": ["frontend-typecheck-build", "frontend-unit"],
            "command": "bash .github/scripts/run_frontend_verification.sh",
            "workflow": "frontend",
            "exit_code": 1,
            "status": "failed",
            "provenance": {
                "capabilities": ["capability:useLoansCapability"],
                "impact_kinds": ["capability", "view_model"],
                "source": "chain-map+blast-radius",
            },
        }
    ],
    "unmapped": [],
}


def _write_evidence(
    root: Path,
    frontend: dict | None = None,
    manifest: dict | None = None,
    backend: dict | None = None,
) -> Path:
    """Build an evidence directory the aggregator can consume."""
    evidence = root / "runtime/generated/evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    if frontend is not None:
        (evidence / "frontend").mkdir(exist_ok=True)
        (evidence / "frontend" / "frontend-verification.json").write_text(
            json.dumps(frontend)
        )
    if manifest is not None:
        (evidence / "run-manifest.json").write_text(json.dumps(manifest))
    if backend is not None:
        (evidence / "backend").mkdir(exist_ok=True)
        (evidence / "backend" / "backend-verification.json").write_text(
            json.dumps(backend)
        )
    return evidence


def _aggregate(root: Path, evidence: Path) -> EvidenceSummary:
    return EvidenceAggregator(root).aggregate(evidence)


class TestFrontendIsRepresentable:
    """E-2 — the frontend must exist in the model at all."""

    def test_summary_has_a_frontend_field(self):
        assert "frontend" in EvidenceSummary().__dataclass_fields__

    def test_frontend_defaults_to_empty_not_pass(self):
        assert EvidenceSummary().frontend == {}

    def test_frontend_phases_are_populated_from_evidence(self, tmp_path: Path):
        evidence = _write_evidence(tmp_path, frontend=FRONTEND_PASS)
        summary = _aggregate(tmp_path, evidence)

        assert summary.frontend["overall_status"] == "pass"
        assert set(summary.frontend["phases"]) == {
            "lint",
            "typecheck",
            "build",
            "test",
        }

    def test_each_phase_carries_status_exit_code_and_duration(self, tmp_path: Path):
        evidence = _write_evidence(tmp_path, frontend=FRONTEND_PASS)
        summary = _aggregate(tmp_path, evidence)
        build = summary.frontend["phases"]["build"]
        assert build["status"] == "pass"
        assert build["exit_code"] == 0
        assert build["duration_seconds"] == 49

    def test_frontend_appears_in_markdown_report(self, tmp_path: Path):
        evidence = _write_evidence(tmp_path, frontend=FRONTEND_BUILD_FAILED)
        markdown = _aggregate(tmp_path, evidence).to_markdown()
        assert "### Frontend" in markdown
        assert "build" in markdown


class TestFrontendFailureForcesNonPass:
    """M5.3 — a red frontend build cannot report `pass`."""

    def test_build_failure_is_visible_in_the_summary(self, tmp_path: Path):
        evidence = _write_evidence(tmp_path, frontend=FRONTEND_BUILD_FAILED)
        summary = _aggregate(tmp_path, evidence)
        assert summary.frontend["phases"]["build"]["status"] == "fail"

    def test_build_failure_forces_non_pass_overall(self, tmp_path: Path):
        evidence = _write_evidence(tmp_path, frontend=FRONTEND_BUILD_FAILED)
        summary = _aggregate(tmp_path, evidence)
        assert summary.overall_status != "pass"
        assert summary.overall_status == "attention_needed"

    def test_frontend_failure_raises_attention(self, tmp_path: Path):
        evidence = _write_evidence(tmp_path, frontend=FRONTEND_BUILD_FAILED)
        summary = _aggregate(tmp_path, evidence)
        types = {item["type"] for item in summary.attention_needed}
        assert "frontend_verification_failed" in types

    def test_attention_names_the_failing_phase(self, tmp_path: Path):
        evidence = _write_evidence(tmp_path, frontend=FRONTEND_BUILD_FAILED)
        summary = _aggregate(tmp_path, evidence)
        item = next(
            i
            for i in summary.attention_needed
            if i["type"] == "frontend_verification_failed"
        )
        assert "build" in item["details"]

    def test_all_green_frontend_does_not_raise_attention(self, tmp_path: Path):
        """Guards over-correction: a passing frontend must not be flagged."""
        evidence = _write_evidence(tmp_path, frontend=FRONTEND_PASS)
        summary = _aggregate(tmp_path, evidence)
        types = {item["type"] for item in summary.attention_needed}
        assert "frontend_verification_failed" not in types


class TestMissingFrontendEvidenceIsNotRun:
    """NEGATIVE TEST — missing evidence yields `not_run`, never `pass`."""

    def test_no_evidence_at_all_is_not_run(self, tmp_path: Path):
        evidence = tmp_path / "runtime/generated/evidence"
        evidence.mkdir(parents=True)
        summary = EvidenceAggregator(tmp_path).aggregate(evidence)
        assert summary.overall_status == "not_run"

    def test_missing_frontend_evidence_leaves_frontend_empty(self, tmp_path: Path):
        evidence = tmp_path / "runtime/generated/evidence"
        evidence.mkdir(parents=True)
        summary = EvidenceAggregator(tmp_path).aggregate(evidence)
        assert summary.frontend == {}

    def test_missing_frontend_is_never_reported_as_pass(self, tmp_path: Path):
        evidence = tmp_path / "runtime/generated/evidence"
        evidence.mkdir(parents=True)
        summary = EvidenceAggregator(tmp_path).aggregate(evidence)
        assert summary.frontend.get("overall_status") != "pass"

    def test_corrupt_frontend_evidence_is_not_silently_passed(self, tmp_path: Path):
        evidence = tmp_path / "runtime/generated/evidence"
        (evidence / "frontend").mkdir(parents=True)
        (evidence / "frontend" / "frontend-verification.json").write_text("{not json")
        summary = EvidenceAggregator(tmp_path).aggregate(evidence)
        assert summary.frontend == {}
        assert summary.overall_status != "pass"


class TestUnitKeyedFailures:
    """E-3 — failures joinable to units and provenance."""

    def test_summary_has_a_unit_failures_field(self):
        assert "unit_failures" in EvidenceSummary().__dataclass_fields__

    def test_frontend_failure_is_keyed_by_unit(self, tmp_path: Path):
        evidence = _write_evidence(
            tmp_path, frontend=FRONTEND_BUILD_FAILED, manifest=MANIFEST
        )
        summary = _aggregate(tmp_path, evidence)
        assert len(summary.unit_failures) == 1
        assert summary.unit_failures[0]["unit_id"] == "frontend-typecheck-build"

    def test_failure_carries_phase_path_and_diagnostic(self, tmp_path: Path):
        evidence = _write_evidence(
            tmp_path, frontend=FRONTEND_BUILD_FAILED, manifest=MANIFEST
        )
        failure = _aggregate(tmp_path, evidence).unit_failures[0]
        assert failure["phase"] == "build"
        assert failure["path"] == "/tmp/build.log"
        assert "build" in failure["diagnostic"]

    def test_failure_carries_provenance_end_to_end(self, tmp_path: Path):
        """The C11 provenance must survive all the way into evidence."""
        evidence = _write_evidence(
            tmp_path, frontend=FRONTEND_BUILD_FAILED, manifest=MANIFEST
        )
        provenance = _aggregate(tmp_path, evidence).unit_failures[0]["provenance"]
        assert provenance["source"] == "chain-map+blast-radius"
        assert provenance["capabilities"] == ["capability:useLoansCapability"]
        assert provenance["impact_kinds"] == ["capability", "view_model"]

    def test_failure_records_all_contributing_units(self, tmp_path: Path):
        evidence = _write_evidence(
            tmp_path, frontend=FRONTEND_BUILD_FAILED, manifest=MANIFEST
        )
        failure = _aggregate(tmp_path, evidence).unit_failures[0]
        assert failure["contributing_units"] == [
            "frontend-typecheck-build",
            "frontend-unit",
        ]

    def test_passing_phases_produce_no_failure_records(self, tmp_path: Path):
        evidence = _write_evidence(
            tmp_path, frontend=FRONTEND_PASS, manifest=MANIFEST
        )
        assert _aggregate(tmp_path, evidence).unit_failures == []

    def test_backend_phase_failure_is_keyed_by_unit(self, tmp_path: Path):
        backend = {
            "schema": "backend-verification/v1",
            "overall_status": "fail",
            "unit_id": "backend-unit",
            "phases": [
                {"phase": "contract", "status": "pass", "exit_code": 0,
                 "duration_seconds": 20, "log": "/tmp/c.log"},
                {"phase": "invariants", "status": "fail", "exit_code": 1,
                 "duration_seconds": 20, "log": "/tmp/i.log"},
            ],
        }
        evidence = _write_evidence(tmp_path, backend=backend, manifest=MANIFEST)
        failures = _aggregate(tmp_path, evidence).unit_failures
        assert len(failures) == 1
        assert failures[0]["unit_id"] == "backend-unit"
        assert failures[0]["layer"] == "backend"
        assert failures[0]["phase"] == "invariants"

    def test_unjoinable_failure_is_unmapped_not_guessed(self, tmp_path: Path):
        """UNKNOWN over GUESSED — no manifest means no unit, not a borrowed one."""
        frontend = dict(FRONTEND_BUILD_FAILED)
        frontend["unit_id"] = ""
        evidence = _write_evidence(tmp_path, frontend=frontend)  # no manifest
        failure = _aggregate(tmp_path, evidence).unit_failures[0]
        assert failure["unit_id"] == UNMAPPED_SENTINEL

    def test_unrelated_manifest_entry_is_never_borrowed(self, tmp_path: Path):
        """E-4 GUARD — the exact defect class this phase exists to avoid.

        `_find_chain_for_failure()` returned the *first* chain-map entry regardless of
        which test failed. The equivalent bug here would be joining a frontend failure
        to whatever unit happens to appear first in the manifest.

        Here the manifest contains only a *backend* step. The frontend failure must
        resolve to UNMAPPED, not silently inherit `backend-unit`.
        """
        frontend = dict(FRONTEND_BUILD_FAILED)
        frontend["unit_id"] = ""
        backend_only_manifest = {
            "schema": "run-manifest/v1",
            "steps": [
                {
                    "step_id": "step-0001",
                    "unit_id": "backend-unit",
                    "contributing_units": ["backend-unit", "unit-targeted"],
                    "command": "bash .github/scripts/run_backend_verification.sh",
                    "workflow": "backend",
                    "exit_code": 0,
                    "status": "passed",
                    "provenance": {"source": "registry-workflow-mapping"},
                }
            ],
            "unmapped": [],
        }
        evidence = _write_evidence(
            tmp_path, frontend=frontend, manifest=backend_only_manifest
        )
        failure = _aggregate(tmp_path, evidence).unit_failures[0]
        assert failure["unit_id"] == UNMAPPED_SENTINEL, (
            "a frontend failure was attributed to a backend unit — this is the E-4 "
            "'first entry wins' defect reappearing in a new format"
        )
        assert failure["provenance"] == {}, (
            "provenance from an unrelated step must not be attached to this failure"
        )

    def test_join_is_by_workflow_not_by_position(self, tmp_path: Path):
        """Order in the manifest must not influence the join."""
        frontend = dict(FRONTEND_BUILD_FAILED)
        frontend["unit_id"] = ""
        reordered = {
            "schema": "run-manifest/v1",
            "steps": [
                {
                    "step_id": "step-0001",
                    "unit_id": "runtime-self-test",
                    "contributing_units": ["runtime-self-test"],
                    "command": "bash .github/scripts/run_runtime_verification.sh",
                    "workflow": "runtime",
                    "exit_code": 0,
                    "status": "passed",
                    "provenance": {"source": "runtime"},
                },
                MANIFEST["steps"][0],
            ],
            "unmapped": [],
        }
        evidence = _write_evidence(tmp_path, frontend=frontend, manifest=reordered)
        failure = _aggregate(tmp_path, evidence).unit_failures[0]
        assert failure["unit_id"] == "frontend-typecheck-build"
        assert failure["provenance"]["source"] == "chain-map+blast-radius"

    def test_unmapped_sentinel_matches_the_registry_sentinel(self):
        """The two sentinels must stay joinable across packages."""
        from runtime.foundation.verification.registry import UNMAPPED

        assert UNMAPPED_SENTINEL == UNMAPPED


class TestBackendAggregationUnchanged:
    """Plan M5: backend-only runs must aggregate exactly as before."""

    def test_backend_only_run_is_unaffected(self, tmp_path: Path):
        evidence = tmp_path / "runtime/generated/evidence"
        evidence.mkdir(parents=True)
        summary = EvidenceAggregator(tmp_path).aggregate(evidence)
        assert set(summary.backend) == {
            "unit_tests",
            "property_tests",
            "contract_tests",
            "coverage",
            "mutation",
        }

    def test_frontend_absence_does_not_alter_backend_section(self, tmp_path: Path):
        evidence = tmp_path / "runtime/generated/evidence"
        evidence.mkdir(parents=True)
        without = EvidenceAggregator(tmp_path).aggregate(evidence)

        evidence2 = _write_evidence(tmp_path, frontend=FRONTEND_PASS)
        with_frontend = EvidenceAggregator(tmp_path).aggregate(evidence2)

        assert without.backend == with_frontend.backend


class TestE4RemainsUntouched:
    """Plan M5 prohibits rewriting or extending the keyword-attribution defect."""

    def test_keyword_functions_still_exist(self):
        assert hasattr(EvidenceAggregator, "_find_chain_for_failure")

    def test_new_code_paths_do_not_call_the_keyword_functions(self):
        """Phase 2 must bypass E-4, not build on it."""
        for name in (
            "_collect_frontend",
            "_collect_unit_failures",
            "_load_run_manifest",
            "_frontend_evidence_path",
            "_backend_evidence_path",
        ):
            source = inspect.getsource(getattr(EvidenceAggregator, name))
            assert "_find_chain_for_failure" not in source
            assert "_find_dependency_chain" not in source

    def test_unit_failure_join_uses_manifest_not_string_matching(self):
        """The join key must come from the manifest, never from a name match."""
        source = inspect.getsource(EvidenceAggregator._collect_unit_failures)
        assert "_load_run_manifest" in source
        for banned in (".startswith(", ".endswith(", " in command", "re.search"):
            assert banned not in source, (
                f"substring/keyword matching ({banned}) reintroduces the E-4 defect"
            )


class TestSerialization:
    def test_summary_with_frontend_round_trips_to_json(self, tmp_path: Path):
        evidence = _write_evidence(
            tmp_path, frontend=FRONTEND_BUILD_FAILED, manifest=MANIFEST
        )
        summary = _aggregate(tmp_path, evidence)
        data = json.loads(summary.to_json())
        assert data["frontend"]["overall_status"] == "fail"
        assert data["unit_failures"][0]["unit_id"] == "frontend-typecheck-build"

    def test_unit_failures_appear_in_markdown(self, tmp_path: Path):
        evidence = _write_evidence(
            tmp_path, frontend=FRONTEND_BUILD_FAILED, manifest=MANIFEST
        )
        markdown = _aggregate(tmp_path, evidence).to_markdown()
        assert "Failures by Verification Unit" in markdown
        assert "frontend-typecheck-build" in markdown
