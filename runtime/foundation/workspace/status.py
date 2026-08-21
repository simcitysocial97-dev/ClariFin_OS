"""Status Workspace — Program 9.

Command: python runtime/verify.py status

Displays repository status, verification status, planner status,
cross-layer status, engineering health, recent failures,
current verification cache, and risk summary.
"""

from __future__ import annotations


from runtime.foundation.workspace.formatter import (
    format_duration,
    format_percent,
    format_status,
    render_section,
    render_table,
)
from runtime.foundation.workspace.models import StatusWorkspace
from runtime.foundation.workspace.workspace import WorkspaceLoader


def render_status(workspace: StatusWorkspace) -> str:
    lines: list[str] = []

    lines.append(render_section("Repository Status"))
    lines.append(
        render_table(
            ["Field", "Value"],
            [
                ["Commit", workspace.repository.commit[:12]],
                ["Branch", workspace.repository.branch],
                ["Changed Files", str(workspace.repository.changed_files)],
                ["Dirty", str(workspace.repository.is_dirty)],
            ],
        )
    )

    lines.append(render_section("Verification Status"))
    lines.append(
        render_table(
            ["Field", "Value"],
            [
                ["Last Profile", workspace.verification.last_profile],
                ["Last Status", format_status(workspace.verification.last_status)],
                ["Last Timestamp", workspace.verification.last_timestamp or "never"],
                ["Passed", str(workspace.verification.passed)],
                ["Failed", str(workspace.verification.failed)],
                ["Skipped", str(workspace.verification.skipped)],
                ["Duration", format_duration(workspace.verification.duration_seconds)],
            ],
        )
    )

    lines.append(render_section("Planner Status"))
    lines.append(
        render_table(
            ["Field", "Value"],
            [
                [
                    "Avg Duration",
                    format_duration(workspace.planner.avg_duration_seconds),
                ],
                ["Runs", str(workspace.planner.runs)],
                ["Last Plan ID", workspace.planner.last_plan_id or "none"],
            ],
        )
    )

    lines.append(render_section("Cross-Layer Status"))
    lines.append(
        render_table(
            ["Field", "Value"],
            [
                ["Total Files", str(workspace.cross_layer.total_files)],
                ["Engines", str(workspace.cross_layer.total_engines)],
                ["Services", str(workspace.cross_layer.total_services)],
                ["Endpoints", str(workspace.cross_layer.total_endpoints)],
                ["Capabilities", str(workspace.cross_layer.total_capabilities)],
            ],
        )
    )

    lines.append(render_section("Engineering Health"))
    lines.append(
        render_table(
            ["Metric", "Value"],
            [
                ["Generated At", workspace.health.generated_at],
                [
                    "Verification Success Rate",
                    format_percent(workspace.health.verification_success_rate),
                ],
                [
                    "Local Success Rate",
                    format_percent(workspace.health.local_success_rate),
                ],
                ["CI Success Rate", format_percent(workspace.health.ci_success_rate)],
                ["Cache Hit Rate", format_percent(workspace.health.cache_hit_rate)],
                [
                    "Avg Duration",
                    format_duration(workspace.health.avg_duration_seconds),
                ],
            ],
        )
    )

    if workspace.recent_failures:
        lines.append(render_section("Recent Failures"))
        rows = [
            [
                f.run_id[:12],
                f.timestamp,
                f.profile,
                str(f.failed),
                f.environment,
            ]
            for f in workspace.recent_failures
        ]
        lines.append(
            render_table(["Run ID", "Timestamp", "Profile", "Failed", "Env"], rows)
        )

    lines.append(render_section("Current Verification Cache"))
    lines.append(
        render_table(
            ["Field", "Value"],
            [
                ["Last Commit", workspace.cache.last_commit[:12] or "none"],
                ["Changed Files", str(len(workspace.cache.changed_files))],
                [
                    "Executed Profiles",
                    ", ".join(workspace.cache.executed_profiles) or "none",
                ],
                ["Duration", format_duration(workspace.cache.duration)],
                ["Timestamp", workspace.cache.timestamp or "never"],
                ["Valid", str(workspace.cache.is_valid)],
            ],
        )
    )

    lines.append(render_section("Risk Summary"))
    lines.append(
        render_table(
            ["Risk Level", "Count"],
            [
                ["High", str(workspace.risk.high_risk_count)],
                ["Medium", str(workspace.risk.medium_risk_count)],
                ["Low", str(workspace.risk.low_risk_count)],
                ["Total Files", str(workspace.risk.total_files)],
            ],
        )
    )

    return "\n".join(lines)


def cmd_status() -> int:
    loader = WorkspaceLoader()
    workspace = loader.load_status_workspace()
    print(render_status(workspace))
    return 0
