"""Repository Index Audit — Program 12.

Verifies the canonical repository index (index.json) for structural integrity:
- Index file existence and JSON validity
- Graph build reproducibility (builder produces same graph as index)
- Node/edge uniqueness and referential integrity
- Ownership completeness
- Gap detection consistency
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _find_index_path(repo_root: Path | None = None) -> Path:
    root = repo_root or REPO_ROOT
    return root / "runtime" / "generated" / "repository" / "index.json"


def _load_index(index_path: Path) -> dict[str, Any]:
    if not index_path.exists():
        return {}
    return json.loads(index_path.read_text(encoding="utf-8"))


def _verify_index_existence(index_path: Path) -> dict[str, Any]:
    if index_path.exists():
        status = "pass"
        message = f"Index file exists at {index_path}"
    else:
        status = "fail"
        message = f"Index file not found at {index_path}"
    return {
        "section": "repository",
        "check_id": "repo-index-existence",
        "name": "Repository index file exists",
        "status": status,
        "severity": "critical" if status == "fail" else "info",
        "priority": "critical" if status == "fail" else "low",
        "message": message,
        "details": {"path": str(index_path), "exists": index_path.exists()},
        "recommendation": (
            ""
            if status == "pass"
            else "Run the repository index builder to generate index.json"
        ),
    }


def _verify_json_validity(index_path: Path) -> dict[str, Any]:
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
        status = "pass"
        message = "Index JSON is valid"
        details = {"top_level_keys": list(data.keys())}
    except (json.JSONDecodeError, OSError) as exc:
        status = "fail"
        message = f"Index JSON is invalid: {exc}"
        data = {}
        details = {"error": str(exc)}
    return {
        "section": "repository",
        "check_id": "repo-json-validity",
        "name": "Index JSON validity",
        "status": status,
        "severity": "critical" if status == "fail" else "info",
        "priority": "critical" if status == "fail" else "low",
        "message": message,
        "details": details,
        "recommendation": (
            "" if status == "pass" else "Fix JSON syntax errors in index.json"
        ),
    }


def _verify_metadata_completeness(data: dict[str, Any]) -> dict[str, Any]:
    meta = data.get("metadata", {})
    required_fields = [
        "schema_version",
        "generated_at",
        "repository_root",
        "node_count",
        "edge_count",
        "node_types",
        "edge_relationships",
        "ownership_classes",
        "validation_summary",
    ]
    missing = [f for f in required_fields if f not in meta]
    if missing:
        status = "fail"
        message = f"Metadata missing fields: {', '.join(missing)}"
    else:
        status = "pass"
        message = "All required metadata fields present"
    return {
        "section": "repository",
        "check_id": "repo-metadata-completeness",
        "name": "Metadata completeness",
        "status": status,
        "severity": "high" if status == "fail" else "info",
        "priority": "high" if status == "fail" else "low",
        "message": message,
        "details": {
            "missing_fields": missing,
            "present_fields": [f for f in required_fields if f in meta],
        },
        "recommendation": (
            ""
            if status == "pass"
            else f"Add missing metadata fields: {', '.join(missing)}"
        ),
    }


def _verify_node_count_consistency(data: dict[str, Any]) -> dict[str, Any]:
    meta = data.get("metadata", {})
    graph = data.get("graph", {})
    declared_nodes = meta.get("node_count", 0)
    actual_nodes = len(graph.get("nodes", []))
    declared_edges = meta.get("edge_count", 0)
    actual_edges = len(graph.get("edges", []))
    node_match = declared_nodes == actual_nodes
    edge_match = declared_edges == actual_edges
    if node_match and edge_match:
        status = "pass"
        message = f"Node count ({actual_nodes}) and edge count ({actual_edges}) are consistent"
    else:
        status = "fail"
        parts = []
        if not node_match:
            parts.append(f"nodes: declared={declared_nodes} actual={actual_nodes}")
        if not edge_match:
            parts.append(f"edges: declared={declared_edges} actual={actual_edges}")
        message = f"Counts inconsistent: {'; '.join(parts)}"
    return {
        "section": "repository",
        "check_id": "repo-count-consistency",
        "name": "Node and edge count consistency",
        "status": status,
        "severity": "high" if status == "fail" else "info",
        "priority": "high" if status == "fail" else "low",
        "message": message,
        "details": {
            "declared_nodes": declared_nodes,
            "actual_nodes": actual_nodes,
            "declared_edges": declared_edges,
            "actual_edges": actual_edges,
        },
        "recommendation": (
            "" if status == "pass" else "Regenerate the index to update metadata counts"
        ),
    }


def _verify_unique_node_ids(data: dict[str, Any]) -> dict[str, Any]:
    graph = data.get("graph", {})
    nodes = graph.get("nodes", [])
    node_ids = [n.get("id", "") for n in nodes]
    seen: set[str] = set()
    duplicates: list[str] = []
    for nid in node_ids:
        if nid in seen and nid not in duplicates:
            duplicates.append(nid)
        seen.add(nid)
    if not duplicates:
        status = "pass"
        message = f"All {len(nodes)} node IDs are unique"
    else:
        status = "fail"
        message = f"Found {len(duplicates)} duplicate node IDs"
    return {
        "section": "repository",
        "check_id": "repo-unique-node-ids",
        "name": "Unique node IDs",
        "status": status,
        "severity": "critical" if status == "fail" else "info",
        "priority": "critical" if status == "fail" else "low",
        "message": message,
        "details": {"duplicate_ids": duplicates[:50], "total_nodes": len(nodes)},
        "recommendation": (
            "" if status == "pass" else "Remove duplicate node entries from index.json"
        ),
    }


def _verify_edge_referential_integrity(data: dict[str, Any]) -> dict[str, Any]:
    graph = data.get("graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_ids = {n.get("id", "") for n in nodes}
    missing_sources: list[str] = []
    missing_targets: list[str] = []
    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        if src not in node_ids:
            missing_sources.append(src)
        if tgt not in node_ids:
            missing_targets.append(tgt)
    if not missing_sources and not missing_targets:
        status = "pass"
        message = f"All {len(edges)} edges reference existing nodes"
    else:
        status = "fail"
        message = f"Found {len(missing_sources)} edges with missing source, {len(missing_targets)} with missing target"
    return {
        "section": "repository",
        "check_id": "repo-edge-referential-integrity",
        "name": "Edge referential integrity",
        "status": status,
        "severity": "critical" if status == "fail" else "info",
        "priority": "critical" if status == "fail" else "low",
        "message": message,
        "details": {
            "total_edges": len(edges),
            "missing_sources": missing_sources[:50],
            "missing_targets": missing_targets[:50],
        },
        "recommendation": (
            "" if status == "pass" else "Remove or fix edges referencing missing nodes"
        ),
    }


def _verify_edge_deduplication(data: dict[str, Any]) -> dict[str, Any]:
    graph = data.get("graph", {})
    edges = graph.get("edges", [])
    seen: set[tuple[str, str, str]] = set()
    duplicates: list[tuple[str, str, str]] = []
    for e in edges:
        key = (e.get("source", ""), e.get("target", ""), e.get("relationship", ""))
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
    if not duplicates:
        status = "pass"
        message = f"All {len(edges)} edges are unique (no duplicates)"
    else:
        status = "fail"
        message = f"Found {len(duplicates)} duplicate edges"
    return {
        "section": "repository",
        "check_id": "repo-edge-deduplication",
        "name": "Edge deduplication",
        "status": status,
        "severity": "high" if status == "fail" else "info",
        "priority": "high" if status == "fail" else "low",
        "message": message,
        "details": {"duplicate_edges": duplicates[:50], "total_edges": len(edges)},
        "recommendation": "" if status == "pass" else "Deduplicate edges in index.json",
    }


def _verify_ownership_comprehensiveness(data: dict[str, Any]) -> dict[str, Any]:
    graph = data.get("graph", {})
    nodes = graph.get("nodes", [])
    valid_ownership = {
        "capability",
        "shared_infrastructure",
        "generated",
        "framework",
        "utility",
        "external",
        "unknown",
    }
    unknown_count = sum(1 for n in nodes if n.get("ownership", "unknown") == "unknown")
    invalid_ownership: list[str] = []
    for n in nodes:
        own = n.get("ownership", "unknown")
        if own not in valid_ownership:
            invalid_ownership.append(f"{n.get('id', '')}={own}")
    if invalid_ownership:
        status = "fail"
        message = f"Found {len(invalid_ownership)} nodes with invalid ownership"
    else:
        status = "pass"
        message = f"All nodes have valid ownership; {unknown_count} with 'unknown' (acceptable)"
    return {
        "section": "repository",
        "check_id": "repo-ownership-completeness",
        "name": "Ownership completeness",
        "status": status,
        "severity": "high" if status == "fail" else "info",
        "priority": "high" if status == "fail" else "low",
        "message": message,
        "details": {
            "total_nodes": len(nodes),
            "unknown_ownership_count": unknown_count,
            "invalid_ownership_nodes": invalid_ownership[:50],
        },
        "recommendation": "" if status == "pass" else "Fix invalid ownership values",
    }


def _verify_graph_build_reproducibility(
    repo_root: Path | None = None,
) -> dict[str, Any]:
    repo = repo_root or REPO_ROOT
    try:
        from runtime.foundation.repository.builder.builder import RepositoryBuilder

        builder = RepositoryBuilder(repo_root=repo)
        builder.build()
        summary = builder.validate()
        errors = summary.errors
        warnings = summary.warnings

        if errors:
            status = "fail"
            message = f"Fresh graph build produced {len(errors)} errors"
        else:
            status = "pass"
            message = f"Fresh graph build succeeded with {summary.node_count} nodes, {summary.edge_count} edges"
        details = {
            "built_node_count": summary.node_count,
            "built_edge_count": summary.edge_count,
            "validation_errors": errors[:50],
            "validation_warnings": warnings[:50],
            "gaps": builder.gaps,
        }
    except Exception as exc:
        status = "fail"
        message = f"Graph build failed: {exc}"
        details = {"error": str(exc)}
        errors = [str(exc)]
    return {
        "section": "repository",
        "check_id": "repo-build-reproducibility",
        "name": "Graph build reproducibility",
        "status": status,
        "severity": "critical" if status == "fail" else "info",
        "priority": "critical" if status == "fail" else "low",
        "message": message,
        "details": details,
        "recommendation": (
            "" if status == "pass" else "Fix errors preventing fresh graph build"
        ),
    }


def _verify_node_type_coverage(data: dict[str, Any]) -> dict[str, Any]:
    from runtime.foundation.repository.graph.schema import NODE_TYPES

    graph = data.get("graph", {})
    nodes = graph.get("nodes", [])
    expected_types = set(NODE_TYPES)
    actual_types = {n.get("type", "") for n in nodes}
    unknown_types = actual_types - expected_types
    if unknown_types:
        status = "fail"
        message = (
            f"Found {len(unknown_types)} unknown node types: {sorted(unknown_types)}"
        )
    else:
        status = "pass"
        message = f"All node types are valid ({len(actual_types)} types found)"
    return {
        "section": "repository",
        "check_id": "repo-node-type-coverage",
        "name": "Node type coverage",
        "status": status,
        "severity": "high" if status == "fail" else "info",
        "priority": "high" if status == "fail" else "low",
        "message": message,
        "details": {
            "found_types": sorted(actual_types),
            "unknown_types": sorted(unknown_types),
        },
        "recommendation": (
            ""
            if status == "pass"
            else "Remove unknown node types or add them to NODE_TYPES schema"
        ),
    }


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    findings: list[dict[str, Any]] = []
    repo = repo_root or REPO_ROOT
    index_path = _find_index_path(repo)

    findings.append(_verify_index_existence(index_path))

    data = _load_index(index_path)

    if data:
        findings.append(_verify_json_validity(index_path))
        findings.append(_verify_metadata_completeness(data))
        findings.append(_verify_node_count_consistency(data))
        findings.append(_verify_unique_node_ids(data))
        findings.append(_verify_edge_referential_integrity(data))
        findings.append(_verify_edge_deduplication(data))
        findings.append(_verify_ownership_comprehensiveness(data))
        findings.append(_verify_node_type_coverage(data))
    else:
        findings.append(
            {
                "section": "repository",
                "check_id": "repo-index-load",
                "name": "Index load",
                "status": "fail",
                "severity": "critical",
                "priority": "critical",
                "message": "Could not load index.json for content checks",
                "details": {},
                "recommendation": "Generate index.json before running repository audit",
            }
        )

    findings.append(_verify_graph_build_reproducibility(repo))

    all_pass = all(f["status"] == "pass" for f in findings)
    overall_status = "pass" if all_pass else "fail"

    duration = time.monotonic() - start
    metrics = {
        "total_checks": len(findings),
        "failures": sum(1 for f in findings if f["status"] == "fail"),
        "passes": sum(1 for f in findings if f["status"] == "pass"),
        "index_path": str(index_path),
    }
    if data:
        meta = data.get("metadata", {})
        metrics["index_node_count"] = meta.get("node_count", 0)
        metrics["index_edge_count"] = meta.get("edge_count", 0)
        metrics["schema_version"] = meta.get("schema_version", "")

    return {
        "section": "repository",
        "name": "Repository Index Audit",
        "status": overall_status,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": duration,
    }
