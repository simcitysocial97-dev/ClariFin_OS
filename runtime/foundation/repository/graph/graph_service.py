"""Repository Graph Service — Phase 1.

The ONLY supported interface for graph access. All modules must use this service
instead of accessing graph.nodes or graph.edges directly.

This service provides:
- Unified node/edge lookup
- Traversal utilities (successors, predecessors, neighbors, paths)
- Query predicates and filtering
- Statistics and validation

All future modules consume RepositoryGraphService. No module should duplicate
traversal logic or inspect raw graph internals.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Set, Tuple

from runtime.foundation.repository.graph.schema import (
    GraphNode,
    GraphEdge,
    RepositoryGraph,
)


@dataclass
class GraphServiceCache:
    """Simple deterministic in-memory caches for RepositoryGraphService."""

    node_cache: Dict[str, GraphNode] = field(default_factory=dict)
    edge_cache: Dict[str, list[GraphEdge]] = field(
        default_factory=lambda: defaultdict(list)
    )
    successor_cache: Dict[Tuple[str, str | None], List[str]] = field(
        default_factory=dict
    )
    predecessor_cache: Dict[Tuple[str, str | None], List[str]] = field(
        default_factory=dict
    )
    neighbor_cache: Dict[str, Set[str]] = field(
        default_factory=dict
    )  # Empty dict, populated lazily
    gaps: Dict[str, Any] = field(default_factory=dict)  # Store gap metadata

    def clear(self) -> None:
        self.node_cache.clear()
        self.edge_cache.clear()
        self.successor_cache.clear()
        self.predecessor_cache.clear()
        self.neighbor_cache.clear()
        self.gaps.clear()


class RepositoryGraphService:
    """Unified read-only service over the canonical repository graph.

    This is the SINGLE entry point for all graph traversal and querying.
    It decouples consumers from the internal RepositoryGraph structure,
    enabling lazy loading, caching, and schema evolution.
    """

    def __init__(
        self, graph: RepositoryGraph | None = None, index_path: Path | None = None
    ):
        """Construct from an existing RepositoryGraph or load from index path.

        Args:
            graph: Pre-built RepositoryGraph (optional).
            index_path: Path to index.json to lazily load (optional).

        Exactly one of graph or index_path must be provided. If index_path is given,
        the graph is loaded lazily on first access.
        """
        if graph is not None and index_path is not None:
            raise ValueError("Provide exactly one: graph OR index_path, not both")
        if graph is None and index_path is None:
            raise ValueError("Must provide either graph or index_path")

        # Ensure index_path is a Path object (accept string too)
        if index_path is not None and not isinstance(index_path, Path):
            index_path = Path(index_path)

        self._graph: RepositoryGraph | None = graph
        self._index_path: Path | None = index_path
        self._loaded = False
        self._cache: GraphServiceCache = GraphServiceCache()

        # Lazily load when first method is called
        self._ensure_loaded()

    def _ensure_loaded(self) -> None:
        """Load the index from disk if constructed with index_path.

        If a RepositoryGraph was provided directly during construction,
        build the caches from that graph.
        """
        if self._loaded and self._graph is not None:
            # Already loaded from index path; graph is already populated
            return
        if self._graph is not None:
            # A pre-built RepositoryGraph was provided; build caches now
            self._rebuild_caches()
            self._loaded = True
            return

        # Otherwise, load from index path
        if self._index_path is None:
            raise RuntimeError("No graph loaded and no index path set")

        ipath = self._index_path  # Ensure it's a Path (should be already)
        if ipath.exists():
            self._load_from_index()
            self._loaded = True
            self._rebuild_caches()
        else:
            raise FileNotFoundError(f"Index file not found: {ipath}")

    def _load_from_index(self) -> None:
        """Deserialize index.json into a RepositoryGraph."""
        if self._index_path is None:
            raise RuntimeError("No index path set for loading")
        data = json.loads(self._index_path.read_text(encoding="utf-8"))

        # Support legacy flat format (without metadata/graph wrapper)
        if "nodes" in data and "edges" in data and "metadata" not in data:
            # Legacy format — treat as v2.1; no gaps section
            self._graph = RepositoryGraph()
            self._graph.schema_version = data.get("schema_version", "2.1")
            self._graph.generated_at = data.get("generated_at", "")
            self._graph.repository_root = data.get("repository_root", "")

            # Reconstruct GraphNode objects
            for nd in data.get("nodes", []):
                node = GraphNode(
                    id=nd["id"],
                    type=nd["type"],
                    name=nd["name"],
                    path=nd["path"],
                    source=nd["source"],
                    ownership=nd.get("ownership", "unknown"),
                    properties=nd.get("properties", {}),
                )
                self._graph.add_node(node)

            # Reconstruct GraphEdge objects (de-duplicate by source/target/relationship)
            seen_edges1: set[tuple[str, str, str]] = set()
            for ed in data.get("edges", []):
                key = (ed["source"], ed["target"], ed["relationship"])
                if key not in seen_edges1:
                    seen_edges1.add(key)
                    edge = GraphEdge(
                        source=ed["source"],
                        target=ed["target"],
                        relationship=ed["relationship"],
                        confidence=ed.get("confidence", 1.0),
                        evidence=ed.get("evidence", ""),
                        ownership=ed.get("ownership", "unknown"),
                    )
                    self._graph.add_edge(edge)
        else:
            # New format with metadata/graph wrapper
            meta = data.get("metadata", {})
            graph_data = data.get("graph", {})
            gaps_raw = data.get("gaps", {})  # Extract gaps from top-level

            self._graph = RepositoryGraph()
            self._graph.schema_version = meta.get("schema_version", "2.2")
            self._graph.generated_at = meta.get("generated_at", "")
            self._graph.repository_root = meta.get("repository_root", "")

            for nd in graph_data.get("nodes", []):
                node = GraphNode(
                    id=nd["id"],
                    type=nd["type"],
                    name=nd["name"],
                    path=nd["path"],
                    source=nd["source"],
                    ownership=nd.get("ownership", "unknown"),
                    properties=nd.get("properties", {}),
                )
                self._graph.add_node(node)

            # Reconstruct GraphEdge objects (de-duplicate)
            seen_edges2: set[tuple[str, str, str]] = set()
            for ed in graph_data.get("edges", []):
                key = (ed["source"], ed["target"], ed["relationship"])
                if key not in seen_edges2:
                    seen_edges2.add(key)
                    edge = GraphEdge(
                        source=ed["source"],
                        target=ed["target"],
                        relationship=ed["relationship"],
                        confidence=ed.get("confidence", 1.0),
                        evidence=ed.get("evidence", ""),
                        ownership=ed.get("ownership", "unknown"),
                    )
                    self._graph.add_edge(edge)

            # Store gaps in cache for gap queries
            if self._cache is not None:
                self._cache.gaps = gaps_raw

        self._rebuild_caches()

    def _rebuild_caches(self) -> None:
        """Rebuild all deterministic caches from the loaded graph."""
        if self._graph is None:
            return

        self._cache.node_cache.clear()
        self._cache.edge_cache.clear()
        self._cache.successor_cache.clear()
        self._cache.predecessor_cache.clear()
        self._cache.neighbor_cache.clear()

        for node in self._graph.nodes:
            self._cache.node_cache[node.id] = node

        for edge in self._graph.edges:
            self._cache.edge_cache[edge.source].append(edge)
            # Pre-populate neighbor sets for O(1) lookups
            if hasattr(self._cache.neighbor_cache, "update"):
                pass  # placeholder

        for edge in self._graph.edges:
            # Successors: edges where source is node_id
            succ_key = (edge.source, None)
            if succ_key not in self._cache.successor_cache:
                self._cache.successor_cache[succ_key] = []
            self._cache.successor_cache[succ_key].append(edge.target)

            # Predecessors: edges where target is node_id
            pred_key = (edge.target, None)
            if pred_key not in self._cache.predecessor_cache:
                self._cache.predecessor_cache[pred_key] = []
            self._cache.predecessor_cache[pred_key].append(edge.source)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def get_node(self, node_id: str) -> GraphNode | None:
        """Retrieve a node by ID.

        Returns the node if found, otherwise None.
        """
        self._ensure_loaded()
        return self._cache.node_cache.get(node_id)

    def get_nodes(self, node_type: str | None = None) -> list[GraphNode]:
        """Retrieve all nodes, optionally filtered by node_type.

        Args:
            node_type: If provided, only nodes of this type are returned.

        Returns:
            List of matching GraphNode objects (empty list if none match).
        """
        self._ensure_loaded()
        if node_type is None:
            return list(self._cache.node_cache.values())
        return [n for n in self._cache.node_cache.values() if n.type == node_type]

    def find_nodes(self, predicate: Callable[[GraphNode], bool]) -> list[GraphNode]:
        """Find all nodes matching a predicate function.

        Args:
            predicate: A function that takes a GraphNode and returns True if it matches.

        Returns:
            List of all nodes for which predicate returns True.
        """
        self._ensure_loaded()
        return [n for n in self._cache.node_cache.values() if predicate(n)]

    def get_edge(self, edge_id: str) -> GraphEdge | None:
        """Retrieve an edge by its composite ID (source:target:relationship).

        Note: Edges don't have unique single IDs; the edge_id is treated as a
        source:target:relationship triplet. Returns None if not found.
        """
        self._ensure_loaded()
        parts = edge_id.split(":", 2)
        if len(parts) != 3:
            return None
        source, target, rel = parts
        # type ignore: _graph is guaranteed non-None by _ensure_loaded() when using index_path
        for edge in self._graph.edges:  # type: ignore
            if (
                edge.source == source
                and edge.target == target
                and edge.relationship == rel
            ):
                return edge
        return None

    def successors(self, node_id: str, edge_type: str | None = None) -> list[str]:
        """Get the successor node IDs (all nodes reachable via outgoing edges).

        Args:
            node_id: The source node ID.
            edge_type: If provided, only edges of this relationship type are followed.

        Returns:
            List of unique successor node IDs (sorted for determinism).
        """
        self._ensure_loaded()

        cache_key = (node_id, edge_type)
        if cache_key in self._cache.successor_cache:
            return sorted(self._cache.successor_cache[cache_key])

        result: set[str] = set()
        if node_id in self._cache.edge_cache:
            for edge in self._cache.edge_cache[node_id]:
                if edge_type is None or edge.relationship == edge_type:
                    result.add(edge.target)

        sorted_result = sorted(result)
        self._cache.successor_cache[cache_key] = sorted_result
        return sorted_result

    def predecessors(self, node_id: str, edge_type: str | None = None) -> list[str]:
        """Get the predecessor node IDs (all nodes with incoming edges to this node).

        Args:
            node_id: The target node ID.
            edge_type: If provided, only edges of this relationship type are followed.

        Returns:
            List of unique predecessor node IDs (sorted for determinism).
        """
        self._ensure_loaded()

        cache_key = (node_id, edge_type)
        if cache_key in self._cache.predecessor_cache:
            return sorted(self._cache.predecessor_cache[cache_key])

        result: set[str] = set()
        for edge in self._graph.edges:
            if edge.target == node_id and (
                edge_type is None or edge.relationship == edge_type
            ):
                result.add(edge.source)

        sorted_result = sorted(result)
        self._cache.predecessor_cache[cache_key] = sorted_result
        return sorted_result

    def neighbors(self, node_id: str) -> list[str]:
        """Get all neighboring node IDs (both successors and predecessors).

        Args:
            node_id: The node ID.

        Returns:
            List of unique neighbor node IDs (sorted for determinism).
        """
        self._ensure_loaded()
        succ = self.successors(node_id)
        pred = self.predecessors(node_id)
        # Combine and deduplicate while preserving sorted order
        combined = sorted(set(succ + list(pred)))
        return combined

    def find_paths(
        self,
        source: str,
        target: str,
        max_depth: int = 8,
    ) -> List[List[str]]:
        """Find all simple paths from source to target up to max_depth.

        Uses BFS to enumerate all simple paths (no repeated nodes) from the
        source node to the target node, bounded by max_depth hops.

        Args:
            source: Starting node ID.
            target: Destination node ID.
            max_depth: Maximum number of edges in any path (default 8).

        Returns:
            List of paths, where each path is a list of node IDs from source
            to target inclusive. Paths are sorted lexicographically for
            determinism.
        """
        self._ensure_loaded()

        if source not in self._cache.node_cache or target not in self._cache.node_cache:
            return []

        results: List[List[str]] = []
        # Stack contains (current_id, path_as_list_of_ids)
        stack: List[Tuple[str, List[str]]] = [(source, [source])]

        while stack:
            current, path = stack.pop()

            if current == target and len(path) > 1:
                results.append(path)
                continue

            if len(path) - 1 >= max_depth:
                continue

            # Get all successors (undirected — follow both incoming and outgoing)
            all_succ = set()
            for edge in self._graph.edges:
                if edge.source == current:
                    all_succ.add(edge.target)
                if edge.target == current:
                    all_succ.add(edge.source)

            for nxt in sorted(all_succ):  # sorted for deterministic ordering
                if nxt not in path:  # Avoid cycles
                    stack.append((nxt, path + [nxt]))

        # Sort results lexicographically for determinism
        results.sort()
        return results

    def find_edges(self, node_id: str) -> tuple[list[GraphEdge], list[GraphEdge]]:
        """Find all edges connected to a node (outgoing and incoming separately).

        Args:
            node_id: The node ID.

        Returns:
            A tuple (outgoing_edges, incoming_edges) where each is a list of
            GraphEdge objects. Outgoing edges are those where node_id is the
            source; incoming edges are those where node_id is the target. Both
            lists are sorted by relationship then target/source for determinism.
        """
        self._ensure_loaded()

        outgoing = [e for e in self._graph.edges if e.source == node_id]
        incoming = [e for e in self._graph.edges if e.target == node_id]

        # Sort for determinism: by relationship, then by counterpart
        outgoing.sort(key=lambda e: (e.relationship, e.target))
        incoming.sort(key=lambda e: (e.relationship, e.source))

        return outgoing, incoming

    def get_gaps(self) -> Dict[str, Any]:
        """Return gap detection metadata from the index (if available).

        Returns:
            A dictionary with keys like "missing_modules", "orphan_modules",
            "no_verification_evidence", "no_documentation_evidence", etc.
            Empty dict if no gaps data is available.
        """
        self._ensure_loaded()
        if self._cache is None:
            return {}
        return self._cache.gaps.copy()

    def statistics(self) -> dict[str, Any]:
        """Compute basic statistics about the graph.

        Returns:
            Dictionary containing counts of nodes, edges, node types,
            relationship types, and distribution of ownership classes.
        """
        self._ensure_loaded()

        if self._graph is None:
            return {}

        node_counts: dict[str, int] = {}
        edge_counts: dict[str, int] = {}
        ownership_counts: dict[str, int] = {}

        for n in self._graph.nodes:
            node_counts[n.type] = node_counts.get(n.type, 0) + 1
            ownership_counts[n.ownership] = ownership_counts.get(n.ownership, 0) + 1

        for e in self._graph.edges:
            edge_counts[e.relationship] = edge_counts.get(e.relationship, 0) + 1

        return {
            "total_nodes": len(self._graph.nodes),
            "total_edges": len(self._graph.edges),
            "node_types": dict(sorted(node_counts.items())),
            "edge_relationships": dict(sorted(edge_counts.items())),
            "ownership_distribution": dict(sorted(ownership_counts.items())),
            "unique_node_ids": len(self._cache.node_cache),
            "unique_edge_pairs": len(
                {(e.source, e.target, e.relationship) for e in self._graph.edges}
            ),
        }

    def validate(self) -> dict[str, Any]:
        """Validate structural integrity of the graph.

        Checks that:
          - All referenced nodes exist (edges don't reference missing nodes)
          - No duplicate edges (same source/target/relationship)
          - All node IDs are unique
          - All required fields are present on nodes/edges

        Returns:
            A dictionary with "valid" (bool), "errors" (list of strings), and
            "warnings" (list of strings).
        """
        self._ensure_loaded()

        errors: list[str] = []
        warnings: list[str] = []

        if self._graph is None:
            errors.append("No graph loaded")
            return {"valid": False, "errors": errors, "warnings": warnings}

        # Check all node IDs are unique
        node_ids: set[str] = set()
        for n in self._graph.nodes:
            if n.id in node_ids:
                errors.append(f"Duplicate node ID: {n.id}")
            node_ids.add(n.id)

        # Check edges reference existing nodes
        for e in self._graph.edges:
            if e.source not in node_ids:
                errors.append(f"Edge references missing source node: {e.source}")
            if e.target not in node_ids:
                errors.append(f"Edge references missing target node: {e.target}")

        # Check for duplicate edges (same source/target/relationship)
        seen_edges: set[tuple[str, str, str]] = set()
        for e in self._graph.edges:
            key = (e.source, e.target, e.relationship)
            if key in seen_edges:
                warnings.append(f"Duplicate edge: {key}")
            seen_edges.add(key)

        # Check all nodes have required fields
        for n in self._graph.nodes:
            for attr in ("id", "type", "name", "path", "source"):
                if getattr(n, attr) is None or getattr(n, attr) == "":
                    warnings.append(f"Node {n.id} missing field '{attr}'")

        # Check edges have required fields
        for e in self._graph.edges:
            for attr in ("source", "target", "relationship"):
                if getattr(e, attr) is None or getattr(e, attr) == "":
                    warnings.append(
                        f"Edge missing field '{attr}' from {e.source}->{e.target}"
                    )

        valid = len(errors) == 0
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "node_count": len(self._graph.nodes),
            "edge_count": len(self._graph.edges),
        }


# Convenience function to build a service from a RepositoryGraph object
def build_graph_service(graph: RepositoryGraph) -> RepositoryGraphService:
    """Create a RepositoryGraphService from an existing RepositoryGraph.

    Args:
        graph: The pre-built RepositoryGraph to wrap.

    Returns:
        A RepositoryGraphService instance.
    """
    return RepositoryGraphService(graph=graph)


# Convenience function to create a service from an index path
def load_graph_service(index_path: Path | str) -> RepositoryGraphService:
    """Create a RepositoryGraphService that lazily loads from index.json.

    Args:
        index_path: Path or string to the index.json file.

    Returns:
        A RepositoryGraphService instance.
    """
    return RepositoryGraphService(index_path=index_path)
