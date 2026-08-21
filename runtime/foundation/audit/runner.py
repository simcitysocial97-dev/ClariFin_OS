"""Audit Runner — Program 12.

Orchestrates all audit sections and produces the Engineering Platform Certification Audit.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.foundation.audit.models import (
    AuditFinding,
    AuditPriority,
    AuditReport,
    AuditSectionResult,
    AuditSeverity,
    AuditStatus,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
AUDIT_OUTPUT_DIR = REPO_ROOT / "runtime" / "generated"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class _SectionRunner:
    name: str
    fn: Any

    def run(self) -> AuditSectionResult:
        start = time.monotonic()
        try:
            result = self.fn()
            if isinstance(result, AuditSectionResult):
                return result
            findings_raw = result.get("findings", [])
            findings = []
            for f in findings_raw:
                if isinstance(f, AuditFinding):
                    findings.append(f)
                elif isinstance(f, dict):
                    findings.append(
                        AuditFinding(
                            section=f.get("section", self.name),
                            check_id=f.get("check_id", ""),
                            name=f.get("name", ""),
                            status=AuditStatus(f.get("status", "fail")),
                            severity=AuditSeverity(f.get("severity", "info")),
                            priority=AuditPriority(f.get("priority", "low")),
                            message=f.get("message", ""),
                            details=f.get("details", {}),
                            recommendation=f.get("recommendation", ""),
                        )
                    )
            status = AuditStatus(result.get("status", "fail"))
            metrics = result.get("metrics", {})
            duration = result.get("duration_seconds", time.monotonic() - start)
            return AuditSectionResult(
                section=result.get("section", self.name),
                name=result.get("name", self.name),
                status=status,
                findings=tuple(findings),
                duration_seconds=duration,
                metrics=metrics,
            )
        except Exception as exc:
            return AuditSectionResult(
                section=self.name,
                name=self.name,
                status=AuditStatus.FAIL,
                findings=tuple(
                    [
                        AuditFinding(
                            section=self.name,
                            check_id="runner-error",
                            name="Section execution error",
                            status=AuditStatus.FAIL,
                            severity=AuditSeverity.CRITICAL,
                            priority=AuditPriority.CRITICAL,
                            message=str(exc),
                        )
                    ]
                ),
                duration_seconds=time.monotonic() - start,
            )


class AuditRunner:
    def __init__(self, repo_root: Path | None = None):
        self._repo_root = repo_root or REPO_ROOT
        self._sections: list[_SectionRunner] = []

    def register(self, name: str, fn: Any) -> "AuditRunner":
        self._sections.append(_SectionRunner(name=name, fn=fn))
        return self

    def run(self) -> AuditReport:
        start = time.monotonic()
        section_results: list[AuditSectionResult] = []
        for runner in self._sections:
            section_results.append(runner.run())

        all_findings: list[AuditFinding] = []
        for sr in section_results:
            all_findings.extend(sr.findings)

        critical = tuple(
            f
            for f in all_findings
            if f.priority == AuditPriority.CRITICAL and f.status == AuditStatus.FAIL
        )
        high = tuple(
            f
            for f in all_findings
            if f.priority == AuditPriority.HIGH and f.status == AuditStatus.FAIL
        )
        medium = tuple(
            f
            for f in all_findings
            if f.priority == AuditPriority.MEDIUM and f.status == AuditStatus.FAIL
        )
        low = tuple(
            f
            for f in all_findings
            if f.priority == AuditPriority.LOW and f.status == AuditStatus.FAIL
        )

        overall = AuditStatus.PASS
        if critical:
            overall = AuditStatus.FAIL
        elif high:
            overall = AuditStatus.WARNING

        certification_details: dict[str, AuditStatus] = {}
        for sr in section_results:
            certification_details[sr.section] = sr.status

        return AuditReport(
            generated_at=_now_iso(),
            overall_status=overall,
            sections=tuple(section_results),
            critical_issues=critical,
            high_priority_issues=high,
            medium_priority_issues=medium,
            low_priority_issues=low,
            total_duration_seconds=time.monotonic() - start,
            certification_status=(
                "CERTIFIED" if not critical and not high else "NOT_CERTIFIED"
            ),
            certification_details=certification_details,
        )
