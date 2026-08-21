"""Audit Reporter — Program 12.

Generates JSON and Markdown reports from AuditReport.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPORT_JSON = Path("runtime/generated/engineering-platform-audit.json")
REPORT_MD = Path("runtime/generated/engineering-platform-audit.md")
PIPELINE_JSON = Path("runtime/generated/pipeline-validation.json")
CERT_MD = Path("runtime/generated/pipeline-certification.md")
DEFECTS_JSON = Path("runtime/generated/runtime-defects.json")
GITHUB_HEALTH_JSON = Path("runtime/generated/github-actions-health.json")
ARTIFACT_OWNERSHIP_JSON = Path("runtime/generated/artifact-ownership.json")
DEPENDENCY_HEALTH_JSON = Path("runtime/generated/dependency-health.json")
SYSTEM_HEALTH_JSON = Path("runtime/generated/system-health-score.json")


class AuditReporter:
    def __init__(self, report: Any):
        self._report = report

    def save_all(self, repo_root: Path | None = None) -> dict[str, Path]:
        root = repo_root or Path(".")
        paths = {
            "json": root / REPORT_JSON,
            "markdown": root / REPORT_MD,
            "pipeline": root / PIPELINE_JSON,
            "certification": root / CERT_MD,
            "defects": root / DEFECTS_JSON,
            "github_health": root / GITHUB_HEALTH_JSON,
            "artifact_ownership": root / ARTIFACT_OWNERSHIP_JSON,
            "dependency_health": root / DEPENDENCY_HEALTH_JSON,
            "system_health": root / SYSTEM_HEALTH_JSON,
        }
        for p in paths.values():
            p.parent.mkdir(parents=True, exist_ok=True)

        paths["json"].write_text(self._to_json(), encoding="utf-8")
        paths["markdown"].write_text(self._to_markdown(), encoding="utf-8")
        paths["pipeline"].write_text(self._to_pipeline_json(), encoding="utf-8")
        paths["certification"].write_text(self._to_certification_md(), encoding="utf-8")
        paths["defects"].write_text(self._to_defects_json(), encoding="utf-8")
        paths["github_health"].write_text(
            self._to_github_health_json(), encoding="utf-8"
        )
        paths["artifact_ownership"].write_text(
            self._to_artifact_ownership_json(), encoding="utf-8"
        )
        paths["dependency_health"].write_text(
            self._to_dependency_health_json(), encoding="utf-8"
        )
        paths["system_health"].write_text(
            self._to_system_health_json(), encoding="utf-8"
        )
        return paths

    def _to_json(self) -> str:
        data = {
            "generated_at": self._report.generated_at,
            "overall_status": self._report.overall_status.value,
            "certification_status": self._report.certification_status,
            "total_duration_seconds": round(self._report.total_duration_seconds, 2),
            "sections": [
                {
                    "section": s.section,
                    "name": s.name,
                    "status": s.status.value,
                    "duration_seconds": round(s.duration_seconds, 2),
                    "metrics": s.metrics,
                    "findings": [
                        {
                            "section": f.section,
                            "check_id": f.check_id,
                            "name": f.name,
                            "status": f.status.value,
                            "severity": f.severity.value,
                            "priority": f.priority.value,
                            "message": f.message,
                            "details": f.details,
                            "recommendation": f.recommendation,
                        }
                        for f in s.findings
                    ],
                }
                for s in self._report.sections
            ],
            "critical_issues": [
                {
                    "section": f.section,
                    "check_id": f.check_id,
                    "name": f.name,
                    "status": f.status.value,
                    "severity": f.severity.value,
                    "priority": f.priority.value,
                    "message": f.message,
                    "details": f.details,
                    "recommendation": f.recommendation,
                }
                for f in self._report.critical_issues
            ],
            "high_priority_issues": [
                {
                    "section": f.section,
                    "check_id": f.check_id,
                    "name": f.name,
                    "status": f.status.value,
                    "severity": f.severity.value,
                    "priority": f.priority.value,
                    "message": f.message,
                    "details": f.details,
                    "recommendation": f.recommendation,
                }
                for f in self._report.high_priority_issues
            ],
            "medium_priority_issues": [
                {
                    "section": f.section,
                    "check_id": f.check_id,
                    "name": f.name,
                    "status": f.status.value,
                    "severity": f.severity.value,
                    "priority": f.priority.value,
                    "message": f.message,
                    "details": f.details,
                    "recommendation": f.recommendation,
                }
                for f in self._report.medium_priority_issues
            ],
            "low_priority_issues": [
                {
                    "section": f.section,
                    "check_id": f.check_id,
                    "name": f.name,
                    "status": f.status.value,
                    "severity": f.severity.value,
                    "priority": f.priority.value,
                    "message": f.message,
                    "details": f.details,
                    "recommendation": f.recommendation,
                }
                for f in self._report.low_priority_issues
            ],
            "certification_details": {
                k: v.value for k, v in self._report.certification_details.items()
            },
        }
        return json.dumps(data, indent=2)

    def _to_markdown(self) -> str:
        lines: list[str] = []
        lines.append("# Engineering Platform Certification Audit")
        lines.append("")
        lines.append(f"**Generated:** {self._report.generated_at}")
        lines.append(f"**Overall Status:** {self._report.overall_status.value}")
        lines.append(f"**Certification:** {self._report.certification_status}")
        lines.append(f"**Duration:** {self._report.total_duration_seconds:.2f}s")
        lines.append("")

        lines.append("## Executive Summary")
        lines.append("")
        lines.append(
            "This audit validates every engineering subsystem works together in practice."
        )
        lines.append(f"Certification status: **{self._report.certification_status}**.")
        lines.append("")

        if self._report.critical_issues:
            lines.append("### Critical Issues")
            lines.append("")
            for f in self._report.critical_issues:
                lines.append(f"- **{f.name}**: {f.message}")
            lines.append("")

        if self._report.high_priority_issues:
            lines.append("### High-Priority Issues")
            lines.append("")
            for f in self._report.high_priority_issues:
                lines.append(f"- **{f.name}**: {f.message}")
            lines.append("")

        if self._report.medium_priority_issues:
            lines.append("### Medium/Low-Priority Improvements")
            lines.append("")
            for f in self._report.medium_priority_issues:
                lines.append(f"- **{f.name}**: {f.message}")
            for f in self._report.low_priority_issues:
                lines.append(f"- **{f.name}**: {f.message}")
            lines.append("")

        lines.append("## Section Results")
        lines.append("")
        for s in self._report.sections:
            status_icon = (
                "PASS"
                if s.status == "pass"
                else "FAIL" if s.status == "fail" else "WARN"
            )
            lines.append(f"### {s.name}")
            lines.append(f"- **Status:** {status_icon}")
            lines.append(f"- **Duration:** {s.duration_seconds:.2f}s")
            if s.metrics:
                for k, v in s.metrics.items():
                    lines.append(f"- **{k}:** {v}")
            lines.append("")
            for f in s.findings:
                lines.append(f"- [{f.status.value.upper()}] {f.name}: {f.message}")
            lines.append("")

        return "\n".join(lines)

    def _to_pipeline_json(self) -> str:
        data = {
            "pipeline_stages": [],
            "overall_status": self._report.overall_status.value,
        }
        for s in self._report.sections:
            data["pipeline_stages"].append(
                {
                    "stage": s.section,
                    "name": s.name,
                    "status": s.status.value,
                    "duration_seconds": round(s.duration_seconds, 2),
                    "findings_count": len(s.findings),
                    "passed": sum(1 for f in s.findings if f.status == "pass"),
                    "failed": sum(1 for f in s.findings if f.status == "fail"),
                }
            )
        return json.dumps(data, indent=2)

    def _to_certification_md(self) -> str:
        lines: list[str] = []
        lines.append("# Engineering Platform Certification")
        lines.append("")
        lines.append(f"**Generated:** {self._report.generated_at}")
        lines.append(f"**Status:** {self._report.certification_status}")
        lines.append("")
        lines.append("| Section | Status |")
        lines.append("|---------|--------|")
        for s in self._report.sections:
            lines.append(f"| {s.name} | {s.status.value.upper()} |")
        lines.append("")
        return "\n".join(lines)

    def _to_defects_json(self) -> str:
        defects = []
        for s in self._report.sections:
            for f in s.findings:
                if f.status == "fail":
                    defects.append(
                        {
                            "section": f.section,
                            "check_id": f.check_id,
                            "name": f.name,
                            "severity": f.severity.value,
                            "priority": f.priority.value,
                            "message": f.message,
                            "recommendation": f.recommendation,
                            "details": f.details,
                        }
                    )
        return json.dumps({"defects": defects, "total": len(defects)}, indent=2)

    def _to_github_health_json(self) -> str:
        gh_section = next(
            (s for s in self._report.sections if s.section == "github_actions"), None
        )
        data = {"overall_status": "unknown", "findings": []}
        if gh_section:
            data["overall_status"] = gh_section.status.value
            data["findings"] = [
                {
                    "name": f.name,
                    "status": f.status.value,
                    "message": f.message,
                }
                for f in gh_section.findings
            ]
        return json.dumps(data, indent=2)

    def _to_artifact_ownership_json(self) -> str:
        ao_section = next(
            (s for s in self._report.sections if s.section == "artifact_ownership"),
            None,
        )
        data = {"overall_status": "unknown", "artifacts": []}
        if ao_section:
            data["overall_status"] = ao_section.status.value
            data["artifacts"] = [
                {
                    "name": f.name,
                    "status": f.status.value,
                    "details": f.details,
                }
                for f in ao_section.findings
            ]
        return json.dumps(data, indent=2)

    def _to_dependency_health_json(self) -> str:
        dg_section = next(
            (s for s in self._report.sections if s.section == "dependency_graph"), None
        )
        data = {"overall_status": "unknown", "graph_health": {}}
        if dg_section:
            data["overall_status"] = dg_section.status.value
            data["graph_health"] = dg_section.metrics
        return json.dumps(data, indent=2)

    def _to_system_health_json(self) -> str:
        data = {
            "overall_status": self._report.overall_status.value,
            "certification_status": self._report.certification_status,
            "total_duration_seconds": round(self._report.total_duration_seconds, 2),
            "section_statuses": {
                s.section: s.status.value for s in self._report.sections
            },
            "critical_count": len(self._report.critical_issues),
            "high_count": len(self._report.high_priority_issues),
            "medium_count": len(self._report.medium_priority_issues),
            "low_count": len(self._report.low_priority_issues),
        }
        return json.dumps(data, indent=2)
