"""Dependency Graph Audit — Program 12.

Verifies the repository dependency graph for:
- Structural integrity (valid JSON, no duplicate/orphan nodes)
- Edge completeness (all edges reference existing nodes)
- Cycle detection (no circular dependencies)
- Ownership distribution (no invalid ownership values)
- Node type and relationship type validity
- Graph depth analysis
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


def _verify_graph_service_load(index_path: Path) -> dict[str, Any]:
    try:
        from runtime.foundation.repository.graph.graph_service import (
            RepositoryGraphService,
        )

        svc = RepositoryGraphService(index_path=index_path)
        stats = svc.statistics()
        status = "pass"
        message = f"Graph service loaded: {stats['total_nodes']} nodes, {stats['total_edges']} edges"
    except Exception as exc:
        status = "fail"
        message = f"Graph service failed to load: {exc}"
        stats = None
    return {
        "section": "dependency_graph",
        "check_id": "dg-service-load",
        "name": "RepositoryGraphService loads index",
        "status": status,
        "severity": "critical" if status == "fail" else "info",
        "priority": "critical" if status == "fail" else "low",
        "message": message,
        "details": (
            {"statistics": stats} if stats else {"error": "Graph validation failed"}
        ),
        "recommendation": (
            ""
            if status == "pass"
            else "Fix index.json to be loadable by RepositoryGraphService"
        ),
    }


def _verify_structural_integrity(svc) -> dict[str, Any]:
    validation = svc.validate()
    errors = validation.get("errors", [])
    warnings = validation.get("warnings", [])
    if not errors:
        status = "pass"
        message = f"Graph has no structural errors ({len(warnings)} warnings)"
    else:
        status = "fail"
        message = f"Graph has {len(errors)} structural errors"
    return {
        "section": "dependency_graph",
        "check_id": "dg-structural-integrity",
        "name": "Structural integrity",
        "status": status,
        "severity": "critical" if status == "fail" else "info",
        "priority": "critical" if status == "fail" else "low",
        "message": message,
        "details": {
            "errors": errors[:50],
            "warnings": warnings[:50],
            "node_count": validation.get("node_count", 0),
            "edge_count": validation.get("edge_count", 0),
        },
        "recommendation": (
            ""
            if status == "pass"
            else "Fix structural errors (duplicate nodes, missing edge targets)"
        ),
    }


def _verify_no_duplicate_nodes(data: dict[str, Any]) -> dict[str, Any]:
    graph = data.get("graph", {})
    nodes = graph.get("nodes", [])
    seen: set[str] = set()
    duplicates: list[str] = []
    for n in nodes:
        nid = n.get("id", "")
        if nid in seen and nid not in duplicates:
            duplicates.append(nid)
        seen.add(nid)
    if not duplicates:
        status = "pass"
        message = f"No duplicate node IDs ({len(nodes)} nodes)"
    else:
        status = "fail"
        message = f"Found {len(duplicates)} duplicate node IDs"
    return {
        "section": "dependency_graph",
        "check_id": "dg-no-duplicate-nodes",
        "name": "No duplicate nodes",
        "status": status,
        "severity": "critical" if status == "fail" else "info",
        "priority": "critical" if status == "fail" else "low",
        "message": message,
        "details": {"duplicate_ids": duplicates[:50], "total_nodes": len(nodes)},
        "recommendation": "" if status == "pass" else "Remove duplicate node entries",
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
        if src not in node_ids and src not in missing_sources:
            missing_sources.append(src)
        if tgt not in node_ids and tgt not in missing_targets:
            missing_targets.append(tgt)
    if not missing_sources and not missing_targets:
        status = "pass"
        message = f"All {len(edges)} edges reference existing nodes"
    else:
        status = "fail"
        message = f"Found {len(missing_sources)} missing sources, {len(missing_targets)} missing targets"
    return {
        "section": "dependency_graph",
        "check_id": "dg-edge-referential-integrity",
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
            "" if status == "pass" else "Fix edges referencing non-existent nodes"
        ),
    }


def _verify_no_duplicate_edges(data: dict[str, Any]) -> dict[str, Any]:
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
        message = f"No duplicate edges ({len(edges)} edges)"
    else:
        status = "fail"
        message = f"Found {len(duplicates)} duplicate edges"
    return {
        "section": "dependency_graph",
        "check_id": "dg-no-duplicate-edges",
        "name": "No duplicate edges",
        "status": status,
        "severity": "high" if status == "fail" else "info",
        "priority": "high" if status == "fail" else "low",
        "message": message,
        "details": {"duplicate_edges": duplicates[:50], "total_edges": len(edges)},
        "recommendation": "" if status == "pass" else "Remove duplicate edges",
    }


def _verify_node_type_validity(data: dict[str, Any]) -> dict[str, Any]:
    from runtime.foundation.repository.graph.schema import NODE_TYPES

    graph = data.get("graph", {})
    nodes = graph.get("nodes", [])
    invalid: list[str] = []
    actual_types = set()
    for n in nodes:
        nt = n.get("type", "")
        actual_types.add(nt)
        if nt not in NODE_TYPES:
            invalid.append(f"{n.get('id', '')}={nt}")
    if not invalid:
        status = "pass"
        message = f"All node types are valid ({len(actual_types)} types)"
    else:
        status = "fail"
        message = f"Found {len(invalid)} nodes with invalid types"
    return {
        "section": "dependency_graph",
        "check_id": "dg-node-type-validity",
        "name": "Node type validity",
        "status": status,
        "severity": "high" if status == "fail" else "info",
        "priority": "high" if status == "fail" else "low",
        "message": message,
        "details": {
            "invalid_type_nodes": invalid[:50],
            "valid_types": sorted(NODE_TYPES),
        },
        "recommendation": (
            "" if status == "pass" else "Fix or remove nodes with invalid types"
        ),
    }


def _verify_relationship_type_validity(data: dict[str, Any]) -> dict[str, Any]:
    from runtime.foundation.repository.graph.schema import RELATIONSHIP_TYPES

    graph = data.get("graph", {})
    edges = graph.get("edges", [])
    invalid: list[str] = []
    for e in edges:
        rel = e.get("relationship", "")
        if rel not in RELATIONSHIP_TYPES:
            invalid.append(f"{e.get('source', '')}->{e.get('target', '')}={rel}")
    if not invalid:
        status = "pass"
        message = "All edge relationships are valid"
    else:
        status = "fail"
        message = f"Found {len(invalid)} edges with invalid relationships"
    return {
        "section": "dependency_graph",
        "check_id": "dg-relationship-type-validity",
        "name": "Relationship type validity",
        "status": status,
        "severity": "high" if status == "fail" else "info",
        "priority": "high" if status == "fail" else "low",
        "message": message,
        "details": {
            "invalid_relationships": invalid[:50],
            "valid_types": sorted(RELATIONSHIP_TYPES),
        },
        "recommendation": (
            ""
            if status == "pass"
            else "Fix or remove edges with invalid relationship types"
        ),
    }


def _verify_ownership_validity(data: dict[str, Any]) -> dict[str, Any]:
    from runtime.foundation.repository.graph.schema import OWNERSHIP_CLASSES

    graph = data.get("graph", {})
    nodes = graph.get("nodes", [])
    invalid: list[str] = []
    for n in nodes:
        own = n.get("ownership", "unknown")
        if own not in OWNERSHIP_CLASSES:
            invalid.append(f"{n.get('id', '')}={own}")
    if not invalid:
        status = "pass"
        message = "All ownership values are valid"
    else:
        status = "fail"
        message = f"Found {len(invalid)} nodes with invalid ownership"
    return {
        "section": "dependency_graph",
        "check_id": "dg-ownership-validity",
        "name": "Ownership validity",
        "status": status,
        "severity": "high" if status == "fail" else "info",
        "priority": "high" if status == "fail" else "low",
        "message": message,
        "details": {
            "invalid_ownership_nodes": invalid[:50],
            "valid_classes": sorted(OWNERSHIP_CLASSES),
        },
        "recommendation": (
            ""
            if status == "pass"
            else "Fix or remove nodes with invalid ownership values"
        ),
    }


def _verify_no_cycles(svc) -> dict[str, Any]:
    try:
        graph = {}
        for n in svc.get_nodes():
            graph[n.id] = list(svc.successors(n.id))

        WHITE, GRAY, BLACK = 0, 1, 2
        color = {nid: WHITE for nid in graph}
        cycles_found = []

        def dfs(node, path):
            color[node] = GRAY
            path.append(node)
            for neighbor in graph.get(node, []):
                if neighbor not in color:
                    color[neighbor] = WHITE
                if color[neighbor] == GRAY:
                    cycle_start = path.index(neighbor) if neighbor in path else 0
                    cycles_found.append(path[cycle_start:] + [neighbor])
                elif color[neighbor] == WHITE:
                    dfs(neighbor, path)
            path.pop()
            color[node] = BLACK

        for nid in sorted(graph):
            if color[nid] == WHITE:
                dfs(nid, [])

        if not cycles_found:
            status = "pass"
            message = "No circular dependencies detected"
        else:
            status = "fail"
            message = f"Found {len(cycles_found)} circular dependencies"
    except RecursionError:
        status = "fail"
        message = "Cycle detection hit recursion limit (deep graph)"
        cycles_found = [["recursion_limit_exceeded"]]

    return {
        "section": "dependency_graph",
        "check_id": "dg-no-cycles",
        "name": "No circular dependencies",
        "status": status,
        "severity": "critical" if status == "fail" else "info",
        "priority": "critical" if status == "fail" else "low",
        "message": message,
        "details": {
            "cycles_found": cycles_found[:10],
            "cycle_count": (
                len(cycles_found) if isinstance(cycles_found, list) else "unknown"
            ),
        },
        "recommendation": (
            ""
            if status == "pass"
            else "Break circular dependencies in the repository graph"
        ),
    }


def _verify_graph_depth(svc) -> dict[str, Any]:
    try:
        graph = {}
        for n in svc.get_nodes():
            graph[n.id] = list(svc.successors(n.id))

        memo: dict[str, int] = {}

        def depth(node):
            if node in memo:
                return memo[node]
            if node not in graph or not graph[node]:
                memo[node] = 0
                return 0
            max_child_depth = 0
            for child in graph[node]:
                if child in graph:
                    d = depth(child)
                    if d > max_child_depth:
                        max_child_depth = d
            memo[node] = max_child_depth + 1
            return memo[node]

        max_depth = 0
        for nid in graph:
            d = depth(nid)
            if d > max_depth:
                max_depth = d

        status = "pass"
        message = f"Maximum graph depth: {max_depth}"
    except RecursionError:
        max_depth = -1
        status = "fail"
        message = "Graph depth too deep (recursion limit exceeded)"

    return {
        "section": "dependency_graph",
        "check_id": "dg-graph-depth",
        "name": "Graph depth analysis",
        "status": status,
        "severity": "info",
        "priority": "low",
        "message": message,
        "details": {"max_depth": max_depth, "node_count": len(graph)},
        "recommendation": "",
    }


def _verify_isolated_nodes(data: dict[str, Any]) -> dict[str, Any]:
    graph = data.get("graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    connected_ids: set[str] = set()
    for e in edges:
        connected_ids.add(e.get("source", ""))
        connected_ids.add(e.get("target", ""))
    isolated: list[str] = []
    for n in nodes:
        nid = n.get("id", "")
        if nid not in connected_ids:
            isolated.append(nid)
    if len(isolated) <= 5:
        status = "pass"
        message = (
            f"Graph is well-connected ({len(isolated)} isolated nodes, acceptable)"
        )
    else:
        pct = (len(nodes) - len(isolated)) / len(nodes) * 100 if nodes else 0
        if pct < 80:
            status = "fail"
            message = f"Too many isolated nodes: {len(isolated)} of {len(nodes)} ({pct:.0f}% connected)"
        else:
            status = "pass"
            message = (
                f"Acceptable number of isolated nodes: {len(isolated)} of {len(nodes)}"
            )
    return {
        "section": "dependency_graph",
        "check_id": "dg-isolated-nodes",
        "name": "Isolated node analysis",
        "status": status,
        "severity": "medium" if status == "fail" else "info",
        "priority": "medium" if status == "fail" else "low",
        "message": message,
        "details": {
            "isolated_count": len(isolated),
            "isolated_ids": isolated[:50],
            "total_nodes": len(nodes),
        },
        "recommendation": (
            ""
            if status == "pass"
            else "Investigate and connect isolated nodes or mark as intentionally standalone"
        ),
    }


def _verify_ownership_distribution(data: dict[str, Any]) -> dict[str, Any]:
    from runtime.foundation.repository.graph.schema import OWNERSHIP_CLASSES

    graph_data = data.get("graph", {})
    nodes = graph_data.get("nodes", [])
    ownership_dist: dict[str, int] = {}
    for n in nodes:
        own = n.get("ownership", "unknown")
        ownership_dist[own] = ownership_dist.get(own, 0) + 1

    invalid = sum(v for k, v in ownership_dist.items() if k not in OWNERSHIP_CLASSES)
    if invalid == 0:
        status = "pass"
        message = f"Valid ownership distribution across {len(ownership_dist)} classes"
    else:
        status = "fail"
        message = f"Found {invalid} nodes with invalid ownership classes"

    return {
        "section": "dependency_graph",
        "check_id": "dg-ownership-distribution",
        "name": "Ownership distribution",
        "status": status,
        "severity": "high" if status == "fail" else "info",
        "priority": "high" if status == "fail" else "low",
        "message": message,
        "details": {"distribution": ownership_dist},
        "recommendation": (
            "" if status == "pass" else "Reassign nodes with invalid ownership"
        ),
    }


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    findings: list[dict[str, Any]] = []
    repo = repo_root or REPO_ROOT
    index_path = _find_index_path(repo)

    findings.append(_verify_graph_service_load(index_path))

    data = _load_index(index_path)
    svc = None

    if data:
        from runtime.foundation.repository.graph.graph_service import (
            RepositoryGraphService,
        )

        try:
            svc = RepositoryGraphService(index_path=index_path)
        except Exception:
            pass

        findings.append(_verify_no_duplicate_nodes(data))
        findings.append(_verify_edge_referential_integrity(data))
        findings.append(_verify_no_duplicate_edges(data))
        findings.append(_verify_node_type_validity(data))
        findings.append(_verify_relationship_type_validity(data))
        findings.append(_verify_ownership_validity(data))
        findings.append(_verify_isolated_nodes(data))
        findings.append(_verify_ownership_distribution(data))

        if svc is not None:
            findings.append(_verify_structural_integrity(svc))
            findings.append(_verify_no_cycles(svc))
            findings.append(_verify_graph_depth(svc))
    else:
        findings.append(
            {
                "section": "dependency_graph",
                "check_id": "dg-index-load",
                "name": "Dependency graph index load",
                "status": "fail",
                "severity": "critical",
                "priority": "critical",
                "message": "Could not load index.json for dependency graph checks",
                "details": {},
                "recommendation": "Generate repository index before running dependency graph audit",
            }
        )

    all_pass = all(f["status"] == "pass" for f in findings)
    overall_status = "pass" if all_pass else "fail"

    duration = time.monotonic() - start
    metrics = {
        "total_checks": len(findings),
        "failures": sum(1 for f in findings if f["status"] == "fail"),
        "passes": sum(1 for f in findings if f["status"] == "pass"),
    }
    if data:
        meta = data.get("metadata", {})
        metrics["index_node_count"] = meta.get("node_count", 0)
        metrics["index_edge_count"] = meta.get("edge_count", 0)

    return {
        "section": "dependency_graph",
        "name": "Dependency Graph Audit",
        "status": overall_status,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": duration,
    }
