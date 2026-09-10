"""
M9-C57 — Diagnostic formatter for financial semantic failures.

Integrates with FailureReport to produce enriched output when financial
invariant violations are detected in test results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.foundation.verification.semantics.parser import SemanticFailure


@dataclass
class EnrichedFailureReport:
    """A FailureReport extended with optional semantic failure information."""

    classification: str
    unit_id: str | None
    command: str
    exit_code: int | None
    failure_summary: str | None = None
    test_failure_count: int | None = None
    root_failure: str | None = None
    diagnostic: str | None = None
    evidence_path: str | None = None
    status: str = "failed"
    semantic_failure: SemanticFailure | None = None


class DiagnosticFormatter:
    """Format failure reports with optional semantic enrichment."""

    @staticmethod
    def format(report: EnrichedFailureReport) -> str:
        lines: list[str] = []
        lines.append("=" * 80)
        lines.append("  VERIFICATION FAILURE REPORT")
        lines.append("=" * 80)
        lines.append(f"  Status:       {report.status}")
        lines.append(f"  Classification: {report.classification}")
        if report.unit_id:
            lines.append(f"  Unit:         {report.unit_id}")
        lines.append(f"  Command:      {report.command}")
        lines.append(f"  Exit code:    {report.exit_code}")
        if report.test_failure_count is not None:
            lines.append(f"  Failures:     {report.test_failure_count}")

        # Semantic failure section
        if report.semantic_failure:
            sf = report.semantic_failure
            lines.append("-" * 80)
            lines.append("  🔍 FINANCIAL INVARIANT VIOLATED")
            lines.append(f"  Invariant:    {sf.invariant_id}")
            lines.append(f"  Expected:     {sf.expected}")
            lines.append(f"  Actual:       {sf.actual}")
            if sf.context:
                ctx_str = ", ".join(f"{k}={v}" for k, v in sorted(sf.context.items()))
                lines.append(f"  Context:      {{{ctx_str}}}")
            if sf.remediation:
                lines.append(f"  Remediation:  💡 {sf.remediation}")

        if report.failure_summary:
            lines.append("-" * 80)
            lines.append("  FAILURE SUMMARY:")
            for line in report.failure_summary.splitlines()[:10]:
                lines.append(f"  {line}")

        if report.diagnostic:
            lines.append("-" * 80)
            lines.append("  DIAGNOSTIC:")
            for line in report.diagnostic.splitlines()[:10]:
                lines.append(f"  {line}")

        lines.append("=" * 80)
        return "\n".join(lines)

    @staticmethod
    def format_json(report: EnrichedFailureReport) -> str:
        import json  # noqa: PLC0415

        data = report.to_dict()
        return json.dumps(data, indent=2, default=str)

    @staticmethod
    def from_failure_report(failure_report: Any) -> EnrichedFailureReport:
        """Convert a FailureReport to an EnrichedFailureReport."""
        return EnrichedFailureReport(
            classification=failure_report.classification,
            unit_id=failure_report.unit_id,
            command=failure_report.command,
            exit_code=failure_report.exit_code,
            failure_summary=failure_report.failure_summary,
            test_failure_count=failure_report.test_failure_count,
            root_failure=failure_report.root_failure,
            diagnostic=failure_report.diagnostic,
            evidence_path=failure_report.evidence_path,
            status=failure_report.status,
            semantic_failure=None,
        )


def enrich_with_semantic_failure(report: EnrichedFailureReport, semantic: SemanticFailure) -> EnrichedFailureReport:
    """Attach a SemanticFailure to an EnrichedFailureReport."""
    return EnrichedFailureReport(
        classification=report.classification,
        unit_id=report.unit_id,
        command=report.command,
        exit_code=report.exit_code,
        failure_summary=report.failure_summary,
        test_failure_count=report.test_failure_count,
        root_failure=report.root_failure,
        diagnostic=report.diagnostic,
        evidence_path=report.evidence_path,
        status=report.status,
        semantic_failure=semantic,
    )
