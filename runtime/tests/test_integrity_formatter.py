"""Formatter Tests — Program 10.

Tests for the integrity report terminal formatter.
Deterministic. No network. No git mutation.
"""

from __future__ import annotations

from runtime.foundation.integrity.formatter import (
    format_integrity_report,
    format_violation_detail,
)
from runtime.foundation.integrity.models import (
    IntegrityReport,
    Violation,
    ViolationCategory,
    ViolationSeverity,
)


def make_report(
    violations: list[Violation] | None = None,
    files_scanned: int = 10,
    rules_evaluated: int = 28,
) -> IntegrityReport:
    return IntegrityReport(
        timestamp="2026-08-05T00:00:00+00:00",
        rules_evaluated=rules_evaluated,
        rules_passed=(
            rules_evaluated - len(violations) if violations else rules_evaluated
        ),
        rules_failed=len(violations) if violations else 0,
        violations=tuple(violations or []),
        files_scanned=files_scanned,
        cross_layer_entries=1,
        graph_nodes=100,
        graph_edges=200,
        scan_errors=(),
        critical_count=sum(
            1 for v in (violations or []) if v.severity == ViolationSeverity.CRITICAL
        ),
        high_count=sum(
            1 for v in (violations or []) if v.severity == ViolationSeverity.HIGH
        ),
        medium_count=sum(
            1 for v in (violations or []) if v.severity == ViolationSeverity.MEDIUM
        ),
        low_count=sum(
            1 for v in (violations or []) if v.severity == ViolationSeverity.LOW
        ),
        info_count=sum(
            1 for v in (violations or []) if v.severity == ViolationSeverity.INFO
        ),
    )


class TestFormatIntegrityReport:
    """Tests for format_integrity_report."""

    def test_pass_report_contains_pass_label(self) -> None:
        report = make_report(violations=[])
        output = format_integrity_report(report)
        assert "PASS" in output

    def test_fail_report_contains_fail_label(self) -> None:
        v = Violation(
            rule_id="ARCH-001",
            rule_name="Router may not import Engine",
            severity=ViolationSeverity.HIGH,
            category=ViolationCategory.STRUCTURAL,
            file_path="backend/src/routers/loans.py",
            description="Router imports Engine directly.",
            suggested_action="Use the Service layer instead.",
            line_number=10,
        )
        report = make_report(violations=[v])
        output = format_integrity_report(report)
        assert "FAIL" in output

    def test_report_contains_rules_count(self) -> None:
        report = make_report(rules_evaluated=28)
        output = format_integrity_report(report)
        assert "28" in output

    def test_report_contains_violations_count(self) -> None:
        v = Violation(
            rule_id="ARCH-001",
            rule_name="Router may not import Engine",
            severity=ViolationSeverity.HIGH,
            category=ViolationCategory.STRUCTURAL,
            file_path="backend/src/routers/loans.py",
            description="Router imports Engine directly.",
            line_number=10,
        )
        report = make_report(violations=[v])
        output = format_integrity_report(report)
        assert "1" in output

    def test_report_contains_file_path(self) -> None:
        v = Violation(
            rule_id="ARCH-001",
            rule_name="Router may not import Engine",
            severity=ViolationSeverity.HIGH,
            category=ViolationCategory.STRUCTURAL,
            file_path="backend/src/routers/loans.py",
            description="Router imports Engine directly.",
            line_number=10,
        )
        report = make_report(violations=[v])
        output = format_integrity_report(report)
        assert "backend/src/routers/loans.py" in output

    def test_report_contains_rule_id(self) -> None:
        v = Violation(
            rule_id="ARCH-002",
            rule_name="Component may not call API directly",
            severity=ViolationSeverity.HIGH,
            category=ViolationCategory.STRUCTURAL,
            file_path="frontend/components/card.tsx",
            description="Component calls fetch directly.",
            line_number=42,
        )
        report = make_report(violations=[v])
        output = format_integrity_report(report)
        assert "ARCH-002" in output

    def test_report_contains_suggested_action(self) -> None:
        v = Violation(
            rule_id="ARCH-001",
            rule_name="Router may not import Engine",
            severity=ViolationSeverity.HIGH,
            category=ViolationCategory.STRUCTURAL,
            file_path="backend/src/routers/loans.py",
            description="Router imports Engine directly.",
            suggested_action="Use the Service layer instead.",
            line_number=10,
        )
        report = make_report(violations=[v])
        output = format_integrity_report(report)
        assert "Service layer" in output

    def test_report_contains_scan_metadata(self) -> None:
        report = make_report(files_scanned=50, rules_evaluated=28)
        output = format_integrity_report(report)
        assert "50" in output

    def test_report_is_deterministic(self) -> None:
        v = Violation(
            rule_id="ARCH-001",
            rule_name="Router may not import Engine",
            severity=ViolationSeverity.HIGH,
            category=ViolationCategory.STRUCTURAL,
            file_path="backend/src/routers/loans.py",
            description="Router imports Engine directly.",
            line_number=10,
        )
        report = make_report(violations=[v])
        output1 = format_integrity_report(report)
        output2 = format_integrity_report(report)
        assert output1 == output2

    def test_empty_report_has_no_violations_section(self) -> None:
        report = make_report(violations=[])
        output = format_integrity_report(report)
        assert "No violations" in output


class TestFormatViolationDetail:
    """Tests for format_violation_detail."""

    def test_contains_rule_id(self) -> None:
        v = Violation(
            rule_id="ARCH-001",
            rule_name="Router may not import Engine",
            severity=ViolationSeverity.HIGH,
            category=ViolationCategory.STRUCTURAL,
            file_path="backend/src/routers/loans.py",
            description="Router imports Engine directly.",
            line_number=10,
        )
        output = format_violation_detail(v)
        assert "ARCH-001" in output

    def test_contains_file_path(self) -> None:
        v = Violation(
            rule_id="ARCH-002",
            rule_name="Component may not call API directly",
            severity=ViolationSeverity.HIGH,
            category=ViolationCategory.STRUCTURAL,
            file_path="frontend/components/card.tsx",
            description="Component calls fetch directly.",
            line_number=42,
        )
        output = format_violation_detail(v)
        assert "frontend/components/card.tsx" in output

    def test_contains_description(self) -> None:
        v = Violation(
            rule_id="ARCH-003",
            rule_name="Mapper must not import React",
            severity=ViolationSeverity.LOW,
            category=ViolationCategory.STRUCTURAL,
            file_path="frontend/lib/mappers/loans-mapper.ts",
            description="Mapper imports React.",
            line_number=3,
        )
        output = format_violation_detail(v)
        assert "Mapper imports React" in output
