#!/usr/bin/env python3
"""Verification Intelligence Layer CLI.

Provides architecture-aware verification intelligence for ClariFin_OS.

Usage:
    python -m verification_intelligence --all              # Generate all reports
    python -m verification_intelligence --dependency-map   # Generate dependency map
    python -m verification_intelligence --change-impact    # Generate change impact
    python -m verification_intelligence --risk-map         # Generate risk map
    python -m verification_intelligence --evidence         # Generate verification evidence
    python -m verification_intelligence --coverage         # Generate architectural coverage
    python -m verification_intelligence --self-validate    # Run self-validation
    python -m verification_intelligence --selective        # Generate selective CI plan
    python -m verification_intelligence --summary          # Generate verification summary
    python -m verification_intelligence --changed <files>  # Analyze specific files
    python -m verification_intelligence --json             # Machine-readable output
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"


def cmd_dependency_map(args: argparse.Namespace) -> None:
    """Generate dependency map report."""
    from verification.intelligence.dependency_engine import (
        DependencyEngine,  # type: ignore[import-not-found]
    )

    engine = DependencyEngine()
    graph = engine.discover()
    data = graph.to_dict()

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GENERATED_DIR / "dependency-map.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Generated: dependency-map.json ({len(graph.edges)} edges)")
    if args.json:
        print(json.dumps(data, indent=2))


def cmd_change_impact(args: argparse.Namespace) -> None:
    """Generate change impact report."""
    from verification.intelligence.impact_engine import (
        ImpactEngine,  # type: ignore[import-not-found]
    )

    engine = ImpactEngine()

    if args.changed:
        changed_files = args.changed
    else:
        changed_files = _get_git_changed_files()

    impact = engine.analyze(changed_files)
    data = impact.to_dict()

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GENERATED_DIR / "change-impact.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(
        f"Generated: change-impact.json "
        f"(risk={impact.overall_risk}, "
        f"strategy={impact.strategy}, "
        f"caps={len(impact.affected_capabilities)})"
    )
    if args.json:
        print(json.dumps(data, indent=2))


def cmd_risk_map(args: argparse.Namespace) -> None:
    """Generate risk map report."""
    from verification.intelligence.risk_engine import (
        RiskEngine,  # type: ignore[import-not-found]
    )

    engine = RiskEngine()
    risk_map = engine.classify_all()
    data = risk_map.to_dict()

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GENERATED_DIR / "risk-map.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Generated: risk-map.json ({len(risk_map.entries)} entries)")
    if args.json:
        print(json.dumps(data, indent=2))


def cmd_evidence(args: argparse.Namespace) -> None:
    """Generate verification evidence report."""
    from verification.intelligence.evidence_engine import (
        EvidenceEngine,  # type: ignore[import-not-found]
    )

    engine = EvidenceEngine()
    summary = engine.generate_all()
    data = summary.to_dict()

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GENERATED_DIR / "verification-evidence.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(
        f"Generated: verification-evidence.json "
        f"({summary.fully_verified}/{summary.total_capabilities} verified)"
    )
    if args.json:
        print(json.dumps(data, indent=2))


def cmd_coverage(args: argparse.Namespace) -> None:
    """Generate architectural coverage report."""
    from verification.intelligence.coverage_engine import (
        CoverageEngine,  # type: ignore[import-not-found]
    )

    engine = CoverageEngine()
    coverage = engine.generate_all()
    data = coverage.to_dict()

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GENERATED_DIR / "architectural-coverage.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(
        f"Generated: architectural-coverage.json "
        f"({coverage.summary.get('average_coverage_percent', 0)}% avg coverage)"
    )
    if args.json:
        print(json.dumps(data, indent=2))


def cmd_self_validate(args: argparse.Namespace) -> None:
    """Run runtime self-validation."""
    from verification.intelligence.self_validation import (
        SelfValidationEngine,  # type: ignore[import-not-found]
    )

    engine = SelfValidationEngine()
    report = engine.run_all()
    data = report.to_dict()

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GENERATED_DIR / "self-validation-report.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(
        f"Generated: self-validation-report.json "
        f"(passed={report.passed}, failed={report.failed}, warnings={report.warnings})"
    )
    if args.json:
        print(json.dumps(data, indent=2))


def cmd_selective(args: argparse.Namespace) -> None:
    """Generate selective CI execution plan."""
    from verification.intelligence.impact_engine import ImpactEngine
    from verification.intelligence.selective_engine import (
        SelectiveEngine,  # type: ignore[import-not-found]
    )

    impact_engine = ImpactEngine()

    if args.changed:
        changed_files = args.changed
    else:
        changed_files = _get_git_changed_files()

    impact = impact_engine.analyze(changed_files)

    engine = SelectiveEngine()
    plan = engine.plan(changed_files, impact.to_dict())
    data = plan.to_dict()

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GENERATED_DIR / "selective-plan.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(
        f"Generated: selective-plan.json "
        f"(strategy={plan.strategy}, "
        f"must_run={len(plan.must_run_jobs)}, "
        f"skipped={len(plan.skipped_jobs)})"
    )
    if args.json:
        print(json.dumps(data, indent=2))


def cmd_performance_metrics(args: argparse.Namespace) -> None:
    """Generate verification performance metrics report."""
    from src.verification.intelligence.metrics_engine import MetricsEngine

    engine = MetricsEngine()

    # For now, generate sample data
    # In production, this would collect real metrics from test runs
    engine.generate_sample_report(str(GENERATED_DIR / "verification-performance.json"))

    print("Generated: verification-performance.json")
    if args.json:
        with open(GENERATED_DIR / "verification-performance.json") as f:
            print(f.read())


def cmd_qa_report(args: argparse.Namespace) -> None:
    """Generate comprehensive QA report."""
    from src.verification.intelligence.qa_report import QAReportGenerator

    generator = QAReportGenerator(str(GENERATED_DIR))

    # For now, generate sample data
    # In production, this would use real data
    generator.generate_sample_report(str(GENERATED_DIR / "qa-report.md"))

    print("Generated: qa-report.md")
    if args.json:
        with open(GENERATED_DIR / "qa-report.md") as f:
            print(f.read())


def cmd_verification_matrix(args: argparse.Namespace) -> None:
    """Generate verification matrix."""
    from src.verification.intelligence.verification_matrix import (
        VerificationMatrixEngine,
    )

    engine = VerificationMatrixEngine()

    # For now, generate sample data
    # In production, this would load real capability, test, and risk data
    engine.generate_sample_matrix(str(GENERATED_DIR / "verification-matrix.json"))

    print("Generated: verification-matrix.json")
    if args.json:
        with open(GENERATED_DIR / "verification-matrix.json") as f:
            print(f.read())


def cmd_regression_matrix(args: argparse.Namespace) -> None:
    """Generate regression test matrix."""
    from src.verification.intelligence.regression_engine import RegressionEngine

    engine = RegressionEngine()

    # For now, generate sample data
    # In production, this would collect real test results
    engine.generate_sample_matrix(str(GENERATED_DIR / "regression-matrix.json"))

    print("Generated: regression-matrix.json")
    if args.json:
        with open(GENERATED_DIR / "regression-matrix.json") as f:
            print(f.read())


def cmd_quality_report(args: argparse.Namespace) -> None:
    """Generate quality report."""

    from src.verification.intelligence.report_engine import ReportEngine

    # Generate quality report markdown
    report_content = """# Quality Report

## Verification Intelligence Summary

This report provides an overview of the verification quality for the current codebase.
"""

    # Add verification summary
    engine = ReportEngine()
    results = engine.generate_all()

    report_content += """
### Verification Status
"""
    for report_name, report_data in results.items():
        report_content += f"- **{report_name}**: {report_data.get('status', 'N/A')}\n"

    # Add performance metrics
    metrics_path = GENERATED_DIR / "verification-performance.json"
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics = json.load(f)

        report_content += """
### Performance Metrics
"""
        report_content += (
            f"- **Overall Score**: {metrics.get('overall_score', 0):.1f}/100\n"
        )
        report_content += f"- **Test Performance**: {metrics.get('test_performance', [{}])[0].get('avg_execution_time_ms', 0):.1f}ms avg\n"
        report_content += f"- **Coverage**: {metrics.get('coverage', [{}])[0].get('percentage', 0):.1f}%\n"
        report_content += f"- **Selective Execution Efficiency**: {metrics.get('selective_execution', [{}])[0].get('efficiency_percentage', 0):.1f}%\n"

    # Add capability validation status
    validation_path = GENERATED_DIR / "verification-evidence.json"
    if validation_path.exists():
        with open(validation_path) as f:
            validation = json.load(f)

        report_content += """
### Capability Validation
"""
        report_content += f"- **Fully Verified**: {validation.get('fully_verified', 0)}/{validation.get('total_capabilities', 0)} capabilities\n"
        report_content += f"- **Verification Coverage**: {validation.get('verification_coverage_percent', 0):.1f}%\n"

    # Add risk assessment
    risk_path = GENERATED_DIR / "risk-map.json"
    if risk_path.exists():
        with open(risk_path) as f:
            risk_data = json.load(f)

        report_content += """
### Risk Assessment
"""
        for entry in risk_data.get("entries", []):
            if entry.get("risk_level"):
                report_content += (
                    f"- **{entry['capability_id']}**: {entry['risk_level']} risk\n"
                )

    # Write markdown file
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GENERATED_DIR / "quality-report.md"
    with open(output_path, "w") as f:
        f.write(report_content)

    print("Generated: quality-report.md")
    if args.json:
        print(json.dumps({"report": "quality-report.md"}, indent=2))


def cmd_summary(args: argparse.Namespace) -> None:
    """Generate verification summary report."""


def cmd_all(args: argparse.Namespace) -> None:
    """Generate all reports."""
    from verification.intelligence.report_engine import ReportEngine

    engine = ReportEngine()
    results = engine.generate_all()

    print("Generated all reports:")
    for report_name, report_data in results.items():
        print(f"  - {report_name}: {report_data.get('file', 'N/A')}")

    if args.json:
        print(json.dumps(results, indent=2))


def _get_git_changed_files() -> list[str]:
    """Get changed files from git diff."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except FileNotFoundError:
        return []


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verification Intelligence Layer for ClariFin_OS"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all reports",
    )
    parser.add_argument(
        "--dependency-map",
        action="store_true",
        help="Generate dependency map",
    )
    parser.add_argument(
        "--change-impact",
        action="store_true",
        help="Generate change impact report",
    )
    parser.add_argument(
        "--risk-map",
        action="store_true",
        help="Generate risk map",
    )
    parser.add_argument(
        "--evidence",
        action="store_true",
        help="Generate verification evidence",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate architectural coverage",
    )
    parser.add_argument(
        "--self-validate",
        action="store_true",
        help="Run self-validation",
    )
    parser.add_argument(
        "--selective",
        action="store_true",
        help="Generate selective CI plan",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Generate verification summary",
    )
    parser.add_argument(
        "--performance-metrics",
        action="store_true",
        help="Generate verification performance metrics",
    )
    parser.add_argument(
        "--quality-report",
        action="store_true",
        help="Generate quality report",
    )
    parser.add_argument(
        "--regression-matrix",
        action="store_true",
        help="Generate regression test matrix",
    )
    parser.add_argument(
        "--verification-matrix",
        action="store_true",
        help="Generate verification matrix",
    )
    parser.add_argument(
        "--qa-report",
        action="store_true",
        help="Generate comprehensive QA report",
    )
    parser.add_argument(
        "--changed",
        nargs="*",
        help="Analyze specific changed files",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Machine-readable JSON output",
    )

    args = parser.parse_args()

    if not any(
        [
            args.all,
            args.dependency_map,
            args.change_impact,
            args.risk_map,
            args.evidence,
            args.coverage,
            args.self_validate,
            args.selective,
            args.summary,
            args.performance_metrics,
            args.quality_report,
            args.regression_matrix,
            args.verification_matrix,
            args.qa_report,
        ]
    ):
        parser.print_help()
        sys.exit(1)

    if args.all:
        cmd_all(args)
    elif args.dependency_map:
        cmd_dependency_map(args)
    elif args.change_impact:
        cmd_change_impact(args)
    elif args.risk_map:
        cmd_risk_map(args)
    elif args.evidence:
        cmd_evidence(args)
    elif args.coverage:
        cmd_coverage(args)
    elif args.self_validate:
        cmd_self_validate(args)
    elif args.selective:
        cmd_selective(args)
    elif args.summary:
        cmd_summary(args)
    elif args.performance_metrics:
        cmd_performance_metrics(args)
    elif args.quality_report:
        cmd_quality_report(args)
    elif args.regression_matrix:
        cmd_regression_matrix(args)
    elif args.verification_matrix:
        cmd_verification_matrix(args)
    elif args.qa_report:
        cmd_qa_report(args)


if __name__ == "__main__":
    main()
