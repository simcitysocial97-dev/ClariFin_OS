"""Tests for RepositoryQuery API using RepositoryGraphService — Phase 5.

These tests verify that the query methods work correctly against synthetic
graph data, without needing to scan an actual repository."""

import json
from pathlib import Path

import pytest

from repo_intelligence.schema import GraphNode, GraphEdge, RepositoryGraph
from repo_intelligence.graph_service import build_graph_service, load_graph_service


def make_node(node_type: str, name: str, path: str, id_str: str, ownership: str = "unknown", properties: dict | None = None) -> GraphNode:
    if properties is None:
        properties = {"id": id_str}
    return GraphNode(
        id=f"{node_type}:{id_str}",
        type=node_type,
        name=name,
        path=path,
        source=f"test:{id_str}",
        ownership=ownership,
        properties=properties,
    )


def make_edge(source_type: str, source_id: str, target_type: str, target_id: str, relationship: str, evidence: str = "") -> GraphEdge:
    return GraphEdge(
        source=f"{source_type}:{source_id}",
        target=f"{target_type}:{target_id}",
        relationship=relationship,
        confidence=1.0,
        evidence=evidence,
    )


class TestRepositoryIndexQueries:
    """Test query methods through RepositoryGraphService."""

    def test_list_capabilities(self) -> None:
        """Test listing capabilities."""
        cap1 = make_node("capability", "account_mgmt", "/cap/acct", "account_management", ownership="capability")
        cap2 = make_node("capability", "billing", "/cap/bill", "billing", ownership="capability")

        graph = RepositoryGraph()
        graph.add_node(cap1)
        graph.add_node(cap2)

        service = build_graph_service(graph)
        caps = service.get_nodes(node_type="capability")

        assert len(caps) == 2
        ids = {c.id for c in caps}
        assert {"capability:account_management", "capability:billing"} == ids

    def test_show_capability_with_details(self) -> None:
        """Test show_capability with related nodes and edges."""
        cap = make_node("capability", "acct_mgmt", "/cap/acct", "account_management", ownership="capability",
                        properties={"id": "account_management", "description": "Manage accounts"})

        # Implementing modules
        engine = make_node("module", "loan_engine", "/engines/loan", "loan_engine", ownership="capability",
                          properties={"module_type": "engine"})
        router = make_node("module", "acct_router", "/routers/acct", "acct_router", ownership="capability",
                          properties={"module_type": "router"})
        service_mod = make_node("module", "acct_svc", "/services/acct", "acct_svc", ownership="capability",
                               properties={"module_type": "service"})

        # Endpoint
        endpoint = make_node("endpoint", "get_account", "/api/v1/account", "ep1", ownership="unknown",
                             properties={"id": "ep1", "method": "GET", "path": "/v1/accounts", "capability": "account_management"})

        # Tests
        test_suite = make_node("test_suite", "test_acct", "/tests/acct_test", "test_acct", ownership="capability")

        # Documentation
        doc = make_node("documentation", "acct_docs", "/docs/acct.md", "doc1", ownership="capability")

        # Edges connecting everything
        edges = [
            make_edge("capability", "account_management", "module", "loan_engine", "implements"),
            make_edge("capability", "account_management", "module", "acct_router", "implements"),
            make_edge("capability", "account_management", "module", "acct_svc", "implements"),
            make_edge("capability", "account_management", "endpoint", "ep1", "implements"),
            make_edge("capability", "account_management", "test_suite", "test_acct", "tests"),
            make_edge("capability", "account_management", "documentation", "doc1", "documents"),
            make_edge("capability", "account_management", "database_table", "accounts", "owns"),
        ]

        table = make_node("database_table", "accounts", "/db/db.py", "accounts", ownership="capability")

        graph = RepositoryGraph()
        for n in [cap, engine, router, service_mod, endpoint, test_suite, doc, table]:
            graph.add_node(n)
        for e in edges:
            graph.add_edge(e)

        service = build_graph_service(graph)

        # Test we can find capability directly
        found = service.get_node("capability:account_management")
        assert found is not None
        assert found.name == "acct_mgmt"

        # Verify relationships via service API
        out_edges = service.find_edges(found.id)[0]
        impl_caps = [e for e in out_edges if e.relationship == "implements"]
        assert len(impl_caps) >= 4  # engine, router, service, endpoint

    def test_find_owner_of_router(self) -> None:
        """Test finding which capability owns a router."""
        cap = make_node("capability", "acct_mgmt", "/cap/acct", "account_management")
        router = make_node("module", "acct_router", "/routers/acct.py", "router_mod", ownership="capability",
                          properties={"module_type": "router"})

        edge = make_edge("capability", "account_management", "module", "router_mod", "implements")

        graph = RepositoryGraph()
        graph.add_node(cap)
        graph.add_node(router)
        graph.add_edge(edge)

        service = build_graph_service(graph)

        # Find node by path for router lookup
        def pred(n):
            return n.path == "/routers/acct.py"
        matching = service.find_nodes(pred)
        assert len(matching) == 1
        router_node = matching[0]

        # In a real RepositoryIndex, find_owner_of_router would use internal methods
        # Here we just verify the underlying data supports it via public API
        # Get all edges through the service's graph (we can access _graph for testing)
        incoming = [e for e in service._graph.edges if e.target == router_node.id and e.relationship == "implements"]
        assert len(incoming) == 1
        assert incoming[0].source == "capability:account_management"

    def test_list_nodes_by_ownership(self) -> None:
        """Test filtering nodes by ownership category."""
        cap_own = make_node("capability", "own_cap", "/cap/own", "c1", ownership="capability")
        shared = make_node("module", "shared_util", "/lib/util.py", "m1", ownership="shared_infrastructure")
        gen_art = make_node("generated_artifact", "gen", "/gen/file.json", "g1", ownership="generated")
        framework = make_node("workflow", "ci", "/.github/workflow/ci.yml", "w1", ownership="framework")

        graph = RepositoryGraph()
        for n in [cap_own, shared, gen_art, framework]:
            graph.add_node(n)

        service = build_graph_service(graph)

        # Test each ownership class
        cap_nodes = service.find_nodes(lambda n: n.ownership == "capability")
        assert len(cap_nodes) == 1 and cap_nodes[0].id == "capability:c1"

        shared_nodes = service.find_nodes(lambda n: n.ownership == "shared_infrastructure")
        assert len(shared_nodes) == 1

        gen_nodes = service.find_nodes(lambda n: n.ownership == "generated")
        assert len(gen_nodes) == 1

        fw_nodes = service.find_nodes(lambda n: n.ownership == "framework")
        assert len(fw_nodes) == 1

        # Unknown ownership (none in this set)
        unknown = service.find_nodes(lambda n: n.ownership == "unknown")
        assert len(unknown) == 0

    def test_find_paths_simple(self) -> None:
        """Test basic path finding between two nodes."""
        cap = make_node("capability", "c1", "/cap/c1", "c1")
        mod1 = make_node("module", "m1", "/mod/m1", "m1")
        mod2 = make_node("module", "m2", "/mod/m2", "m2")
        ep = make_node("endpoint", "ep1", "/ep/ep1", "ep1")

        edges = [
            make_edge("capability", "c1", "module", "m1", "implements"),
            make_edge("module", "m1", "module", "m2", "calls"),
            make_edge("module", "m2", "endpoint", "ep1", "owns"),
        ]

        graph = RepositoryGraph()
        for n in [cap, mod1, mod2, ep]:
            graph.add_node(n)
        for e in edges:
            graph.add_edge(e)

        service = build_graph_service(graph)

        paths = service.find_paths("capability:c1", "endpoint:ep1", max_depth=8)
        assert len(paths) > 0

        # Found path should be a list of node IDs from source to target
        any_path = paths[0]
        assert any_path[0] == "capability:c1"
        assert any_path[-1] == "endpoint:ep1"
        assert len(any_path) == 4  # c1 -> m1 -> m2 -> ep1

    def test_find_paths_no_path(self) -> None:
        """Test that no path returns empty list when no connection exists."""
        cap1 = make_node("capability", "c1", "/cap/c1", "c1")
        cap2 = make_node("capability", "c2", "/cap/c2", "c2")

        graph = RepositoryGraph()
        graph.add_node(cap1)
        graph.add_node(cap2)

        service = build_graph_service(graph)

        paths = service.find_paths("capability:c1", "capability:c2", max_depth=5)
        assert len(paths) == 0

    def test_statistics_roundtrip(self) -> None:
        """Test that statistics returns meaningful values."""
        cap = make_node("capability", "c1", "/cap/c1", "c1")
        mod1 = make_node("module", "m1", "/mod/m1", "m1")
        mod2 = make_node("module", "m2", "/mod/m2", "m2")
        edge1 = make_edge("capability", "c1", "module", "m1", "implements")
        edge2 = make_edge("capability", "c1", "module", "m2", "depends_on")

        graph = RepositoryGraph()
        for n in [cap, mod1, mod2]:
            graph.add_node(n)
        graph.add_edge(edge1)
        graph.add_edge(edge2)

        service = build_graph_service(graph)
        stats = service.statistics()

        assert stats["total_nodes"] == 3
        assert stats["total_edges"] == 2
        assert stats["node_types"]["capability"] == 1
        assert stats["node_types"]["module"] == 2
        assert "capability" in stats["ownership_distribution"] or "unknown" in stats["ownership_distribution"]

    def test_validate_clean_graph(self) -> None:
        """Test validate on a clean graph returns valid=True."""
        cap = make_node("capability", "c1", "/cap/c1", "c1")
        mod = make_node("module", "m1", "/mod/m1", "m1")
        edge = make_edge("capability", "c1", "module", "m1", "implements")

        graph = RepositoryGraph()
        graph.add_node(cap)
        graph.add_node(mod)
        graph.add_edge(edge)

        service = build_graph_service(graph)
        result = service.validate()

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
        assert result["node_count"] == 2
        assert result["edge_count"] == 1

    def test_validate_duplicate_edge_warning(self) -> None:
        """Test validate warns about duplicate edges."""
        cap = make_node("capability", "c1", "/cap/c1", "c1")
        mod = make_node("module", "m1", "/mod/m1", "m1")
        edge = make_edge("capability", "c1", "module", "m1", "implements")

        graph = RepositoryGraph()
        graph.add_node(cap)
        graph.add_node(mod)
        graph.add_edge(edge)
        graph.add_edge(edge)  # Duplicate

        service = build_graph_service(graph)
        result = service.validate()

        # Should have at least one warning about duplicate
        assert any("Duplicate edge" in w for w in result["warnings"])

    def test_lodading_from_index_with_gaps(self, tmp_path: Path) -> None:
        """Test loading index with gaps section populates service cache."""
        cap = make_node("capability", "c1", "/cap/c1", "c1")
        mod = make_node("module", "m1", "/mod/m1", "m1")

        index_data = {
            "metadata": {
                "schema_version": "2.2",
                "generator_version": "1.0.0",
                "generated_at": "hash123",
                "repository_root": "/tmp/test",
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
                "orphan_modules": [{"id": "module:m1", "path": "/mod/m1", "name": "m1"}],
                "no_verification_evidence": [],
                "no_documentation_evidence": [],
                "unknown_ownership_modules": [],
                "missing_dependencies": [],
            },
        }

        (tmp_path / "index.json").write_text(json.dumps(index_data), encoding="utf-8")

        service = load_graph_service(tmp_path / "index.json")
        gaps = service.get_gaps()

        assert gaps is not None
        assert len(gaps.get("orphan_modules", [])) == 1
        assert gaps["orphan_modules"][0]["name"] == "m1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
