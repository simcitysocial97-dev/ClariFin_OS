"""Regression tests for RepositoryGraphService — Phase 5.

These tests use small synthetic graphs to verify core functionality without
requiring actual repository scanning. They cover:
- Graph loading and node lookup
- Node type filtering
- Predicate-based search
- Edge lookup and traversal
- Path finding
- Statistics and validation
"""

import json
from pathlib import Path

import pytest

from repo_intelligence.schema import GraphNode, GraphEdge, RepositoryGraph
from repo_intelligence.graph_service import (
    build_graph_service,
    load_graph_service,
)


def make_node(node_type: str, name: str, path: str, id_str: str, ownership: str = "unknown") -> GraphNode:
    """Create a test GraphNode."""
    return GraphNode(
        id=f"{node_type}:{id_str}",
        type=node_type,
        name=name,
        path=path,
        source=f"test:{id_str}",
        ownership=ownership,
        properties={"id": id_str},
    )


def make_edge(source_type: str, source_id: str, target_type: str, target_id: str, relationship: str) -> GraphEdge:
    """Create a test GraphEdge."""
    return GraphEdge(
        source=f"{source_type}:{source_id}",
        target=f"{target_type}:{target_id}",
        relationship=relationship,
        confidence=1.0,
        evidence="test edge",
    )


class TestRepositoryGraphService:
    """Test RepositoryGraphService with synthetic graph data."""

    def test_get_node(self) -> None:
        """Test basic node lookup."""
        cap = make_node("capability", "test_cap", "/cap/test", "cap1")
        mod = make_node("module", "test_mod", "/mod/test", "mod1")
        edge = make_edge("capability", "cap1", "module", "mod1", "implements")

        graph = RepositoryGraph()
        graph.add_node(cap)
        graph.add_node(mod)
        graph.add_edge(edge)

        service = build_graph_service(graph)

        # Test get_node found
        node = service.get_node("capability:cap1")
        assert node is not None
        assert node.type == "capability"
        assert node.name == "test_cap"

        # Test get_node not found
        missing = service.get_node("capability:missing")
        assert missing is None

    def test_get_nodes_without_filter(self) -> None:
        """Test retrieving all nodes."""
        cap = make_node("capability", "c1", "/c/c1", "c1")
        mod = make_node("module", "m1", "/m/m1", "m1")

        graph = RepositoryGraph()
        graph.add_node(cap)
        graph.add_node(mod)

        service = build_graph_service(graph)
        all_nodes = service.get_nodes()

        assert len(all_nodes) == 2
        ids = {n.id for n in all_nodes}
        assert {"capability:c1", "module:m1"} == ids

    def test_get_nodes_with_filter(self) -> None:
        """Test retrieving nodes filtered by type."""
        cap = make_node("capability", "c1", "/c/c1", "c1")
        mod = make_node("module", "m1", "/m/m1", "m1")
        api = make_node("api", "api1", "/a/api1", "api1")

        graph = RepositoryGraph()
        graph.add_node(cap)
        graph.add_node(mod)
        graph.add_node(api)

        service = build_graph_service(graph)
        cap_nodes = service.get_nodes(node_type="capability")

        assert len(cap_nodes) == 1
        assert cap_nodes[0].id == "capability:c1"

        empty = service.get_nodes(node_type="nonexistent")
        assert len(empty) == 0

    def test_find_nodes_with_predicate(self) -> None:
        """Test predicate-based node search."""
        cap = make_node("capability", "prod_cap", "/c/prod", "prod", ownership="capability")
        mod = make_node("module", "util_mod", "/m/util", "mod1", ownership="shared_infrastructure")

        graph = RepositoryGraph()
        graph.add_node(cap)
        graph.add_node(mod)

        service = build_graph_service(graph)

        # Find capabilities by ownership
        def pred(n):
            return n.type == "capability" and n.ownership == "capability"
        results = service.find_nodes(pred)
        assert len(results) == 1
        assert results[0].name == "prod_cap"

        # Find all modules
        def pred2(n):
            return n.type == "module"
        mods = service.find_nodes(pred2)
        assert len(mods) == 1

    def test_successors(self) -> None:
        """Test successor lookup."""
        cap = make_node("capability", "c1", "/c/c1", "c1")
        mod1 = make_node("module", "m1", "/m/m1", "m1")
        mod2 = make_node("module", "m2", "/m/m2", "m2")
        edge1 = make_edge("capability", "c1", "module", "m1", "implements")
        edge2 = make_edge("capability", "c1", "module", "m2", "depends_on")

        graph = RepositoryGraph()
        graph.add_node(cap)
        graph.add_node(mod1)
        graph.add_node(mod2)
        graph.add_edge(edge1)
        graph.add_edge(edge2)

        service = build_graph_service(graph)

        # Get all successors of cap
        succ = service.successors("capability:c1")
        assert set(succ) == {"module:m1", "module:m2"}

        # Filtered by relationship type
        succ_impl = service.successors("capability:c1", edge_type="implements")
        assert succ_impl == ["module:m1"]

        # Non-existent node
        succ_miss = service.successors("capability:missing")
        assert succ_miss == []

    def test_predecessors(self) -> None:
        """Test predecessor lookup."""
        cap = make_node("capability", "c1", "/c/c1", "c1")
        mod1 = make_node("module", "m1", "/m/m1", "m1")
        edge = make_edge("capability", "c1", "module", "m1", "implements")

        graph = RepositoryGraph()
        graph.add_node(cap)
        graph.add_node(mod1)
        graph.add_edge(edge)

        service = build_graph_service(graph)

        preds = service.predecessors("module:m1")
        assert set(preds) == {"capability:c1"}

        # Filtered
        preds_impl = service.predecessors("module:m1", edge_type="implements")
        assert preds_impl == ["capability:c1"]

    def test_neighbors(self) -> None:
        """Test neighbor lookup (both directions)."""
        cap = make_node("capability", "c1", "/c/c1", "c1")
        mod1 = make_node("module", "m1", "/m/m1", "m1")
        mod2 = make_node("module", "m2", "/m/m2", "m2")
        edge1 = make_edge("capability", "c1", "module", "m1", "implements")
        edge2 = make_edge("module", "m1", "module", "m2", "imports")

        graph = RepositoryGraph()
        graph.add_node(cap)
        graph.add_node(mod1)
        graph.add_node(mod2)
        graph.add_edge(edge1)
        graph.add_edge(edge2)

        service = build_graph_service(graph)

        # Neighbors of m1 should include c1 (incoming) and m2 (outgoing)
        neigh = service.neighbors("module:m1")
        assert set(neigh) == {"capability:c1", "module:m2"}

    def test_find_paths(self) -> None:
        """Test path finding between nodes."""
        cap = make_node("capability", "c1", "/c/c1", "c1")
        mod1 = make_node("module", "m1", "/m/m1", "m1")
        mod2 = make_node("module", "m2", "/m/m2", "m2")
        endpoint = make_node("endpoint", "ep1", "/e/ep1", "ep1")

        edges = [
            make_edge("capability", "c1", "module", "m1", "implements"),
            make_edge("module", "m1", "module", "m2", "calls"),
            make_edge("module", "m2", "endpoint", "ep1", "owns"),
        ]

        graph = RepositoryGraph()
        for n in [cap, mod1, mod2, endpoint]:
            graph.add_node(n)
        for e in edges:
            graph.add_edge(e)

        service = build_graph_service(graph)

        # Find path from capability to endpoint
        paths = service.find_paths("capability:c1", "endpoint:ep1", max_depth=8)
        assert len(paths) > 0
        # Verify path goes through m1 and m2
        any_path = paths[0]
        assert any_path[0] == "capability:c1"
        assert any_path[-1] == "endpoint:ep1"
        assert len(any_path) == 4  # c1 -> m1 -> m2 -> ep1

        # No path between non-connected nodes
        no_paths = service.find_paths("capability:c1", "endpoint:missing")
        assert no_paths == []

    def test_find_edges(self) -> None:
        """Test finding edges connected to a node."""
        cap = make_node("capability", "c1", "/c/c1", "c1")
        mod1 = make_node("module", "m1", "/m/m1", "m1")
        mod2 = make_node("module", "m2", "/m/m2", "m2")

        out_edge = make_edge("capability", "c1", "module", "m1", "implements")
        in_edge = make_edge("module", "m2", "capability", "c1", "depends_on")

        graph = RepositoryGraph()
        for n in [cap, mod1, mod2]:
            graph.add_node(n)
        graph.add_edge(out_edge)
        graph.add_edge(in_edge)

        service = build_graph_service(graph)

        outgoing, incoming = service.find_edges("capability:c1")

        # Outgoing: implements -> m1
        assert len(outgoing) == 1
        assert outgoing[0].relationship == "implements"
        assert outgoing[0].target == "module:m1"

        # Incoming: depends_on from m2
        assert len(incoming) == 1
        assert incoming[0].relationship == "depends_on"
        assert incoming[0].source == "module:m2"

    def test_statistics(self) -> None:
        """Test statistics computation."""
        cap = make_node("capability", "c1", "/c/c1", "c1")
        mod = make_node("module", "m1", "/m/m1", "m1")
        edge = make_edge("capability", "c1", "module", "m1", "implements")

        graph = RepositoryGraph()
        graph.add_node(cap)
        graph.add_node(mod)
        graph.add_edge(edge)

        service = build_graph_service(graph)

        stats = service.statistics()
        assert stats["total_nodes"] == 2
        assert stats["total_edges"] == 1
        assert stats["node_types"]["capability"] == 1
        assert stats["node_types"]["module"] == 1
        assert stats["edge_relationships"]["implements"] == 1
        assert stats["ownership_distribution"]["unknown"] == 2  # Both nodes have unknown ownership by default

    def test_validate(self) -> None:
        """Test graph validation."""
        cap = make_node("capability", "c1", "/c/c1", "c1")
        mod = make_node("module", "m1", "/m/m1", "m1")
        edge = make_edge("capability", "c1", "module", "m1", "implements")

        graph = RepositoryGraph()
        graph.add_node(cap)
        graph.add_node(mod)
        graph.add_edge(edge)

        service = build_graph_service(graph)

        result = service.validate()
        assert result["valid"] is True
        assert result["node_count"] == 2
        assert result["edge_count"] == 1
        assert result["errors"] == []
        assert result["warnings"] == []

        # Test with invalid graph (duplicate edge)
        graph2 = RepositoryGraph()
        graph2.add_node(cap)
        graph2.add_node(mod)
        graph2.add_edge(edge)
        graph2.add_edge(edge)  # duplicate

        service2 = build_graph_service(graph2)
        result2 = service2.validate()
        # Should have warning about duplicate edge
        assert any("Duplicate edge" in w for w in result2["warnings"])

    def test_build_graph_service_from_graph(self) -> None:
        """Test build_graph_service factory function."""
        cap = make_node("capability", "c1", "/c/c1", "c1")
        graph = RepositoryGraph()
        graph.add_node(cap)

        service = build_graph_service(graph)
        node = service.get_node("capability:c1")
        assert node is not None
        assert node.name == "c1"

    def test_load_graph_service_from_index(self, tmp_path: Path) -> None:
        """Test loading from an index.json file."""
        # Create a minimal valid index structure
        cap = make_node("capability", "c1", "/c/c1", "c1")
        graph = RepositoryGraph()
        graph.add_node(cap)
        graph.generated_at = "testhash"
        graph.repository_root = "/tmp/test"

        # Write index in legacy format
        index_data = {
            "schema_version": "2.1",
            "generated_at": "testhash",
            "repository_root": "/tmp/test",
            "nodes": [cap.to_dict()],
            "edges": [],
        }

        index_file = tmp_path / "index.json"
        index_file.write_text(json.dumps(index_data), encoding="utf-8")

        # Load via RepositoryGraphService
        service = load_graph_service(tmp_path / "index.json")
        node = service.get_node("capability:c1")
        assert node is not None
        assert node.name == "c1"

    def test_new_format_with_metadata_graph_section(self, tmp_path: Path) -> None:
        """Test loading new index format with metadata/graph wrapper."""
        cap = make_node("capability", "c1", "/c/c1", "c1")
        mod = make_node("module", "m1", "/m/m1", "m1")

        index_data = {
            "metadata": {
                "schema_version": "2.2",
                "generator_version": "1.0.0",
                "generated_at": "testhash",
                "repository_root": "/tmp/test",
                "python_version": "3.11",
                "scanner_versions": {"MetadataScanner": "1.0"},
                "node_count": 2,
                "edge_count": 0,
                "node_types": {"capability": 1, "module": 1},
                "edge_relationships": {},
                "ownership_classes": ["capability", "unknown"],
                "validation_summary": {"total_nodes": 2, "total_edges": 0, "has_errors": False},
            },
            "graph": {
                "nodes": [cap.to_dict(), mod.to_dict()],
                "edges": [],
            },
            "gaps": {
                "missing_modules": [],
                "orphan_modules": [],
                "no_verification_evidence": [],
                "no_documentation_evidence": [],
                "unknown_ownership_modules": [],
                "missing_dependencies": [],
            },
        }

        index_file = tmp_path / "index.json"
        index_file.write_text(json.dumps(index_data), encoding="utf-8")

        service = load_graph_service(tmp_path / "index.json")
        nodes = service.get_nodes()
        assert len(nodes) == 2
        gaps = service.get_gaps()
        assert gaps is not None
        assert gaps.get("missing_modules") == []


class TestLegacyIndexCompatibility:
    """Tests for backward compatibility with legacy index formats."""

    def test_legacy_v21_format_loads(self, tmp_path: Path) -> None:
        """Old flat-format index (without metadata/graph wrapper) loads correctly."""
        cap = make_node("capability", "acct", "/cap/acct", "acct", ownership="capability")
        mod = make_node("module", "router", "/r/router", "router", ownership="capability")
        edge = make_edge("capability", "acct", "module", "router", "implements")

        graph = RepositoryGraph()
        graph.add_node(cap)
        graph.add_node(mod)
        graph.add_edge(edge)
        graph.generated_at = "v21hash"
        graph.repository_root = "/tmp/test"

        # Write legacy format (just nodes + edges at top level)
        index_data = {
            "schema_version": "2.1",
            "generated_at": "v21hash",
            "repository_root": "/tmp/test",
            "nodes": [cap.to_dict(), mod.to_dict()],
            "edges": [edge.to_dict()],
        }

        (tmp_path / "index.json").write_text(json.dumps(index_data), encoding="utf-8")

        service = load_graph_service(tmp_path / "index.json")
        assert service.get_node("capability:acct") is not None
        assert service.get_node("module:router") is not None
        # Old format doesn't have gaps section
        gaps = service.get_gaps()
        assert gaps == {}  # Empty dict when no gaps found


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
