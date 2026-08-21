"""Verification Workspace — Program 9.

Command: python runtime/verify.py verify-status

Display verification profiles, last execution, cache usage,
planner decision, execution history, and pending verification.
"""

from __future__ import annotations


from runtime.foundation.workspace.formatter import (
    format_duration,
    format_status,
    render_section,
    render_table,
)
from runtime.foundation.workspace.models import VerificationWorkspace
from runtime.foundation.workspace.workspace import WorkspaceLoader


def render_verification(workspace: VerificationWorkspace) -> str:
    lines: list[str] = []

    lines.append(render_section("Verification Profiles"))
    rows = [
        [
            p.name,
            format_status(p.status),
            p.last_executed or "never",
            str(p.executed_count),
            p.cache_usage,
        ]
        for p in workspace.profiles
    ]
    lines.append(
        render_table(["Profile", "Status", "Last Executed", "Count", "Cache"], rows)
    )

    lines.append(render_section("Execution History"))
    rows = [
        [
            e.run_id[:12],
            e.timestamp,
            e.profile,
            format_status(e.status),
            str(e.passed),
            str(e.failed),
            format_duration(e.duration_seconds),
        ]
        for e in workspace.execution_history.recent_runs
    ]
    lines.append(
        render_table(
            ["Run ID", "Timestamp", "Profile", "Status", "Pass", "Fail", "Duration"],
            rows,
        )
    )

    lines.append(render_section("Last Execution"))
    if workspace.last_execution:
        e = workspace.last_execution
        lines.append(
            render_table(
                ["Field", "Value"],
                [
                    ["Run ID", e.run_id],
                    ["Timestamp", e.timestamp],
                    ["Environment", e.environment],
                    ["Profile", e.profile],
                    ["Status", format_status(e.status)],
                    ["Passed", str(e.passed)],
                    ["Failed", str(e.failed)],
                    ["Skipped", str(e.skipped)],
                    ["Duration", format_duration(e.duration_seconds)],
                ],
            )
        )
    else:
        lines.append(render_table(["Field", "Value"], [["Last Execution", "none"]]))

    lines.append(render_section("Pending Verification"))
    lines.append(
        render_table(
            ["Metric", "Value"],
            [
                ["Pending Count", str(workspace.pending.pending_count)],
                [
                    "Pending Profiles",
                    ", ".join(workspace.pending.pending_profiles) or "none",
                ],
            ],
        )
    )

    return "\n".join(lines)


def cmd_verify_status() -> int:
    loader = WorkspaceLoader()
    workspace = loader.load_verification_workspace()
    print(render_verification(workspace))
    return 0
