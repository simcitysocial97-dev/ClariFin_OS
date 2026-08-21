"""Audit Normalization — Program 13.

Converts raw audit findings into immutable structured issues.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
NORMALIZED_PATH = REPO_ROOT / "runtime" / "generated" / "normalized-issues.json"


@dataclass(frozen=True, slots=True)
class NormalizedIssue:
    issue_id: str
    severity: str
    subsystem: str
    pipeline_stage: str
    owner: str
    root_cause: str
    evidence: str
    impact: str
    repair_plan: str
    verification_command: str
    regression_test: str
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    estimated_complexity: str = "medium"
    expected_downstream_benefit: str = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_finding(finding: dict[str, Any], section: str) -> NormalizedIssue:
    check_id = finding.get("check_id", "")
    name = finding.get("name", "")
    message = finding.get("message", "")
    severity = finding.get("severity", "medium")
    priority = finding.get("priority", "medium")
    recommendation = finding.get("recommendation", "")
    details = finding.get("details", {})

    issue_id = f"ISS-{section.upper()}-{check_id.upper()}"

    if section == "repository":
        return NormalizedIssue(
            issue_id=issue_id,
            severity=severity,
            subsystem="repository",
            pipeline_stage="repository_scanner",
            owner="platform",
            root_cause=_infer_repository_root_cause(name, message, details),
            evidence=message,
            impact=_infer_repository_impact(name, message),
            repair_plan=recommendation
            or "Fix repository scanner or generated artifacts",
            verification_command="python runtime/verify.py graph",
            regression_test="python3 -c 'from runtime.foundation.repository.builder.builder import RepositoryBuilder; b=RepositoryBuilder(); b.build(); print(b.validate().is_valid())'",
            dependencies=(),
            estimated_complexity=(
                "high"
                if "referential integrity" in name.lower()
                or "reproducibility" in name.lower()
                else "medium"
            ),
            expected_downstream_benefit="Cross-layer and dependency graph audits will pass once repository index is clean",
        )

    if section == "cross_layer":
        return NormalizedIssue(
            issue_id=issue_id,
            severity=severity,
            subsystem="cross_layer",
            pipeline_stage="cross_layer_generator",
            owner="platform",
            root_cause=_infer_cross_layer_root_cause(name, message, details),
            evidence=message,
            impact=_infer_cross_layer_impact(name, message),
            repair_plan=recommendation
            or "Regenerate cross-layer map with deduplication and completeness checks",
            verification_command="python runtime/verify.py graph",
            regression_test='python3 -c \'import json; m=json.load(open("runtime/generated/cross-layer-map.json")); print(len(m), "chains")\'',
            dependencies=("repository",),
            estimated_complexity="medium",
            expected_downstream_benefit="Knowledge base and diagnostics will have accurate dependency chains",
        )

    if section == "dependency_graph":
        return NormalizedIssue(
            issue_id=issue_id,
            severity=severity,
            subsystem="dependency_graph",
            pipeline_stage="graph_service",
            owner="platform",
            root_cause=_infer_dependency_graph_root_cause(name, message, details),
            evidence=message,
            impact=_infer_dependency_graph_impact(name, message),
            repair_plan=recommendation
            or "Rebuild dependency graph from clean repository index",
            verification_command="python runtime/verify.py graph",
            regression_test="python3 -c 'from runtime.foundation.repository.graph.graph_service import RepositoryGraphService; s=RepositoryGraphService(); print(s.validate())'",
            dependencies=("repository", "cross_layer"),
            estimated_complexity="high",
            expected_downstream_benefit="Impact analysis and blast radius calculations will be accurate",
        )

    if section == "executor":
        return NormalizedIssue(
            issue_id=issue_id,
            severity=severity,
            subsystem="executor",
            pipeline_stage="verification_executor",
            owner="runtime",
            root_cause=_infer_executor_root_cause(name, message, details),
            evidence=message,
            impact=_infer_executor_impact(name, message),
            repair_plan=recommendation or "Implement missing executor capability",
            verification_command="python runtime/verify.py quick",
            regression_test="python3 -c 'from runtime.foundation.verification.executor import Executor; e=Executor(); print(e.execute(\"echo test\").status.value)'",
            dependencies=(),
            estimated_complexity=(
                "high"
                if "parallel" in name.lower() or "retry" in name.lower()
                else "medium"
            ),
            expected_downstream_benefit="Verification runtime will be more resilient and efficient",
        )

    if section == "knowledge":
        return NormalizedIssue(
            issue_id=issue_id,
            severity=severity,
            subsystem="knowledge",
            pipeline_stage="knowledge_indexer",
            owner="platform",
            root_cause=_infer_knowledge_root_cause(name, message, details),
            evidence=message,
            impact=_infer_knowledge_impact(name, message),
            repair_plan=recommendation
            or "Rebuild knowledge index from valid runtime artifacts",
            verification_command="python runtime/verify.py knowledge",
            regression_test="python3 -c 'from runtime.foundation.knowledge.indexer import build_index; idx=build_index(); print(idx.total_entries, \"entries\")'",
            dependencies=("cross_layer",),
            estimated_complexity="medium",
            expected_downstream_benefit="Diagnostics and workspace queries will return correct results",
        )

    if section == "runtime_cli":
        return NormalizedIssue(
            issue_id=issue_id,
            severity=severity,
            subsystem="runtime_cli",
            pipeline_stage="cli_entry_point",
            owner="runtime",
            root_cause="Missing dashboard command implementation",
            evidence=message,
            impact="Users cannot access dashboard via CLI",
            repair_plan=recommendation
            or "Implement dashboard command or remove from audit scope",
            verification_command="python runtime/verify.py dashboard",
            regression_test='python3 -c \'import sys; sys.argv=["verify.py", "dashboard"]\'',
            dependencies=(),
            estimated_complexity="low",
            expected_downstream_benefit="CLI command coverage is complete",
        )

    if section == "github_runtime":
        return NormalizedIssue(
            issue_id=issue_id,
            severity=severity,
            subsystem="github_actions",
            pipeline_stage="ci_workflows",
            owner="platform",
            root_cause="Workflow missing artifact upload step",
            evidence=message,
            impact="Verification results are not available as CI artifacts for downstream consumption",
            repair_plan=recommendation or "Add artifact upload step to workflow",
            verification_command="python runtime/verify.py ci-doctor",
            regression_test="python3 .github/scripts/validate_actions.py",
            dependencies=(),
            estimated_complexity="low",
            expected_downstream_benefit="CI artifacts are properly published and retained",
        )

    if section == "artifact_ownership":
        return NormalizedIssue(
            issue_id=issue_id,
            severity=severity,
            subsystem="artifact_ownership",
            pipeline_stage="artifact_management",
            owner="platform",
            root_cause="Sample artifacts exist in multiple locations causing potential overwrites",
            evidence=message,
            impact="Artifact collisions may cause data loss or incorrect reporting",
            repair_plan=recommendation
            or "Consolidate sample artifacts into single canonical location",
            verification_command="python runtime/verify.py audit",
            regression_test='python3 -c \'from pathlib import Path; files=list(Path("runtime/generated").rglob("*")); print(len(files), "files")\'',
            dependencies=(),
            estimated_complexity="low",
            expected_downstream_benefit="Artifact ownership is unambiguous",
        )

    return NormalizedIssue(
        issue_id=issue_id,
        severity=severity,
        subsystem=section,
        pipeline_stage=section,
        owner="platform",
        root_cause=message,
        evidence=message,
        impact="Platform certification blocked",
        repair_plan=recommendation or "Investigate and fix",
        verification_command="python runtime/verify.py audit",
        regression_test="",
        dependencies=(),
        estimated_complexity="medium",
        expected_downstream_benefit="Certification progress",
    )


def _infer_repository_root_cause(
    name: str, message: str, details: dict[str, Any]
) -> str:
    if "referential integrity" in name.lower():
        return (
            "Scanner generates edges referencing nodes that do not exist in the graph"
        )
    if "reproducibility" in name.lower():
        return "Fresh graph build produces errors, indicating scanner or builder bugs"
    if "count consistency" in name.lower():
        return "Declared edge count does not match actual edges in index.json"
    return "Repository scanner or index builder defect"


def _infer_repository_impact(name: str, message: str) -> str:
    if "referential integrity" in name.lower():
        return "Cross-layer map and dependency graph are unreliable; downstream audits will fail"
    if "reproducibility" in name.lower():
        return (
            "Repository index cannot be regenerated; platform state is non-reproducible"
        )
    return "Repository discovery is incomplete or incorrect"


def _infer_cross_layer_root_cause(
    name: str, message: str, details: dict[str, Any]
) -> str:
    if "duplicate" in name.lower():
        return "Cross-layer map generator does not deduplicate endpoints across chains"
    if "ownership" in name.lower():
        return "Cross-layer map generator does not populate all required chain fields"
    return "Cross-layer map generation is incomplete"


def _infer_cross_layer_impact(name: str, message: str) -> str:
    if "duplicate" in name.lower():
        return "Diagnostics may report incorrect blast radius due to duplicate mappings"
    if "ownership" in name.lower():
        return (
            "Knowledge base and impact analysis have missing capability/router mappings"
        )
    return "Cross-layer dependency tracking is unreliable"


def _infer_dependency_graph_root_cause(
    name: str, message: str, details: dict[str, Any]
) -> str:
    if "referential integrity" in name.lower():
        return "Graph contains edges referencing non-existent nodes"
    if "structural" in name.lower():
        return "Graph has duplicate nodes or invalid edge relationships"
    if "isolated" in name.lower():
        return "Many nodes are unreachable from the graph root"
    return "Dependency graph construction has defects"


def _infer_dependency_graph_impact(name: str, message: str) -> str:
    if "referential integrity" in name.lower():
        return "Graph traversal produces errors; impact analysis is unreliable"
    if "structural" in name.lower():
        return "Graph queries return incorrect or incomplete results"
    if "isolated" in name.lower():
        return "Significant portion of repository is invisible to impact analysis"
    return "Dependency analysis is incorrect"


def _infer_executor_root_cause(name: str, message: str, details: dict[str, Any]) -> str:
    if "retry" in name.lower():
        return "Executor does not implement retry logic for transient command failures"
    if "cancel" in name.lower():
        return "Executor does not support cancellation of long-running commands"
    if "parallel" in name.lower():
        return "Executor runs commands sequentially, missing optimization opportunity"
    if "formats command correctly" in name.lower():
        return "Executor command formatting method produces incorrect command strings"
    return "Executor capability gap"


def _infer_executor_impact(name: str, message: str) -> str:
    if "retry" in name.lower():
        return "Transient CI failures cause unnecessary verification failures"
    if "cancel" in name.lower():
        return "Users cannot interrupt long-running verification profiles"
    if "parallel" in name.lower():
        return "Verification takes longer than necessary"
    if "formats command correctly" in name.lower():
        return "Commands may fail due to incorrect argument quoting or path handling"
    return "Verification execution is less reliable than expected"


def _infer_knowledge_root_cause(
    name: str, message: str, details: dict[str, Any]
) -> str:
    if "broken link" in name.lower():
        return "Knowledge index contains references to files or endpoints that do not exist"
    if "indexer consistency" in name.lower():
        return "Knowledge indexer count does not match rebuilt index, indicating stale or missing entries"
    return "Knowledge base has data quality issues"


def _infer_knowledge_impact(name: str, message: str) -> str:
    if "broken link" in name.lower():
        return "Workspace queries and diagnostics return invalid references"
    if "indexer consistency" in name.lower():
        return "Knowledge base may be out of sync with runtime artifacts"
    return "Knowledge queries are unreliable"


def normalize(findings: list[dict[str, Any]], section: str) -> list[dict[str, Any]]:
    issues = []
    for f in findings:
        issue = _normalize_finding(f, section)
        issues.append(
            {
                "issue_id": issue.issue_id,
                "severity": issue.severity,
                "subsystem": issue.subsystem,
                "pipeline_stage": issue.pipeline_stage,
                "owner": issue.owner,
                "root_cause": issue.root_cause,
                "evidence": issue.evidence,
                "impact": issue.impact,
                "repair_plan": issue.repair_plan,
                "verification_command": issue.verification_command,
                "regression_test": issue.regression_test,
                "dependencies": list(issue.dependencies),
                "estimated_complexity": issue.estimated_complexity,
                "expected_downstream_benefit": issue.expected_downstream_benefit,
            }
        )
    return issues


def run_normalization() -> dict[str, Any]:
    with open(
        REPO_ROOT / "runtime" / "generated" / "engineering-platform-audit.json",
        encoding="utf-8",
    ) as f:
        audit_data = json.load(f)

    all_issues = []
    section_summaries = {}

    for section in audit_data.get("sections", []):
        section_name = section.get("section", "")
        findings = section.get("findings", [])
        section_issues = normalize(findings, section_name)
        all_issues.extend(section_issues)
        section_summaries[section_name] = {
            "total_findings": len(findings),
            "normalized_issues": len(section_issues),
            "critical": sum(1 for i in section_issues if i["severity"] == "critical"),
            "high": sum(1 for i in section_issues if i["severity"] == "high"),
            "medium": sum(1 for i in section_issues if i["severity"] == "medium"),
            "low": sum(1 for i in section_issues if i["severity"] == "low"),
        }

    output = {
        "generated_at": _now_iso(),
        "total_issues": len(all_issues),
        "critical_count": sum(1 for i in all_issues if i["severity"] == "critical"),
        "high_count": sum(1 for i in all_issues if i["severity"] == "high"),
        "medium_count": sum(1 for i in all_issues if i["severity"] == "medium"),
        "low_count": sum(1 for i in all_issues if i["severity"] == "low"),
        "sections": section_summaries,
        "issues": all_issues,
    }

    NORMALIZED_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


if __name__ == "__main__":
    result = run_normalization()
    print(f"Normalized {result['total_issues']} issues")
    print(
        f"Critical: {result['critical_count']}, High: {result['high_count']}, Medium: {result['medium_count']}, Low: {result['low_count']}"
    )
