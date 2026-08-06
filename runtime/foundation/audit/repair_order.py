"""Repair Order — Program 13.

Generates the repair DAG based on root cause clusters.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REPAIR_ORDER_PATH = REPO_ROOT / "runtime" / "generated" / "repair-order.json"


REPAIR_DAG = [
    {
        "order": 1,
        "cluster_id": "CLUSTER-REPOSITORY_GRAPH_INTEGRITY",
        "name": "Repository Graph Integrity",
        "depends_on": [],
        "rationale": "All downstream subsystems depend on a clean repository index",
    },
    {
        "order": 2,
        "cluster_id": "CLUSTER-CROSS_LAYER_COMPLETENESS",
        "name": "Cross-Layer Map Completeness",
        "depends_on": ["CLUSTER-REPOSITORY_GRAPH_INTEGRITY"],
        "rationale": "Cross-layer map is built from repository index",
    },
    {
        "order": 3,
        "cluster_id": "CLUSTER-DEPENDENCY_GRAPH_INTEGRITY",
        "name": "Dependency Graph Integrity",
        "depends_on": ["CLUSTER-REPOSITORY_GRAPH_INTEGRITY", "CLUSTER-CROSS_LAYER_COMPLETENESS"],
        "rationale": "Dependency graph depends on clean repository and cross-layer data",
    },
    {
        "order": 4,
        "cluster_id": "CLUSTER-KNOWLEDGE_DATA_QUALITY",
        "name": "Knowledge Base Data Quality",
        "depends_on": ["CLUSTER-CROSS_LAYER_COMPLETENESS", "CLUSTER-DEPENDENCY_GRAPH_INTEGRITY"],
        "rationale": "Knowledge index is built from cross-layer map and repository artifacts",
    },
    {
        "order": 5,
        "cluster_id": "CLUSTER-EXECUTOR_COMMAND_FORMTING",
        "name": "Executor Command Formatting",
        "depends_on": [],
        "rationale": "Independent of graph issues; can be fixed in parallel",
    },
    {
        "order": 6,
        "cluster_id": "CLUSTER-EXECUTOR_RESILIENCE",
        "name": "Executor Resilience",
        "depends_on": ["CLUSTER-EXECUTOR_COMMAND_FORMTING"],
        "rationale": "Resilience features depend on correct command formatting",
    },
    {
        "order": 7,
        "cluster_id": "CLUSTER-CLI_COMPLETENESS",
        "name": "CLI Completeness",
        "depends_on": [],
        "rationale": "Independent feature gap",
    },
    {
        "order": 8,
        "cluster_id": "CLUSTER-GITHUB_ACTIONS_COMPLETENESS",
        "name": "GitHub Actions Completeness",
        "depends_on": [],
        "rationale": "Independent workflow configuration issue",
    },
    {
        "order": 9,
        "cluster_id": "CLUSTER-ARTIFACT_ORGANIZATION",
        "name": "Artifact Organization",
        "depends_on": [],
        "rationale": "Independent artifact management issue",
    },
]


def generate_repair_order() -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repair_dag": REPAIR_DAG,
        "total_clusters": len(REPAIR_DAG),
        "execution_phases": [
            {
                "phase": 1,
                "description": "Fix repository graph integrity",
                "clusters": ["CLUSTER-REPOSITORY_GRAPH_INTEGRITY"],
            },
            {
                "phase": 2,
                "description": "Fix cross-layer and dependency graph",
                "clusters": ["CLUSTER-CROSS_LAYER_COMPLETENESS", "CLUSTER-DEPENDENCY_GRAPH_INTEGRITY"],
            },
            {
                "phase": 3,
                "description": "Fix knowledge base",
                "clusters": ["CLUSTER-KNOWLEDGE_DATA_QUALITY"],
            },
            {
                "phase": 4,
                "description": "Fix executor formatting and resilience",
                "clusters": ["CLUSTER-EXECUTOR_COMMAND_FORMTING", "CLUSTER-EXECUTOR_RESILIENCE"],
            },
            {
                "phase": 5,
                "description": "Fix CLI, GitHub Actions, and artifacts",
                "clusters": ["CLUSTER-CLI_COMPLETENESS", "CLUSTER-GITHUB_ACTIONS_COMPLETENESS", "CLUSTER-ARTIFACT_ORGANIZATION"],
            },
        ],
    }


def run_repair_order() -> dict[str, Any]:
    result = generate_repair_order()
    REPAIR_ORDER_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    result = run_repair_order()
    print(f"Generated repair order with {result['total_clusters']} clusters")
    for phase in result["execution_phases"]:
        print(f"  Phase {phase['phase']}: {phase['description']}")
