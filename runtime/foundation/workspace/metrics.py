"""Metrics Workspace — Program 9.

Command: python runtime/verify.py metrics

Render verification counts, local vs CI metrics, cache hit rate,
average duration, failure rate, flaky tests, dependency growth,
and risk distribution. Read only.
"""

from __future__ import annotations


from runtime.foundation.workspace.formatter import (
    format_duration,
    format_number,
    format_percent,
    render_section,
    render_table,
)
from runtime.foundation.workspace.models import MetricsWorkspace
from runtime.foundation.workspace.workspace import WorkspaceLoader


def render_metrics(workspace: MetricsWorkspace) -> str:
    lines: list[str] = []

    lines.append(render_section("Verification Counts (Combined)"))
    lines.append(render_table(
        ["Metric", "Value"],
        [
            ["Total Runs", format_number(workspace.verification.total_runs)],
            ["Passed", format_number(workspace.verification.passed_runs)],
            ["Failed", format_number(workspace.verification.failed_runs)],
            ["Skipped", format_number(workspace.verification.skipped_runs)],
            ["Success Rate", format_percent(workspace.verification.success_rate)],
        ],
    ))

    lines.append(render_section("Local vs CI Metrics"))
    rows = [
        ["Local", str(workspace.local_verification.total_runs), format_percent(workspace.local_verification.success_rate)],
        ["CI", str(workspace.ci_verification.total_runs), format_percent(workspace.ci_verification.success_rate)],
        ["Combined", str(workspace.verification.total_runs), format_percent(workspace.verification.success_rate)],
    ]
    lines.append(render_table(["Environment", "Runs", "Success Rate"], rows))

    lines.append(render_section("Cache Hit Rate"))
    lines.append(render_table(
        ["Environment", "Hits", "Total", "Hit Rate"],
        [
            ["Local", str(workspace.local_cache.hits), str(workspace.local_cache.total), format_percent(workspace.local_cache.hit_rate)],
            ["CI", str(workspace.ci_cache.hits), str(workspace.ci_cache.total), format_percent(workspace.ci_cache.hit_rate)],
            ["Combined", str(workspace.cache.hits), str(workspace.cache.total), format_percent(workspace.cache.hit_rate)],
        ],
    ))

    lines.append(render_section("Average Duration"))
    lines.append(render_table(
        ["Environment", "Avg", "Min", "Max"],
        [
            ["Local", format_duration(workspace.local_duration.avg_seconds), format_duration(workspace.local_duration.min_seconds), format_duration(workspace.local_duration.max_seconds)],
            ["CI", format_duration(workspace.ci_duration.avg_seconds), format_duration(workspace.ci_duration.min_seconds), format_duration(workspace.ci_duration.max_seconds)],
            ["Combined", format_duration(workspace.duration.avg_seconds), format_duration(workspace.duration.min_seconds), format_duration(workspace.duration.max_seconds)],
        ],
    ))

    lines.append(render_section("Failure Rate"))
    lines.append(render_table(
        ["Environment", "Failure Rate"],
        [
            ["Local", format_percent(workspace.failure_rate.local)],
            ["CI", format_percent(workspace.failure_rate.ci)],
            ["Combined", format_percent(workspace.failure_rate.combined)],
        ],
    ))

    lines.append(render_section("Flaky Tests"))
    lines.append(render_table(
        ["Metric", "Value"],
        [
            ["Total Flaky", str(workspace.flaky_tests.total_flaky)],
            ["Flaky Tests", ", ".join(workspace.flaky_tests.flaky_tests) or "none"],
        ],
    ))

    lines.append(render_section("Dependency Growth"))
    rows = [
        [g.category, str(g.current_count), str(g.previous_count), str(g.delta), format_percent(g.growth_rate * 100) if g.growth_rate else "0.0%"]
        for g in workspace.dependency_growth
    ]
    lines.append(render_table(["Category", "Current", "Previous", "Delta", "Growth Rate"], rows))

    lines.append(render_section("Risk Distribution"))
    lines.append(render_table(
        ["Risk Level", "Count"],
        [
            ["High", str(workspace.risk_distribution.high)],
            ["Medium", str(workspace.risk_distribution.medium)],
            ["Low", str(workspace.risk_distribution.low)],
            ["Total", str(workspace.risk_distribution.total)],
        ],
    ))

    return "\n".join(lines)


def cmd_metrics() -> int:
    loader = WorkspaceLoader()
    workspace = loader.load_metrics_workspace()
    print(render_metrics(workspace))
    return 0
