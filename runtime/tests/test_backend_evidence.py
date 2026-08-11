"""Per-Phase Structured Evidence, Keyed by Unit (VEA-2 Phase 2, M4)

Tests for the backend/frontend verification scripts' evidence contracts.

Why these tests exist
---------------------
Before M4:

* `run_backend_verification.sh` emitted a single exit code and concatenated pytest
  output. A failure could not be attributed to a suite.
* **No script anywhere in the repository emitted `--junitxml`** (except mutation), so
  `EvidenceAggregator._collect_test_results()` — which has always probed for `junit.xml`
  — never found anything. That is finding E-1.

M4 closes E-1 and generalises the frontend script's per-phase decomposition to the
backend. These tests pin the *contracts* that later milestones and CI depend on:

1. The **exit-code contract is unchanged** — 0 all-pass, 1 any-fail. Asserted in both
   directions, because a script that can only be observed passing is not verified.
2. Evidence **self-identifies** via `VERIFICATION_UNIT_ID`.
3. JUnit XML is real, parseable, and consumable by the *existing* collector — not a new
   parallel evidence system.
4. The backend suite **still runs in parallel** (plan M4: "do not serialize for
   convenience").

Scripts are validated by static contract inspection plus targeted execution, rather than
by running the full multi-minute backend suite inside the unit-test suite.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SCRIPT = REPO_ROOT / ".github/scripts/run_backend_verification.sh"
FRONTEND_SCRIPT = REPO_ROOT / ".github/scripts/run_frontend_verification.sh"

BACKEND_EVIDENCE = REPO_ROOT / "runtime/generated/evidence/backend"
FRONTEND_EVIDENCE = REPO_ROOT / "runtime/generated/evidence/frontend"

#: The four backend suite phases, in the order the script declares them.
EXPECTED_BACKEND_PHASES = ["contract", "invariants", "properties", "unit-engines"]


def _script(path: Path) -> str:
    return path.read_text()


class TestScriptsAreValid:
    def test_backend_script_is_syntactically_valid(self):
        result = subprocess.run(
            ["bash", "-n", str(BACKEND_SCRIPT)], capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr

    def test_frontend_script_is_syntactically_valid(self):
        result = subprocess.run(
            ["bash", "-n", str(FRONTEND_SCRIPT)], capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr


class TestExitCodeContract:
    """Plan M4: exit-code semantics must be unchanged."""

    def test_backend_script_exits_with_the_fail_flag(self):
        assert "exit $fail" in _script(BACKEND_SCRIPT)

    def test_frontend_script_exits_with_the_fail_flag(self):
        assert "exit $fail" in _script(FRONTEND_SCRIPT)

    def test_backend_sets_fail_on_any_nonzero_phase(self):
        source = _script(BACKEND_SCRIPT)
        assert "fail=1" in source
        assert "fail=0" in source

    def test_backend_exit_contract_holds_both_directions(self, tmp_path: Path):
        """Executes the real script twice: all-pass, then with an injected failure.

        Asserting only the passing direction would not prove the contract; a script that
        always exits 0 would satisfy it.
        """
        probe_dir = REPO_ROOT / "backend/tests/invariants/_m4_exit_probe"
        evidence = tmp_path / "evidence"

        # Direction 1: unmodified tree must pass.
        passing = subprocess.run(
            ["bash", str(BACKEND_SCRIPT)],
            capture_output=True,
            text=True,
            env={**_env(), "BACKEND_EVIDENCE_DIR": str(evidence)},
        )
        assert passing.returncode == 0, passing.stdout[-3000:]
        summary = json.loads((evidence / "backend-verification.json").read_text())
        assert summary["overall_status"] == "pass"

        # Direction 2: one failing test must produce exit 1 and a failing phase.
        probe_dir.mkdir(parents=True, exist_ok=True)
        try:
            (probe_dir / "test_m4_exit_probe.py").write_text(
                "def test_m4_probe():\n    assert False\n"
            )
            failing = subprocess.run(
                ["bash", str(BACKEND_SCRIPT)],
                capture_output=True,
                text=True,
                env={**_env(), "BACKEND_EVIDENCE_DIR": str(evidence)},
            )
            assert failing.returncode == 1
            summary = json.loads((evidence / "backend-verification.json").read_text())
            assert summary["overall_status"] == "fail"
            failed = [p for p in summary["phases"] if p["status"] == "fail"]
            assert [p["phase"] for p in failed] == ["invariants"], (
                "the failure must be attributable to exactly the suite that failed"
            )
        finally:
            shutil.rmtree(probe_dir, ignore_errors=True)


def _env() -> dict:
    import os

    return dict(os.environ)


class TestBackendPhaseDecomposition:
    def test_script_declares_all_four_suites(self):
        source = _script(BACKEND_SCRIPT)
        for tdir in (
            "tests/contract",
            "tests/invariants",
            "tests/properties",
            "tests/unit/engines",
        ):
            assert tdir in source

    def test_phase_names_are_explicitly_mapped_not_derived(self):
        """A renamed directory must fail loudly, not silently rename a phase."""
        source = _script(BACKEND_SCRIPT)
        assert "phase_name_for()" in source
        for phase in EXPECTED_BACKEND_PHASES:
            assert f'echo "{phase}"' in source

    def test_suites_still_run_in_parallel(self):
        """Plan M4: preserve parallelism; do not serialize for convenience."""
        source = _script(BACKEND_SCRIPT)
        assert "&\n" in source or "> \"$out\" 2>&1 &" in source
        assert "pids+=($!)" in source
        assert 'wait "${pids[$i]}"' in source

    def test_per_phase_exit_codes_are_collected_individually(self):
        """Collapsing into one flag is what M4 exists to undo."""
        source = _script(BACKEND_SCRIPT)
        assert "codes+=(0)" in source
        assert "codes+=($?)" in source


class TestBackendEvidenceSchema:
    @pytest.fixture(scope="class")
    def summary(self) -> dict:
        path = BACKEND_EVIDENCE / "backend-verification.json"
        if not path.exists():
            pytest.skip(
                "backend evidence not present; run run_backend_verification.sh first"
            )
        return json.loads(path.read_text())

    def test_schema_key_is_versioned(self, summary):
        assert summary["schema"] == "backend-verification/v1"

    def test_summary_lists_every_phase(self, summary):
        assert [p["phase"] for p in summary["phases"]] == EXPECTED_BACKEND_PHASES

    def test_every_phase_has_the_required_fields(self, summary):
        required = {
            "phase",
            "status",
            "exit_code",
            "duration_seconds",
            "log",
            "junit",
        }
        for phase in summary["phases"]:
            assert required <= set(phase)

    def test_status_is_consistent_with_exit_code(self, summary):
        for phase in summary["phases"]:
            expected = "pass" if phase["exit_code"] == 0 else "fail"
            assert phase["status"] == expected

    def test_overall_status_is_consistent_with_phases(self, summary):
        any_fail = any(p["status"] == "fail" for p in summary["phases"])
        assert summary["overall_status"] == ("fail" if any_fail else "pass")

    def test_evidence_self_identifies_with_unit_id(self, summary):
        assert "unit_id" in summary


class TestUnitIdPropagation:
    """M4.3 — both scripts accept VERIFICATION_UNIT_ID and record it."""

    def test_backend_script_reads_the_env_var(self):
        assert 'VERIFICATION_UNIT_ID="${VERIFICATION_UNIT_ID:-}"' in _script(
            BACKEND_SCRIPT
        )

    def test_frontend_script_reads_the_env_var(self):
        assert 'VERIFICATION_UNIT_ID="${VERIFICATION_UNIT_ID:-}"' in _script(
            FRONTEND_SCRIPT
        )

    def test_backend_writes_unit_id_into_its_summary(self):
        assert '"unit_id": "$VERIFICATION_UNIT_ID"' in _script(BACKEND_SCRIPT)

    def test_frontend_writes_unit_id_into_its_summary(self):
        assert '"unit_id": "$VERIFICATION_UNIT_ID"' in _script(FRONTEND_SCRIPT)

    def test_unset_unit_id_is_empty_not_guessed(self):
        """UNKNOWN over GUESSED: an absent unit must not be invented."""
        for script in (BACKEND_SCRIPT, FRONTEND_SCRIPT):
            assert "VERIFICATION_UNIT_ID:-}" in _script(script)


class TestJUnitEmission:
    """E-1 — the finding this milestone closes."""

    def test_backend_script_passes_junitxml_to_pytest(self):
        assert "--junitxml=" in _script(BACKEND_SCRIPT)

    def test_junit_files_exist_for_every_phase(self):
        if not BACKEND_EVIDENCE.exists():
            pytest.skip("backend evidence not present")
        for phase in EXPECTED_BACKEND_PHASES:
            path = BACKEND_EVIDENCE / f"{phase}-junit.xml"
            assert path.exists(), f"missing JUnit for phase {phase}"

    def test_junit_files_parse_as_valid_xml(self):
        if not BACKEND_EVIDENCE.exists():
            pytest.skip("backend evidence not present")
        for path in sorted(BACKEND_EVIDENCE.glob("*-junit.xml")):
            root = ET.parse(path).getroot()
            assert root.tag in {"testsuite", "testsuites"}

    def test_junit_is_parseable_by_the_existing_collector(self):
        """The point of E-1: feed the collector that always looked for junit.xml.

        Asserts the collector extracts real structure. It deliberately does **not**
        assert `failed == 0`: this file is whatever the last backend run produced, and
        pinning it to green would make the test a hostage to unrelated state. What
        matters for E-1 is that the collector now finds and parses tests at all, and
        that counts are internally consistent.
        """
        from runtime.system.evidence.collectors.test_results import (
            TestResultCollector,
        )

        merged = REPO_ROOT / "backend/tests/generated/junit.xml"
        if not merged.exists():
            pytest.skip("merged junit.xml not present")

        evidence = TestResultCollector(REPO_ROOT).collect()
        assert evidence.passed > 0, (
            "collector parsed no tests; E-1 would still be open"
        )
        assert evidence.duration_seconds > 0
        # Failure names must be reported whenever failures are counted — a count
        # without names would be unattributable evidence.
        assert len(evidence.failed_test_names) == evidence.failed

    def test_merged_junit_is_written_to_the_collector_probe_path(self):
        assert "backend/tests/generated" in _script(BACKEND_SCRIPT)


class TestFrontendEvidenceUnchangedInShape:
    """Plan M4 acceptance: frontend evidence shape must stay `frontend-verification/v1`."""

    def test_schema_key_is_unchanged(self):
        assert '"schema": "frontend-verification/v1"' in _script(FRONTEND_SCRIPT)

    def test_phases_are_unchanged(self):
        source = _script(FRONTEND_SCRIPT)
        for phase in ("lint", "typecheck", "build", "test"):
            assert f"run_phase {phase}" in source

    def test_existing_frontend_evidence_still_validates(self):
        path = FRONTEND_EVIDENCE / "frontend-verification.json"
        if not path.exists():
            pytest.skip("frontend evidence not present")
        data = json.loads(path.read_text())
        assert data["schema"] == "frontend-verification/v1"
        assert {p["phase"] for p in data["phases"]} <= {
            "lint",
            "typecheck",
            "build",
            "test",
        }


class TestNoWorkflowFilesTouched:
    """Phase 2 STOP condition: .github/workflows/ must remain unmodified."""

    def test_workflow_directory_still_has_nine_files(self):
        workflows = sorted((REPO_ROOT / ".github/workflows").glob("*.yml"))
        assert len(workflows) == 9

    def test_no_workflow_file_is_modified(self):
        result = subprocess.run(
            ["git", "status", "--porcelain", ".github/workflows/"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.stdout.strip() == "", (
            f"workflow files modified: {result.stdout}"
        )
