"""Certification Progress — Program 13.

Tracks certification progress over time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROGRESS_PATH = REPO_ROOT / "runtime" / "generated" / "certification-progress.json"
DASHBOARD_PATH = REPO_ROOT / "runtime" / "generated" / "certification-dashboard.json"
HISTORY_PATH = REPO_ROOT / "runtime" / "generated" / "certification-history.json"


@dataclass(frozen=True, slots=True)
class CertificationSnapshot:
    timestamp: str
    overall_status: str
    certification_status: str
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    sections_passed: int
    sections_total: int
    duration_seconds: float


def _load_progress() -> list[dict[str, Any]]:
    if PROGRESS_PATH.exists():
        try:
            return json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return []


def _load_history() -> list[dict[str, Any]]:
    if HISTORY_PATH.exists():
        try:
            return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return []


def record_progress(snapshot: CertificationSnapshot) -> None:
    progress = _load_progress()
    history = _load_history()

    progress.append({
        "timestamp": snapshot.timestamp,
        "overall_status": snapshot.overall_status,
        "certification_status": snapshot.certification_status,
        "critical_count": snapshot.critical_count,
        "high_count": snapshot.high_count,
        "medium_count": snapshot.medium_count,
        "low_count": snapshot.low_count,
        "sections_passed": snapshot.sections_passed,
        "sections_total": snapshot.sections_total,
        "duration_seconds": snapshot.duration_seconds,
    })

    history.append({
        "timestamp": snapshot.timestamp,
        "event": "certification_audit",
        "critical_count": snapshot.critical_count,
        "high_count": snapshot.high_count,
        "overall_status": snapshot.overall_status,
        "certification_status": snapshot.certification_status,
    })

    PROGRESS_PATH.write_text(json.dumps(progress, indent=2), encoding="utf-8")
    HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")


def generate_dashboard() -> dict[str, Any]:
    progress = _load_progress()
    if not progress:
        return {"status": "no_data"}

    latest = progress[-1]
    previous = progress[-2] if len(progress) >= 2 else None

    critical_delta = 0
    high_delta = 0
    if previous:
        critical_delta = previous["critical_count"] - latest["critical_count"]
        high_delta = previous["high_count"] - latest["high_count"]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "current_snapshot": {
            "timestamp": latest["timestamp"],
            "overall_status": latest["overall_status"],
            "certification_status": latest["certification_status"],
            "critical_count": latest["critical_count"],
            "high_count": latest["high_count"],
            "medium_count": latest["medium_count"],
            "low_count": latest["low_count"],
            "sections_passed": latest["sections_passed"],
            "sections_total": latest["sections_total"],
        },
        "progress": {
            "critical_delta": critical_delta,
            "high_delta": high_delta,
            "trend": "improving" if (critical_delta > 0 or high_delta > 0) else "stable" if (critical_delta == 0 and high_delta == 0) else "regressing",
        },
        "total_audits": len(progress),
    }


def save_dashboard() -> dict[str, Any]:
    dashboard = generate_dashboard()
    DASHBOARD_PATH.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
    return dashboard


def run_certification_tracking(audit_report: Any) -> None:
    critical_count = len(audit_report.critical_issues)
    high_count = len(audit_report.high_priority_issues)
    medium_count = len(audit_report.medium_priority_issues)
    low_count = len(audit_report.low_priority_issues)
    sections_passed = sum(1 for s in audit_report.sections if s.status.value == "pass")
    sections_total = len(audit_report.sections)

    snapshot = CertificationSnapshot(
        timestamp=audit_report.generated_at,
        overall_status=audit_report.overall_status.value,
        certification_status=audit_report.certification_status,
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        sections_passed=sections_passed,
        sections_total=sections_total,
        duration_seconds=audit_report.total_duration_seconds,
    )
    record_progress(snapshot)
    save_dashboard()


if __name__ == "__main__":
    dashboard = generate_dashboard()
    print(json.dumps(dashboard, indent=2))
