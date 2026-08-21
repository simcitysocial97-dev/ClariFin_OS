"""History Workspace — Program 9.

Command: python runtime/verify.py history

Display recent verification events, recent failures, recent engineering
reports, timeline, and verification trends. No analytics generation.
Only presentation.
"""

from __future__ import annotations


from runtime.foundation.workspace.formatter import (
    format_duration,
    format_status,
    render_section,
    render_table,
)
from runtime.foundation.workspace.models import VerificationHistory
from runtime.foundation.workspace.workspace import WorkspaceLoader


def render_history(history: VerificationHistory) -> str:
    lines: list[str] = []

    all_events = history.combined[:20]

    if all_events:
        lines.append(render_section("Recent Verification Events"))
        rows = [
            [
                e.run_id[:12],
                e.timestamp,
                e.environment,
                e.profile,
                format_status(e.status),
                str(e.passed),
                str(e.failed),
                format_duration(e.duration_seconds),
            ]
            for e in all_events
        ]
        lines.append(
            render_table(
                [
                    "Run ID",
                    "Timestamp",
                    "Env",
                    "Profile",
                    "Status",
                    "Pass",
                    "Fail",
                    "Duration",
                ],
                rows,
            )
        )

    failures = [e for e in all_events if e.status == "failed"]
    if failures:
        lines.append(render_section("Recent Failures"))
        rows = [
            [e.run_id[:12], e.timestamp, e.profile, str(e.failed), e.environment]
            for e in failures
        ]
        lines.append(
            render_table(["Run ID", "Timestamp", "Profile", "Failed", "Env"], rows)
        )

    if all_events:
        lines.append(render_section("Timeline"))
        rows = [
            [
                e.timestamp[:19],
                f"{e.profile} ({e.environment})",
                format_status(e.status),
            ]
            for e in all_events
        ]
        lines.append(render_table(["Timestamp", "Profile", "Status"], rows))

        lines.append(render_section("Verification Trends"))
        total = len(all_events)
        passed = sum(1 for e in all_events if e.status == "passed")
        failed = sum(1 for e in all_events if e.status == "failed")
        avg_dur = sum(e.duration_seconds for e in all_events) / total if total else 0.0
        lines.append(
            render_table(
                ["Metric", "Value"],
                [
                    ["Total Events", str(total)],
                    ["Passed", str(passed)],
                    ["Failed", str(failed)],
                    [
                        "Success Rate",
                        f"{(passed / total * 100.0) if total else 0.0:.1f}%",
                    ],
                    ["Avg Duration", format_duration(avg_dur)],
                ],
            )
        )

    return "\n".join(lines)


def cmd_history() -> int:
    loader = WorkspaceLoader()
    history = loader.load_history_events()
    print(render_history(history))
    return 0
