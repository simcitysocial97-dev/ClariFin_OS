"""Tests for runtime/system/evidence/aggregator.py.

Tests the EvidenceAggregator by creating synthetic artifact files in
tempfile.TemporaryDirectory and constructing EvidenceSummary objects directly.
Does NOT read real CI artifacts.
"""

import json
import tempfile
from pathlib import Path

from runtime.system.evidence.aggregator import (
    EvidenceAggregator,
    EvidenceSummary,
)
from runtime.system.evidence.collectors.mutation import MutationEvidence


class TestAggregateProducesSummary:
    """Test that aggregate() produces a valid EvidenceSummary with synthetic artifacts."""

    def _make_passing_artifacts(self, tmpdir: Path) -> None:
        """Create synthetic artifacts that produce a 'pass' summary."""
        test_dir = tmpdir / "test-results"
        test_dir.mkdir(parents=True)
        (test_dir / "pytest.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<testsuites>\n'
            '  <testsuite name="pytest" tests="10" failures="0" errors="0" skipped="0">'
            '<testcase name="test_a"/>'
            '<testcase name="test_b"/>'
            '</testsuite>\n'
            '</testsuites>\n'
        )

        cov_dir = tmpdir / "coverage"
        cov_dir.mkdir(parents=True)
        (cov_dir / "synth_cov.json").write_text(json.dumps({
            "totals": {"percent_covered": 75.0},
            "files": {},
        }))

    def test_overall_status_is_valid_value(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            self._make_passing_artifacts(tmpdir)
            agg = EvidenceAggregator(tmpdir)
            summary = agg.aggregate(tmpdir)
            assert summary.overall_status in ("pass", "attention_needed", "fail")

    def test_backend_unit_tests_status_is_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            self._make_passing_artifacts(tmpdir)
            agg = EvidenceAggregator(tmpdir)
            summary = agg.aggregate(tmpdir)
            assert "status" in summary.backend["unit_tests"]

    def test_attention_needed_is_a_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            self._make_passing_artifacts(tmpdir)
            agg = EvidenceAggregator(tmpdir)
            summary = agg.aggregate(tmpdir)
            assert isinstance(summary.attention_needed, list)

    def test_passing_status_no_attention(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            self._make_passing_artifacts(tmpdir)
            agg = EvidenceAggregator(tmpdir)
            summary = agg.aggregate(tmpdir)
            assert summary.overall_status == "pass"
            assert summary.attention_needed == []


class TestAttentionNeededMutationBelow60:
    """Mutation score below 60% should generate an attention item."""

    def test_mutation_below_target_generates_attention(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            agg = EvidenceAggregator(tmpdir)
            backend = {
                "mutation": {
                    "loan": {
                        "score_pct": 45.0,
                        "killed": 9,
                        "survived": 11,
                        "status": "below_target",
                    },
                },
                "unit_tests": {"status": "pass", "passed": 10, "failed": 0},
                "property_tests": {"status": "pass", "passed": 5, "counterexamples_found": 0},
                "coverage": {"collected": False, "overall_pct": 0.0},
                "contract_tests": {"status": "not_run", "endpoints_tested": 0, "failures_found": 0},
            }
            mut_ev = MutationEvidence(score_pct=45.0, killed=9, survived=11)
            attention = agg._build_attention(backend, mut_ev)
            assert any(item["type"] == "mutation_below_target" for item in attention)


class TestAttentionNeededLowCoverage:
    """Coverage below 40% (when collected) should generate an attention item."""

    def test_low_coverage_generates_attention(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            agg = EvidenceAggregator(tmpdir)
            backend = {
                "unit_tests": {"status": "pass", "passed": 10, "failed": 0},
                "property_tests": {"status": "pass", "passed": 5, "counterexamples_found": 0},
                "mutation": {},
                "contract_tests": {"status": "pass", "endpoints_tested": 5, "failures_found": 0},
                "coverage": {"collected": True, "overall_pct": 25.0},
            }
            mut_ev = MutationEvidence(score_pct=0.0, killed=0, survived=0)
            attention = agg._build_attention(backend, mut_ev)
            assert any(item["type"] == "low_coverage" for item in attention)


class TestAttentionNeededTestFailures:
    """Unit test failures should generate an attention item."""

    def test_unit_test_failures_generate_attention(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            agg = EvidenceAggregator(tmpdir)
            backend = {
                "unit_tests": {"status": "fail", "passed": 5, "failed": 3},
                "property_tests": {"status": "pass", "passed": 5, "counterexamples_found": 0},
                "mutation": {},
                "contract_tests": {"status": "pass", "endpoints_tested": 5, "failures_found": 0},
                "coverage": {"collected": False, "overall_pct": 0.0},
            }
            mut_ev = MutationEvidence(score_pct=0.0, killed=0, survived=0)
            attention = agg._build_attention(backend, mut_ev)
            assert any(item["type"] == "unit_test_failures" for item in attention)


class TestMarkdownGeneration:
    """Test EvidenceSummary markdown output."""

    def test_to_markdown_contains_verification_header(self):
        summary = EvidenceSummary(
            overall_status="pass",
            backend={
                "unit_tests": {"status": "pass", "passed": 10, "failed": 0},
                "property_tests": {"status": "pass", "passed": 5, "counterexamples_found": 0},
                "contract_tests": {"status": "pass", "endpoints_tested": 5, "failures_found": 0},
            },
        )
        md = summary.to_markdown()
        assert "## Verification Evidence" in md

    def test_to_markdown_contains_check_table_header(self):
        summary = EvidenceSummary(
            overall_status="pass",
            backend={
                "unit_tests": {"status": "pass", "passed": 10, "failed": 0},
                "property_tests": {"status": "pass", "passed": 5, "counterexamples_found": 0},
                "contract_tests": {"status": "pass", "endpoints_tested": 5, "failures_found": 0},
            },
        )
        md = summary.to_markdown()
        assert "| Check |" in md


class TestMissingEvidence:
    """Test that aggregator handles missing evidence gracefully."""

    def test_aggregate_with_empty_dir_does_not_crash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            agg = EvidenceAggregator(tmpdir)
            summary = agg.aggregate(tmpdir)
            assert isinstance(summary, EvidenceSummary)

    def test_aggregate_with_empty_dir_returns_not_run_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            agg = EvidenceAggregator(tmpdir)
            summary = agg.aggregate(tmpdir)
            assert summary.overall_status == "not_run"
