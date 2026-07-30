"""Impact Analysis Engine — Phase 2.2.

Deterministic graph traversal only. No heuristics. No planning. No AI.

The ImpactAnalyzer computes the downstream effect of a repository file by
following all outgoing relationship edges from the starting node, up to a
configurable maximum depth, and aggregates results by affected entity type.
All decisions are explicit, documented in the 'why' field for each result.

This module now uses RepositoryGraphService as the unified interface for
graph access.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Dict, List, Set

from repo_intelligence.graph_service import RepositoryGraphService
from repo_intelligence.schema import GraphNode


class ImpactAnalyzer:
    """Deterministic impact analysis over the canonical repository index.

    Traversal is breadth-first up to a configurable depth (default 8). Each
    edge follows exactly one relationship type; results include explanatory
    documentation for why each entity was included.
    """

    def __init__(self, service: RepositoryGraphService, max_depth: int = 8):
        self._service = service
        self._max_depth = max_depth

    @staticmethod
    def _path_description(edge_rel: str, target_type: str) -> str:
        """Describe the traversed edge for the 'why' explanation."""
        desc_map = {
            "implements": f"capability implements {target_type}",
            "depends_on": f"module depends on {target_type}",
            "calls": f"module calls {target_type}",
            "imports": f"module imports {target_type}",
            "owns": f"capability owns {target_type}",
            "tests": f"capability tests {target_type}",
            "documents": f"capability documents {target_type}",
            "verifies": f"capability verifies {target_type}",
            "consumes": "frontend module consumes endpoint",
            "contains": f"capability contains {target_type}",
            "extends": f"{target_type} extends another component",
            "invokes": f"{target_type} invoked by caller",
        }
        return desc_map.get(edge_rel, "relationship " + edge_rel + " to " + target_type)

    def _find_node_by_path(self, path: str) -> GraphNode | None:
        """Find a node by matching its path property using the service."""
        def predicate(n: GraphNode) -> bool:
            return n.path == path
        matching = self._service.find_nodes(predicate)
        if matching:
            return matching[0]
        return None

    def analyze_file(self, path: str) -> Dict[str, Any]:
        """Analyze the impact of changes to a repository file.

        Args:
            path: Repository file path (e.g., "src/routers/reconciliation.py").

        Returns:
            Dictionary mapping entity types to lists of items with explanatory
            'why' strings describing the traversal chain.
        """
        start_node_obj = self._find_node_by_path(path)
        if start_node_obj is None:
            return self._empty_result()

        start_node_id = start_node_obj.id

        # BFS traversal tracking cumulative reasons
        visited: Set[str] = {start_node_id}
        queue: deque = deque([(start_node_id, "", 0)])  # (node_id, incoming_reason, depth)

        # Accumulate findings per entity type
        results: Dict[str, List[Dict[str, Any]]] = {
            "capabilities": [],
            "endpoints": [],
            "frontend_consumers": [],
            "workflows": [],
            "tests": [],
            "documentation": [],
            "generated_artifacts": [],
            "migrations": [],
        }

        while queue:
            node_id, incoming_reason, depth = queue.popleft()
            if depth > self._max_depth:
                continue

            current_node_obj = self._service.get_node(node_id)
            if current_node_obj is None:
                continue

            current_type = current_node_obj.type
            current_name = current_node_obj.name

            # Record the node if it matches a tracked entity type
            if current_type == "capability":
                reason = f"{incoming_reason} → {current_name}" if incoming_reason else current_name
                results["capabilities"].append({
                    "id": current_node_obj.id,
                    "name": current_name,
                    "why": reason,
                })
            elif current_type == "endpoint":
                reason = f"{incoming_reason} → {current_name}" if incoming_reason else current_name
                results["endpoints"].append({
                    "id": current_node_obj.id,
                    "name": current_name,
                    "why": reason,
                })
            elif current_type in ("component", "hook"):
                reason = f"{incoming_reason} → {current_name}" if incoming_reason else current_name
                results["frontend_consumers"].append({
                    "id": current_node_obj.id,
                    "name": current_name,
                    "why": reason,
                })
            elif current_type == "workflow":
                results["workflows"].append({
                    "id": current_node_obj.id,
                    "name": current_name,
                    "why": f"{incoming_reason} → {current_name}" if incoming_reason else current_name,
                })
            elif current_type == "test_suite":
                results["tests"].append({
                    "id": current_node_obj.id,
                    "name": current_name,
                    "why": f"{incoming_reason} → {current_name}" if incoming_reason else current_name,
                })
            elif current_type == "documentation":
                results["documentation"].append({
                    "id": current_node_obj.id,
                    "name": current_name,
                    "why": f"{incoming_reason} → {current_name}" if incoming_reason else current_name,
                })
            elif current_type == "generated_artifact":
                results["generated_artifacts"].append({
                    "id": current_node_obj.id,
                    "name": current_name,
                    "why": f"{incoming_reason} → {current_name}" if incoming_reason else current_name,
                })
            elif current_type == "migration":
                results["migrations"].append({
                    "id": current_node_obj.id,
                    "name": current_name,
                    "why": f"{incoming_reason} → {current_name}" if incoming_reason else current_name,
                })

            # Enqueue outgoing neighbors with updated reasoning
            out_edges = self._service.find_edges(node_id)[0]  # outgoing edges only
            for edge in out_edges:
                target_id = edge.target
                rel = edge.relationship
                if target_id not in visited:
                    visited.add(target_id)
                    target_node_obj = self._service.get_node(target_id)
                    target_type = target_node_obj.type if target_node_obj else "unknown"
                    edge_desc = self._path_description(rel, target_type)
                    new_reason = f"{incoming_reason} {edge_desc} →" if incoming_reason else edge_desc
                    queue.append((target_id, new_reason, depth + 1))

        # Count verification targets for metadata
        all_outgoing = []
        for node in self._service.get_nodes():
            all_outgoing.extend(self._service.find_edges(node.id)[0])
        all_incoming = []
        for node in self._service.get_nodes():
            all_incoming.extend(self._service.find_edges(node.id)[1])
        verification_target_count = sum(1 for e in all_outgoing + all_incoming if e.relationship == "verifies")
        results["verification_targets"] = {
            "count": verification_target_count,
            "reason": "Total verification relationships in the graph",
        }

        return results

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty structure when no matching start node is found."""
        return {
            "capabilities": [],
            "endpoints": [],
            "frontend_consumers": [],
            "workflows": [],
            "tests": [],
            "documentation": [],
            "generated_artifacts": [],
            "migrations": [],
            "verification_targets": {"count": 0, "reason": "No matching start node found"},
        }


# Convenience wrapper
def compute_impact(path: str, max_depth: int = 8) -> Dict[str, Any]:
    """Quick impact analysis entry point.

    Loads the default index and runs impact analysis on the given path.
    """
    from pathlib import Path
    from repo_intelligence.graph_service import load_graph_service as load_service

    index_path = Path(__file__).parent / "index.json"
    service = load_service(index_path)
    analyzer = ImpactAnalyzer(service, max_depth=max_depth)
    return analyzer.analyze_file(path)
