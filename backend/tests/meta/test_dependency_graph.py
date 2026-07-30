"""Dependency graph validation tests.

Verifies that the dependency graph is internally consistent and complete.
"""

from __future__ import annotations

from runtime.discovery import discover_dependencies


class TestDependencyGraph:
    """Validate the dependency graph structure."""

    def test_graph_not_empty(self) -> None:
        """Dependency graph must not be empty."""
        dep_map = discover_dependencies()
        edges = dep_map.get("edges", [])
        capabilities = dep_map.get("capabilities", {})

        assert len(edges) > 0, "Dependency graph has no edges"
        assert len(capabilities) > 0, "Dependency graph has no capabilities"

    def test_all_capabilities_present(self) -> None:
        """All registered capabilities must appear in the dependency graph."""
        dep_map = discover_dependencies()
        capabilities = dep_map.get("capabilities", {})

        expected_caps = {
            "account_management",
            "credit_cards",
            "debt_management",
            "financial_events",
            "financial_health",
            "forecasting",
            "household_cashflow",
            "pattern_analysis",
            "recommendations",
            "reconciliation",
            "transaction_intelligence",
        }

        actual_caps = set(capabilities.keys())
        missing = expected_caps - actual_caps
        assert not missing, f"Missing capabilities in dependency graph: {missing}"

    def test_all_edge_types_present(self) -> None:
        """All required edge types must be present in the graph."""
        dep_map = discover_dependencies()
        edges = dep_map.get("edges", [])

        edge_types = {e.get("target_type", "") for e in edges}

        required_types = {
            "engine",
            "router",
            "service",
            "repository",
            "capability",
            "property_test",
            "contract",
            "golden_dataset",
            "invariant_test",
            "capability_test",
        }

        missing_types = required_types - edge_types
        assert (
            not missing_types
        ), f"Missing edge types in dependency graph: {missing_types}"

    def test_capability_edges_for_all_capabilities(self) -> None:
        """Every capability must have at least one edge."""
        dep_map = discover_dependencies()
        edges = dep_map.get("edges", [])
        capabilities = dep_map.get("capabilities", {})

        caps_with_edges = set()
        for edge in edges:
            if edge.get("source_type") == "capability":
                caps_with_edges.add(edge.get("source", ""))

        all_caps = set(capabilities.keys())
        missing = all_caps - caps_with_edges
        assert not missing, f"Capabilities without any edges: {missing}"

    def test_edge_sources_valid(self) -> None:
        """All capability-type edge sources must exist in capabilities."""
        dep_map = discover_dependencies()
        edges = dep_map.get("edges", [])
        capabilities = dep_map.get("capabilities", {})
        all_cap_ids = set(capabilities.keys())

        for edge in edges:
            if edge.get("source_type") == "capability":
                source = edge.get("source", "")
                assert (
                    source in all_cap_ids
                ), f"Edge source '{source}' not found in capabilities"

    def test_capability_dependency_edges_valid(self) -> None:
        """Capability-to-capability edges must reference valid capabilities."""
        dep_map = discover_dependencies()
        edges = dep_map.get("edges", [])
        capabilities = dep_map.get("capabilities", {})
        all_cap_ids = set(capabilities.keys())

        for edge in edges:
            if edge.get("target_type") == "capability":
                target = edge.get("target", "")
                assert (
                    target in all_cap_ids
                ), f"Capability dependency target '{target}' not found in capabilities"

    def test_dependency_graph_has_sufficient_edges(self) -> None:
        """Dependency graph must have a reasonable number of edges."""
        dep_map = discover_dependencies()
        edges = dep_map.get("edges", [])
        capabilities = dep_map.get("capabilities", {})

        min_edges = len(capabilities) * 3
        assert len(edges) >= min_edges, (
            f"Dependency graph has {len(edges)} edges, expected at least {min_edges} "
            f"(3 per capability)"
        )

    def test_capability_metadata_complete(self) -> None:
        """Each capability in the graph must have complete metadata."""
        dep_map = discover_dependencies()
        capabilities = dep_map.get("capabilities", {})

        required_fields = [
            "name",
            "risk",
            "criticality",
            "engines",
            "services",
            "routers",
            "repositories",
        ]

        for cap_id, cap_data in capabilities.items():
            for field in required_fields:
                assert (
                    field in cap_data
                ), f"Capability '{cap_id}' missing field '{field}' in dependency graph"

    def test_transitive_dependencies_work(self) -> None:
        """Transitive dependency resolution must work correctly."""
        from runtime.discovery import get_transitive_dependencies

        transitive = get_transitive_dependencies("forecasting")

        assert (
            "household_cashflow" in transitive
        ), "forecasting should transitively depend on household_cashflow"
        assert (
            "debt_management" in transitive
        ), "forecasting should transitively depend on debt_management"

    def test_get_dependents_works(self) -> None:
        """get_dependents must return capabilities that depend on the given one."""
        from runtime.discovery import get_dependents

        dependents = get_dependents("household_cashflow")
        assert len(dependents) > 0, "household_cashflow should have dependents"
        assert (
            "debt_management" in dependents
        ), "debt_management should depend on household_cashflow"
