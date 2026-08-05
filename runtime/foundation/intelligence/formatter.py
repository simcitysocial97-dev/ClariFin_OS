from __future__ import annotations

import sys

from runtime.foundation.intelligence.models import (
    AffectedTestPlan,
    DiagnosticReport,
    RepairSuggestion,
    RiskReport,
    Severity,
)


def _supports_color() -> bool:
    if not hasattr(sys.stdout, "isatty"):
        return False
    return sys.stdout.isatty()


def _color(code: int, text: str) -> str:
    if _supports_color():
        return f"\033[{code}m{text}\033[0m"
    return text


def _bold(text: str) -> str:
    return _color(1, text)


def _red(text: str) -> str:
    return _color(31, text)


def _yellow(text: str) -> str:
    return _color(33, text)


def _green(text: str) -> str:
    return _color(32, text)


def _cyan(text: str) -> str:
    return _color(36, text)


def _white(text: str) -> str:
    return _color(37, text)


def format_diagnostic_report(report: DiagnosticReport) -> str:
    lines: list[str] = []
    lines.append(_bold("Developer Diagnostic"))
    lines.append("")

    lines.append(_cyan("Modified"))
    for f in report.changed_files:
        lines.append(f"  {f}")
    lines.append("")

    if report.affected_capabilities:
        lines.append(_cyan("Affected Capabilities"))
        for c in report.affected_capabilities:
            lines.append(f"  {c}")
        lines.append("")

    if report.affected_workspaces:
        lines.append(_cyan("Affected Workspaces"))
        for w in report.affected_workspaces:
            lines.append(f"  {w}")
        lines.append("")

    if report.affected_endpoints:
        lines.append(_cyan("Affected Endpoints"))
        for e in report.affected_endpoints:
            lines.append(f"  {e}")
        lines.append("")

    if report.repair_suggestions:
        lines.append(_cyan("Repair Suggestions"))
        for s in report.repair_suggestions:
            lines.append(f"  {_yellow(s.target)} ({s.change_type})")
            lines.append(f"    {s.guidance}")
        lines.append("")

    lines.append(_cyan("Verification"))
    lines.append(f"  Profile: {report.suggested_verification_profile}")
    lines.append(
        f"  Local: {report.verification_estimate_local_seconds} sec"
    )
    lines.append(
        f"  CI: {report.verification_estimate_ci_minutes} min"
    )
    lines.append("")

    if report.dependency_chain:
        lines.append(_cyan("Dependency Chain"))
        for chain in report.dependency_chain:
            source = chain.get("source", "unknown")
            engine = chain.get("engine", "unknown")
            lines.append(f"  {source}")
            lines.append(f"    Engine: {engine}")
            for cap in chain.get("capabilities", []):
                lines.append(f"    Capability: {cap}")
            for ep in chain.get("endpoints", []):
                lines.append(f"    Endpoint: {ep}")
        lines.append("")

    return "\n".join(lines)


def format_repair_suggestions(
    suggestions: list[RepairSuggestion],
) -> str:
    lines: list[str] = []
    lines.append(_bold("Repair Guidance"))
    lines.append("")

    if not suggestions:
        lines.append("No repair suggestions.")
        return "\n".join(lines)

    for s in suggestions:
        lines.append(f"{_yellow(s.target)} ({s.change_type})")
        lines.append(f"  Reason: {s.reason}")
        lines.append(f"  Guidance: {s.guidance}")
        lines.append(f"  Ref: {s.dependency_reference}")
        lines.append("")

    return "\n".join(lines)


def format_risk_report(report: RiskReport) -> str:
    lines: list[str] = []
    lines.append(_bold("Risk Analysis"))
    lines.append("")

    score_color = _red
    if report.severity == Severity.LOW:
        score_color = _green
    elif report.severity == Severity.MEDIUM:
        score_color = _yellow
    elif report.severity == Severity.HIGH:
        score_color = _red
    elif report.severity == Severity.CRITICAL:
        score_color = _red

    lines.append(f"Risk Score: {score_color(str(report.score))}")
    lines.append(f"Severity: {_bold(report.severity.value)}")
    lines.append("")

    if report.reasons:
        lines.append(_cyan("Reasons"))
        for r in report.reasons:
            lines.append(f"  - {r}")
        lines.append("")

    if report.changed_layers:
        lines.append(_cyan("Changed Layers"))
        for layer in report.changed_layers:
            lines.append(f"  - {layer}")
        lines.append("")

    lines.append(f"Cross-Layer Depth: {report.cross_layer_depth}")
    lines.append("")

    return "\n".join(lines)


def format_affected_test_plan(plan: AffectedTestPlan) -> str:
    lines: list[str] = []
    lines.append(_bold("Affected Tests"))
    lines.append("")

    if plan.backend_tests:
        lines.append(_cyan("Backend"))
        for t in plan.backend_tests:
            lines.append(f"  {t}")
        lines.append("")

    if plan.frontend_tests:
        lines.append(_cyan("Frontend"))
        for t in plan.frontend_tests:
            lines.append(f"  {t}")
        lines.append("")

    if plan.runtime_tests:
        lines.append(_cyan("Runtime"))
        for t in plan.runtime_tests:
            lines.append(f"  {t}")
        lines.append("")

    if plan.playwright:
        lines.append(_cyan("Playwright"))
        for t in plan.playwright:
            lines.append(f"  {t}")
        lines.append("")

    if plan.contracts:
        lines.append(_cyan("Contracts"))
        for t in plan.contracts:
            lines.append(f"  {t}")
        lines.append("")

    lines.append(f"Total: {plan.total_count} tests")
    lines.append("")

    return "\n".join(lines)