"""Tests for RepositoryBuilder — Phase 3."""

import json
from pathlib import Path
import tempfile

from repo_intelligence.builder import RepositoryBuilder, ValidationSummary
from repo_intelligence.schema import GraphNode, GraphEdge, RepositoryGraph


def make_node(node_type: str, name: str, path: str, id_str: str, ownership: str = "unknown") -> GraphNode:
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
    return GraphEdge(
        source=f"{source_type}:{source_id}",
        target=f"{target_type}:{target_id}",
        relationship=relationship,
        confidence=1.0,
        evidence="test edge",
    )


def test_builder_can_create_instance() -> None:
    """Test that RepositoryBuilder can be instantiated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = RepositoryBuilder(Path(tmpdir))
        assert isinstance(builder, RepositoryBuilder)
        assert builder.repo_root is not None


def test_builder_assigns_ownership_correctly() -> None:
    """Test ownership classification logic."""
    builder = RepositoryBuilder(Path("/tmp"))

    # Test generated artifact ownership
    gen_node = make_node("generated_artifact", "gen", "/gen/file.json", "g1", ownership="unknown")
    classified = builder._classify_ownership(gen_node)
    assert classified == "generated"

    # Test package.json ownership
    pkg_node = make_node("package_json", "pkg", "/package/package.json", "p1")
    classified = builder._classify_ownership(pkg_node)
    assert classified == "framework"

    # Test script ownership
    script_node = make_node("script", "build", "/scripts/build.sh", "s1")
    classified = builder._classify_ownership(script_node)
    assert classified == "utility"

    # Test module with router type
    router_mod = make_node("module", "router", "/src/routers/router.py", "m1")
    router_mod.properties["module_type"] = "router"
    classified = builder._classify_ownership(router_mod)
    assert classified == "capability"

    # Test module with common type
    common_mod = make_node("module", "common", "/src/utils/common.py", "m2")
    common_mod.properties["module_type"] = "common"
    classified = builder._classify_ownership(common_mod)
    assert classified == "shared_infrastructure"

    # Default unknown
    unknown_mod = make_node("module", "unknown", "/src/unknown.py", "m3")
    unknown_mod.properties["module_type"] = "something"
    classified = builder._classify_ownership(unknown_mod)
    assert classified == "unknown"


def test_builder_detects_gaps() -> None:
    """Test gap detection in the builder."""
    builder = RepositoryBuilder(Path("/tmp"))

    # Create a graph with some nodes but no implements edges from capabilities
    cap = make_node("capability", "c1", "/cap/c1", "c1")
    mod = make_node("module", "m1", "/mod/m1", "m1")

    builder.graph = RepositoryGraph()
    builder.graph.add_node(cap)
    builder.graph.add_node(mod)
    builder.graph.generated_at = "test"

    builder._assign_ownership()
    gaps = builder._detect_gaps()

    # Should detect orphan module (m1 not implemented by any capability)
    assert len(gaps.get("orphan_modules", [])) == 1
    assert gaps["orphan_modules"][0]["name"] == "m1"

    # Missing modules should be empty (no implements edges to check)
    assert len(gaps.get("missing_modules", [])) == 0


def test_builder_write_index(tmp_path: Path) -> None:
    """Test that RepositoryBuilder.write_index creates valid index.json."""
    builder = RepositoryBuilder(Path("/tmp"))

    # Add a simple node to the graph
    cap = make_node("capability", "test_cap", "/cap/test", "cap1")
    builder.graph = RepositoryGraph()
    builder.graph.add_node(cap)
    builder.graph.generated_at = "hash123"
    builder.graph.repository_root = "/tmp/test"

    # Build and write
    output_path = tmp_path / "index.json"
    written = builder.write_index(output_path)

    assert written == output_path

    # Verify the file exists and has valid content
    assert output_path.exists()
    data = json.loads(output_path.read_text())

    # Should have metadata.graph format with schema_version 2.2
    assert "metadata" in data
    assert "graph" in data
    assert data["metadata"]["schema_version"] == "2.2"
    assert len(data["graph"]["nodes"]) == 1


def test_builder_get_metrics() -> None:
    """Test RepositoryBuilder.get_builder_metrics()."""
    builder = RepositoryBuilder(Path("/tmp"))

    cap = make_node("capability", "c1", "/cap/c1", "c1")
    mod = make_node("module", "m1", "/mod/m1", "m1")
    edge = make_edge("capability", "c1", "module", "m1", "implements")

    builder.graph = RepositoryGraph()
    builder.graph.add_node(cap)
    builder.graph.add_node(mod)
    builder.graph.add_edge(edge)
    builder.graph.generated_at = "test"
    builder._assign_ownership()
    gaps = builder._detect_gaps()

    metrics = builder.get_builder_metrics()
    assert metrics["total_nodes"] == 2
    assert metrics["total_edges"] == 1
    assert metrics["node_types"]["capability"] == 1
    assert metrics["node_types"]["module"] == 1
    assert "gaps" in metrics
    assert metrics["gaps"]["orphan_modules"] == 0  # m1 is now implemented
    assert metrics["gaps"]["missing_modules"] == 0


def test_validation_summary() -> None:
    """Test ValidationSummary class methods."""
    summary = ValidationSummary()
    assert summary.is_valid() is True

    summary.errors.append("test error")
    assert summary.is_valid() is False

    assert summary.node_count == 0
    assert summary.edge_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])