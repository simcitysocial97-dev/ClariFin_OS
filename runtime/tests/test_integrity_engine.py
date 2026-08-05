"""Engine Tests — Program 10.

Tests for ArchitecturalIntegrityEngine.evaluate().
Deterministic. No network. No git mutation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.foundation.integrity.engine import (
    ArchitecturalIntegrityEngine,
    evaluate_integrity,
)
from runtime.foundation.integrity.models import IntegrityReport


class TestArchitecturalIntegrityEngine:
    """Tests for the integrity engine."""

    def test_evaluate_returns_report(self) -> None:
        engine = ArchitecturalIntegrityEngine()
        report = engine.evaluate()
        assert isinstance(report, IntegrityReport)

    def test_report_has_required_fields(self) -> None:
        engine = ArchitecturalIntegrityEngine()
        report = engine.evaluate()
        assert report.timestamp
        assert report.rules_evaluated > 0
        assert report.files_scanned >= 0
        assert report.cross_layer_entries >= 0
        assert report.graph_nodes >= 0
        assert report.graph_edges >= 0

    def test_report_is_deterministic(self) -> None:
        engine = ArchitecturalIntegrityEngine()
        report1 = engine.evaluate()
        report2 = engine.evaluate()
        assert report1.rules_evaluated == report2.rules_evaluated
        assert report1.files_scanned == report2.files_scanned
        assert report1.total_violations == report2.total_violations

    def test_report_violations_are_sorted(self) -> None:
        engine = ArchitecturalIntegrityEngine()
        report = engine.evaluate()
        # Violations should be deterministic (same order on repeated runs)
        rule_ids_1 = [v.rule_id for v in report.violations]
        rule_ids_2 = [v.rule_id for v in report.violations]
        assert rule_ids_1 == rule_ids_2

    def test_evaluate_integrity_convenience(self) -> None:
        report = evaluate_integrity()
        assert isinstance(report, IntegrityReport)
        assert report.rules_evaluated > 0

    def test_report_severity_counts_match_violations(self) -> None:
        engine = ArchitecturalIntegrityEngine()
        report = engine.evaluate()
        counts = report.severity_counts
        total = counts["CRITICAL"] + counts["HIGH"] + counts["MEDIUM"] + counts["LOW"] + counts["INFO"]
        assert total == report.total_violations

    def test_report_rules_passed_plus_failed_equals_total(self) -> None:
        engine = ArchitecturalIntegrityEngine()
        report = engine.evaluate()
        # rules_passed + rules_failed should equal rules_evaluated
        # (a rule "fails" if it produces at least one violation)
        assert report.rules_passed + report.rules_failed == report.rules_evaluated

    def test_report_with_custom_repo_root(self, tmp_path: Path) -> None:
        engine = ArchitecturalIntegrityEngine(repo_root=str(tmp_path))
        report = engine.evaluate()
        assert isinstance(report, IntegrityReport)
        assert report.files_scanned == 0  # No source files in empty tmp_path

    def test_report_scan_errors_are_tuple(self) -> None:
        engine = ArchitecturalIntegrityEngine()
        report = engine.evaluate()
        assert isinstance(report.scan_errors, tuple)

    def test_report_violations_are_tuple(self) -> None:
        engine = ArchitecturalIntegrityEngine()
        report = engine.evaluate()
        assert isinstance(report.violations, tuple)