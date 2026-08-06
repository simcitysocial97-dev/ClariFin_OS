"""Root Cause Clustering — Program 13.

Clusters normalized audit issues into root cause groups.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CLUSTERS_PATH = REPO_ROOT / "runtime" / "generated" / "root-cause-clusters.json"


@dataclass(frozen=True, slots=True)
class RootCauseCluster:
    cluster_id: str
    name: str
    description: str
    root_cause: str
    issues: tuple[str, ...]
    subsystems: tuple[str, ...]
    pipeline_stages: tuple[str, ...]
    estimated_repair_complexity: str
    expected_benefit: str
    repair_strategy: str


def _cluster_key(issue: dict[str, Any]) -> str:
    subsystem = issue.get("subsystem", "")
    pipeline_stage = issue.get("pipeline_stage", "")
    root_cause = issue.get("root_cause", "")

    if "repository" in subsystem and ("referential integrity" in root_cause.lower() or "reproducibility" in root_cause.lower() or "count consistency" in root_cause.lower()):
        return "repository_graph_integrity"

    if "cross_layer" in subsystem and ("duplicate" in root_cause.lower() or "ownership" in root_cause.lower()):
        return "cross_layer_completeness"

    if "dependency_graph" in subsystem and ("referential integrity" in root_cause.lower() or "structural" in root_cause.lower() or "isolated" in root_cause.lower()):
        return "dependency_graph_integrity"

    if "executor" in subsystem and ("retry" in root_cause.lower() or "cancel" in root_cause.lower() or "parallel" in root_cause.lower()):
        return "executor_resilience"

    if "executor" in subsystem and "format" in root_cause.lower():
        return "executor_command_formatting"

    if "knowledge" in subsystem and ("broken link" in root_cause.lower() or "indexer consistency" in root_cause.lower()):
        return "knowledge_data_quality"

    if "runtime_cli" in subsystem and "dashboard" in root_cause.lower():
        return "cli_completeness"

    if "github_runtime" in subsystem or "github_actions" in subsystem:
        return "github_actions_completeness"

    if "artifact_ownership" in subsystem:
        return "artifact_organization"

    return "miscellaneous"


def _cluster_metadata(cluster_key: str) -> tuple[str, str, str, str, str]:
    mapping = {
        "repository_graph_integrity": (
            "Repository Graph Integrity",
            "Repository scanner generates invalid graph edges or fails to build a clean index",
            "Fix repository scanner and builder to produce referentially complete, reproducible graph",
            "high",
            "Unblocks cross-layer, dependency graph, and knowledge base audits",
        ),
        "cross_layer_completeness": (
            "Cross-Layer Map Completeness",
            "Cross-layer map has duplicate endpoints or incomplete chain ownership",
            "Regenerate cross-layer map with deduplication and completeness validation",
            "medium",
            "Diagnostics and impact analysis will have accurate dependency chains",
        ),
        "dependency_graph_integrity": (
            "Dependency Graph Integrity",
            "Dependency graph has structural errors, missing nodes, or excessive isolation",
            "Rebuild dependency graph from clean repository index",
            "high",
            "Impact analysis and blast radius calculations will be accurate",
        ),
        "executor_resilience": (
            "Executor Resilience",
            "Executor lacks retry, cancellation, and parallel execution support",
            "Implement retry, cancellation, and parallel execution in Executor",
            "high",
            "Verification runtime will be more resilient and efficient",
        ),
        "executor_command_formatting": (
            "Executor Command Formatting",
            "Executor command formatting methods produce incorrect command strings",
            "Fix command formatting in Executor methods",
            "medium",
            "All verification commands will execute correctly",
        ),
        "knowledge_data_quality": (
            "Knowledge Base Data Quality",
            "Knowledge index contains broken links or count mismatches",
            "Rebuild knowledge index from valid runtime artifacts",
            "medium",
            "Workspace queries and diagnostics will return correct results",
        ),
        "cli_completeness": (
            "CLI Completeness",
            "Runtime CLI is missing the dashboard command",
            "Implement dashboard command in runtime/verify.py",
            "low",
            "CLI command coverage is complete",
        ),
        "github_actions_completeness": (
            "GitHub Actions Completeness",
            "Workflows are missing artifact upload steps",
            "Add artifact upload steps to verification workflows",
            "low",
            "CI artifacts are properly published and retained",
        ),
        "artifact_organization": (
            "Artifact Organization",
            "Sample artifacts exist in multiple locations causing potential overwrites",
            "Consolidate sample artifacts into single canonical location",
            "low",
            "Artifact ownership is unambiguous",
        ),
    }
    return mapping.get(cluster_key, ("Miscellaneous", "Various issues", "Investigate individually", "medium", "Certification progress"))


def cluster_issues(issues: list[dict[str, Any]]) -> dict[str, Any]:
    clusters: dict[str, list[dict[str, Any]]] = {}
    for issue in issues:
        key = _cluster_key(issue)
        if key not in clusters:
            clusters[key] = []
        clusters[key].append(issue)

    result_clusters = []
    for key, cluster_issues in clusters.items():
        name, description, repair_strategy, complexity, benefit = _cluster_metadata(key)
        subsystems = tuple(sorted(set(i["subsystem"] for i in cluster_issues)))
        pipeline_stages = tuple(sorted(set(i["pipeline_stage"] for i in cluster_issues)))
        issue_ids = tuple(i["issue_id"] for i in cluster_issues)

        cluster = RootCauseCluster(
            cluster_id=f"CLUSTER-{key.upper()}",
            name=name,
            description=description,
            root_cause=cluster_issues[0]["root_cause"],
            issues=issue_ids,
            subsystems=subsystems,
            pipeline_stages=pipeline_stages,
            estimated_repair_complexity=complexity,
            expected_benefit=benefit,
            repair_strategy=repair_strategy,
        )
        result_clusters.append({
            "cluster_id": cluster.cluster_id,
            "name": cluster.name,
            "description": cluster.description,
            "root_cause": cluster.root_cause,
            "issues": list(cluster.issues),
            "subsystems": list(cluster.subsystems),
            "pipeline_stages": list(cluster.pipeline_stages),
            "estimated_repair_complexity": cluster.estimated_repair_complexity,
            "expected_benefit": cluster.expected_benefit,
            "repair_strategy": cluster.repair_strategy,
            "issue_count": len(cluster_issues),
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_clusters": len(result_clusters),
        "total_issues": sum(c["issue_count"] for c in result_clusters),
        "clusters": result_clusters,
    }


def run_clustering() -> dict[str, Any]:
    with open(REPO_ROOT / "runtime" / "generated" / "normalized-issues.json", encoding="utf-8") as f:
        normalized = json.load(f)

    issues = normalized.get("issues", [])
    result = cluster_issues(issues)

    CLUSTERS_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    result = run_clustering()
    print(f"Clustered {result['total_issues']} issues into {result['total_clusters']} root causes")
    for c in result["clusters"]:
        print(f"  {c['cluster_id']}: {c['name']} ({c['issue_count']} issues)")
