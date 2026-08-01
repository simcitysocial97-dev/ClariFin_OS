"""Tests for runtime/system/evidence/collectors/*.

Tests create synthetic artifacts in tempfile.TemporaryDirectory.
Does NOT read real CI artifacts from the repository.
"""

import json
import tempfile
from pathlib import Path

from runtime.system.evidence.collectors.coverage import (
    CoverageCollector,
    CoverageEvidence,
)
from runtime.system.evidence.collectors.mutation import (
    MutationCollector,
    MutationEvidence,
)
from runtime.system.evidence.collectors.test_results import (
    TestResultCollector,
    TestResultEvidence,
)
from runtime.system.evidence.collectors.contract import (
    ContractCollector,
    ContractEvidence,
)


class TestCoverageCollector:
    """Tests for CoverageCollector — reads pytest-cov JSON output."""

    def _make_synthetic_coverage(self, tmpdir: Path) -> Path:
        coverage_data = {
            "totals": {
                "covered_lines": 100,
                "num_statements": 150,
                "percent_covered": 66.7,
                "covered_branches": 40,
                "num_branches": 60,
            },
            "files": {
                "src/engines/loan_engine/emi.py": {
                    "summary": {"percent_covered": 90.0},
                    "missing_lines": [45, 46],
                }
            },
        }
        cov_file = tmpdir / "synth_cov.json"
        cov_file.write_text(json.dumps(coverage_data))
        return cov_file

    def test_total_pct_is_approximately_66_7(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            cov_file = self._make_synthetic_coverage(tmpdir)
            evidence = CoverageCollector(tmpdir).collect(cov_file)
            assert abs(evidence.overall_pct - 66.7) < 0.1

    def test_per_engine_loan_is_approximately_90(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            cov_file = self._make_synthetic_coverage(tmpdir)
            evidence = CoverageCollector(tmpdir).collect(cov_file)
            assert evidence.per_engine["loan"] == 90.0

    def test_uncovered_lines_loan_contains_45_and_46(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            cov_file = self._make_synthetic_coverage(tmpdir)
            evidence = CoverageCollector(tmpdir).collect(cov_file)
            assert 45 in evidence.uncovered_lines["loan"]
            assert 46 in evidence.uncovered_lines["loan"]

    def test_branch_coverage_is_approximately_66_7(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            cov_file = self._make_synthetic_coverage(tmpdir)
            evidence = CoverageCollector(tmpdir).collect(cov_file)
            assert abs(evidence.branch_coverage - 66.67) < 0.1

    def test_missing_file_returns_empty_evidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            evidence = CoverageCollector(tmpdir).collect(tmpdir / "nonexistent.json")
            assert evidence.overall_pct == 0.0
            assert evidence.per_engine == {}
            assert evidence.uncovered_lines == {}

    def test_invalid_json_returns_empty_evidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            bad_file = tmpdir / "synth_cov.json"
            bad_file.write_text("not valid json{{{")
            evidence = CoverageCollector(tmpdir).collect(bad_file)
            assert evidence.overall_pct == 0.0


class TestMutationCollector:
    """Tests for MutationCollector — reads mutmut results and survivors."""

    def _make_synthetic_mutation(self, tmpdir: Path):
        results_file = tmpdir / "loan-results.txt"
        results_file.write_text("Killed: 15\nSurvived: 5\nTimeout: 0\n")

        survivors_file = tmpdir / "loan-survivors.txt"
        survivors_file.write_text(
            "--- loan_engine/emi.py\n"
            "+++ (mutation)\n"
            "@@ -10,1 +10,1 @@\n"
            "-    return result\n"
            "+    return None\n"
        )
        return tmpdir

    def test_killed_is_15(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            self._make_synthetic_mutation(tmpdir)
            evidence = MutationCollector(tmpdir).collect(tmpdir)
            assert evidence.killed == 15

    def test_survived_is_5(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            self._make_synthetic_mutation(tmpdir)
            evidence = MutationCollector(tmpdir).collect(tmpdir)
            assert evidence.survived == 5

    def test_score_pct_is_75(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            self._make_synthetic_mutation(tmpdir)
            evidence = MutationCollector(tmpdir).collect(tmpdir)
            assert evidence.score_pct == 75.0

    def test_surviving_diffs_is_non_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            self._make_synthetic_mutation(tmpdir)
            evidence = MutationCollector(tmpdir).collect(tmpdir)
            assert len(evidence.per_engine["loan"]["surviving_diffs"]) > 0

    def test_double_counting_prevention_with_summary(self):
        """If mutation-summary.json exists, results.txt totals must not be double-counted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            summary_file = tmpdir / "mutation-summary.json"
            summary_file.write_text(json.dumps({"killed": 15, "survived": 5}))

            results_file = tmpdir / "loan-results.txt"
            results_file.write_text("Killed: 15\nSurvived: 5\nTimeout: 0\n")

            evidence = MutationCollector(tmpdir).collect(tmpdir)
            assert evidence.killed == 15
            assert evidence.survived == 5

    def test_missing_mutation_dir_returns_empty_evidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            evidence = MutationCollector(tmpdir).collect(tmpdir / "nonexistent_dir")
            assert evidence.killed == 0
            assert evidence.survived == 0
            assert evidence.score_pct == 0.0


class TestTestResultCollector:
    """Tests for TestResultCollector — reads JUnit XML from pytest."""

    SYNTAX_JUNIT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="pytest" tests="10" failures="2" errors="0" skipped="1">
    <testcase name="test_pass_1"/>
    <testcase name="test_fail_1">
      <failure message="assert False">assert 1 == 2</failure>
    </testcase>
  </testsuite>
</testsuites>
"""

    def test_passed_is_7(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            xml_file = tmpdir / "synth_results.xml"
            xml_file.write_text(self.SYNTAX_JUNIT_XML)
            evidence = TestResultCollector(tmpdir).collect(xml_file)
            assert evidence.passed == 7

    def test_failed_is_2(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            xml_file = tmpdir / "synth_results.xml"
            xml_file.write_text(self.SYNTAX_JUNIT_XML)
            evidence = TestResultCollector(tmpdir).collect(xml_file)
            assert evidence.failed == 2

    def test_skipped_is_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            xml_file = tmpdir / "synth_results.xml"
            xml_file.write_text(self.SYNTAX_JUNIT_XML)
            evidence = TestResultCollector(tmpdir).collect(xml_file)
            assert evidence.skipped == 1

    def test_failed_test_names_contains_test_fail_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            xml_file = tmpdir / "synth_results.xml"
            xml_file.write_text(self.SYNTAX_JUNIT_XML)
            evidence = TestResultCollector(tmpdir).collect(xml_file)
            assert "test_fail_1" in evidence.failed_test_names

    def test_passed_is_not_negative(self):
        """Ensure no double-counting — passed must remain non-negative."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            xml_file = tmpdir / "synth_results.xml"
            xml_file.write_text(self.SYNTAX_JUNIT_XML)
            evidence = TestResultCollector(tmpdir).collect(xml_file)
            assert evidence.passed >= 0

    def test_missing_file_returns_empty_evidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            evidence = TestResultCollector(tmpdir).collect(tmpdir / "nonexistent.xml")
            assert evidence.passed == 0
            assert evidence.failed == 0
            assert evidence.skipped == 0
            assert evidence.failed_test_names == []

    def test_invalid_xml_returns_empty_evidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            xml_file = tmpdir / "synth_results.xml"
            xml_file.write_text("not xml at all <<<")
            evidence = TestResultCollector(tmpdir).collect(xml_file)
            assert evidence.passed == 0
            assert evidence.failed == 0


class TestContractCollector:
    """Tests for ContractCollector — reads Schemathesis JSON report."""

    def test_zero_failures_zero_violations_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            contract_file = tmpdir / "contract.json"
            contract_file.write_text(json.dumps({
                "endpoints_tested": 5,
                "failures": [],
                "schema_violations": 0,
            }))
            evidence = ContractCollector(tmpdir).collect(contract_file)
            assert evidence.status == "pass"

    def test_one_failure_status_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            contract_file = tmpdir / "contract.json"
            contract_file.write_text(json.dumps({
                "endpoints_tested": 5,
                "failures": [
                    {"endpoint": "/loans", "method": "GET", "status_code": 500}
                ],
                "schema_violations": 0,
            }))
            evidence = ContractCollector(tmpdir).collect(contract_file)
            assert evidence.status == "fail"

    def test_zero_failures_two_violations_status_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            contract_file = tmpdir / "contract.json"
            contract_file.write_text(json.dumps({
                "endpoints_tested": 5,
                "failures": [],
                "schema_violations": 2,
            }))
            evidence = ContractCollector(tmpdir).collect(contract_file)
            assert evidence.status == "warning"

    def test_missing_file_status_not_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            evidence = ContractCollector(tmpdir).collect(tmpdir / "nonexistent.json")
            assert evidence.status == "not_run"

    def test_failures_are_parsed_with_endpoint(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            contract_file = tmpdir / "contract.json"
            contract_file.write_text(json.dumps({
                "endpoints_tested": 3,
                "failures": [
                    {"endpoint": "/accounts", "method": "POST", "status_code": 404, "response": "Not Found", "request": "{}"}
                ],
                "schema_violations": 0,
            }))
            evidence = ContractCollector(tmpdir).collect(contract_file)
            assert len(evidence.failures) == 1
            assert evidence.failures[0]["endpoint"] == "/accounts"
