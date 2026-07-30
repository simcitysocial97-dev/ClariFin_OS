"""Repository Health Metrics — Phase 2.2.

Computes deterministic metrics about the repository index structure,
ownership coverage, verification/documentation evidence levels, and graph
statistics. Output is JSON-only (no markdown).

This module now uses RepositoryGraphService as the unified interface for
graph access.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Set

from repo_intelligence.graph_service import RepositoryGraphService


def calculate_metrics(service: RepositoryGraphService) -> Dict[str, Any]:
    """Compute comprehensive repository health metrics from the index service.

    Args:
        service: A RepositoryGraphService instance providing read-only access.

    Returns:
        A flat dictionary of metric names to numeric or string values.
    """
    nodes = service.get_nodes()

    # Get all edges directly from the underlying graph (unique edges only)
    if service._graph is None:
        raise RuntimeError("Graph not loaded")
    all_edges = service._graph.edges

    node_counts: Dict[str, int] = {}
    for n in nodes:
        t = n.type
        node_counts[t] = node_counts.get(t, 0) + 1

    edge_counts: Dict[str, int] = {}
    # Track seen edge keys to avoid duplicates
    seen_edges: Set[tuple[str, str, str]] = set()
    for e in all_edges:
        key = (e.source, e.target, e.relationship)
        if key not in seen_edges:
            seen_edges.add(key)
            r = e.relationship
            edge_counts[r] = edge_counts.get(r, 0) + 1

    total_nodes = len(nodes)
    total_edges = len(all_edges)

    # Ownership coverage
    ownership_unknown = sum(1 for n in nodes if n.ownership == "unknown")
    ownership_known = total_nodes - ownership_unknown
    ownership_coverage = (ownership_known / total_nodes * 100) if total_nodes > 0 else 0.0

    # Verification evidence coverage: endpoints verified by capabilities
    endpoint_count = node_counts.get("endpoint", 0)
    verified_endpoints: Set[str] = set()
    for e in all_edges:
        if e.relationship == "verifies" and e.source.startswith("capability:"):
            verified_endpoints.add(e.target)
    verification_coverage = (len(verified_endpoints) / endpoint_count * 100) if endpoint_count > 0 else 0.0

    # Documentation evidence coverage: capabilities with docs
    documented_cap_ids: Set[str] = set()
    for e in all_edges:
        if e.relationship == "documents":
            cap_id = e.source.split(":", 1)[-1] if ":" in e.source else e.source
            documented_cap_ids.add(f"capability:{cap_id}")
    cap_count = node_counts.get("capability", 0)
    documentation_coverage = (len(documented_cap_ids) / cap_count * 100) if cap_count > 0 else 0.0

    # Orphan module percentage
    implemented_modules: Set[str] = set()
    for e in all_edges:
        if e.relationship == "implements" and e.source.startswith("capability:"):
            implemented_modules.add(e.target)
    all_modules = [n for n in nodes if n.type == "module"]
    orphan_count = sum(1 for m in all_modules if m.id not in implemented_modules)
    orphan_percentage = (orphan_count / len(all_modules) * 100) if all_modules else 0.0

    # Graph density
    unique_nodes = {n.id for n in nodes}
    possible_edges = len(unique_nodes) * (len(unique_nodes) - 1) if len(unique_nodes) > 1 else 1
    graph_density = total_edges / possible_edges if possible_edges > 0 else 0.0

    # Largest capability by number of outgoing edges
    capability_nodes = [n for n in nodes if n.type == "capability"]
    largest_capability = None
    largest_cap_outgoing = 0
    for cap_node in capability_nodes:
        outgoing_count = len([e for e in all_edges if e.source == cap_node.id])
        if outgoing_count > largest_cap_outgoing:
            largest_cap_outgoing = outgoing_count
            largest_capability = cap_node.name if cap_node.name else cap_node.id

    # Top 10 highest fan-out nodes (most outgoing edges)
    node_out_degree: Dict[str, int] = {}
    for e in all_edges:
        src = e.source
        node_out_degree[src] = node_out_degree.get(src, 0) + 1
    sorted_out = sorted(node_out_degree.items(), key=lambda x: x[1], reverse=True)[:10]
    top_fanout = [{"node_id": nid, "degree": deg} for nid, deg in sorted_out]

    # Top 10 highest fan-in nodes (most incoming edges)
    node_in_degree: Dict[str, int] = {}
    for e in all_edges:
        tgt = e.target
        node_in_degree[tgt] = node_in_degree.get(tgt, 0) + 1
    sorted_in = sorted(node_in_degree.items(), key=lambda x: x[1], reverse=True)[:10]
    top_fanin = [{"node_id": nid, "degree": deg} for nid, deg in sorted_in]

    # Dead nodes (zero in-degree and zero out-degree)
    dead_nodes: List[str] = []
    for n in nodes:
        nid = n.id
        has_out = any(e.source == nid for e in all_edges)
        has_in = any(e.target == nid for e in all_edges)
        if not has_out and not has_in:
            dead_nodes.append(nid)

    # Longest dependency chain (depends_on edges only)
    depends_on_adj: Dict[str, List[str]] = {}
    for e in all_edges:
        if e.relationship == "depends_on":
            src = e.source
            tgt = e.target
            depends_on_adj.setdefault(src, []).append(tgt)

    def longest_path_from(start: str, adj: Dict[str, List[str]]) -> List[str]:
        best_path: List[str] = []

        def dfs(node: str, path: List[str]):
            nonlocal best_path
            path.append(node)
            if len(path) > len(best_path):
                best_path = list(path)
            for neighbor in adj.get(node, []):
                if neighbor not in path:
                    dfs(neighbor, path)
            path.pop()

        if start in adj or any(start in neighbors for neighbors in adj.values()):
            dfs(start, [])
        return best_path

    dep_sources = set(depends_on_adj.keys())
    longest_chain: List[str] = []
    for src in dep_sources:
        chain = longest_path_from(src, depends_on_adj)
        if len(chain) > len(longest_chain):
            longest_chain = chain

    top_dependency_chains = [{"chain": longest_chain, "length": len(longest_chain)}] if longest_chain else []

    generated_at = "unknown"
    schema_version = "2.2"

    return {
        "schema_version": schema_version,
        "generated_at": generated_at,
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "node_types": dict(sorted(node_counts.items())),
        "edge_relationships": dict(sorted(edge_counts.items())),
        "ownership_coverage_percent": round(ownership_coverage, 1),
        "verification_coverage_percent": round(verification_coverage, 1),
        "documentation_coverage_percent": round(documentation_coverage, 1),
        "orphan_module_percentage": round(orphan_percentage, 1),
        "graph_density": round(graph_density, 4),
        "largest_capability": largest_capability,
        "largest_capability_scope_edges": largest_cap_outgoing,
        "top_10_fan_out_nodes": top_fanout,
        "top_10_fan_in_nodes": top_fanin,
        "dead_nodes_count": len(dead_nodes),
        "dead_nodes": dead_nodes,
        "longest_dependency_chain": top_dependency_chains,
    }


if __name__ == "__main__":
    import sys
    from pathlib import Path

    index_path = Path(__file__).parent.parent / "repo_intelligence" / "index.json"
    if not index_path.exists():
        print(f"Index file not found: {index_path}", file=sys.stderr)
        sys.exit(1)

    service = RepositoryGraphService(index_path=index_path)
    metrics = calculate_metrics(service)
    print(json.dumps(metrics, indent=2))