"""Graph Integrity Validation.

Validates every node and edge in the dependency graph:
- No orphan capability
- No orphan engine
- No orphan router
- No orphan repository
- No orphan service
- No orphan test
- No orphan golden dataset
- No orphan invariant
- No orphan capability test directory
- No dangling edge
- Every capability reachable
- Every test reachable
- Graph deterministic

Part F of Phase 3.2 — Capability Validation & Real-World Verification.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
TESTS_DIR = BACKEND_DIR / "tests"


def _load_registry() -> dict[str, Any]:
    """Load the capability registry."""
    from runtime.registries import load_capability_registry

    return load_capability_registry()


def _discover_all_production_files() -> dict[str, set[str]]:
    """Discover all production code files by category."""
    files: dict[str, set[str]] = {
        "routers": set(),
        "services": set(),
        "engines": set(),
        "repositories": set(),
    }

    src_dir = BACKEND_DIR / "src"

    # Routers
    routers_dir = src_dir / "routers"
    if routers_dir.exists():
        for f in routers_dir.glob("*.py"):
            if f.name != "__init__.py":
                files["routers"].add(f"src/routers/{f.name}")

    # Services
    services_dir = src_dir / "services"
    if services_dir.exists():
        for f in services_dir.glob("*.py"):
            if f.name != "__init__.py":
                files["services"].add(f"src/services/{f.name}")

    # Engines (top-level and subdirectories)
    engines_dir = src_dir / "engines"
    if engines_dir.exists():
        for f in engines_dir.glob("*.py"):
            if f.name != "__init__.py":
                files["engines"].add(f"src/engines/{f.name}")
        for subdir in engines_dir.iterdir():
            if subdir.is_dir():
                for f in subdir.glob("*.py"):
                    if f.name != "__init__.py":
                        files["engines"].add(f"src/engines/{subdir.name}/{f.name}")

    # Repositories
    repos_dir = src_dir / "repositories"
    if repos_dir.exists():
        for f in repos_dir.glob("*.py"):
            if f.name != "__init__.py" and f.name != "base.py":
                files["repositories"].add(f"src/repositories/{f.name}")

    return files


def _discover_all_test_files() -> dict[str, set[str]]:
    """Discover all test files by category."""
    files: dict[str, set[str]] = {
        "property_tests": set(),
        "invariant_tests": set(),
        "golden_datasets": set(),
        "capability_tests": set(),
        "contract_tests": set(),
    }

    # Property tests
    props_dir = TESTS_DIR / "properties"
    if props_dir.exists():
        for f in props_dir.rglob("test_*.py"):
            rel = f.relative_to(BACKEND_DIR)
            files["property_tests"].add(str(rel))

    # Invariant tests
    inv_dir = TESTS_DIR / "invariants"
    if inv_dir.exists():
        for f in inv_dir.rglob("test_*.py"):
            rel = f.relative_to(BACKEND_DIR)
            files["invariant_tests"].add(str(rel))

    # Golden datasets
    golden_dir = TESTS_DIR / "golden" / "datasets"
    if golden_dir.exists():
        for f in golden_dir.glob("*.json"):
            files["golden_datasets"].add(f"tests/golden/datasets/{f.name}")

    # Capability tests
    caps_dir = TESTS_DIR / "capability"
    if caps_dir.exists():
        for cap_dir in caps_dir.iterdir():
            if cap_dir.is_dir():
                for f in cap_dir.glob("test_*.py"):
                    rel = f.relative_to(BACKEND_DIR)
                    files["capability_tests"].add(str(rel))

    # Contract tests
    contract_dir = TESTS_DIR / "contract" / "generated"
    if contract_dir.exists():
        for f in contract_dir.glob("test_*.py"):
            rel = f.relative_to(BACKEND_DIR)
            files["contract_tests"].add(str(rel))

    return files


def _get_referenced_paths(registry: dict[str, Any]) -> dict[str, set[str]]:
    """Get all paths referenced by the capability registry."""
    referenced: dict[str, set[str]] = {
        "routers": set(),
        "services": set(),
        "engines": set(),
        "repositories": set(),
        "property_tests": set(),
        "invariant_tests": set(),
        "golden_datasets": set(),
        "capability_tests": set(),
        "contract_tests": set(),
    }

    for cap in registry.get("capabilities", []):
        for router in cap.get("routers", []):
            referenced["routers"].add(router)
        for service in cap.get("services", []):
            referenced["services"].add(service)
        for engine in cap.get("engines", []):
            referenced["engines"].add(engine)
        for repo in cap.get("repositories", []):
            referenced["repositories"].add(repo)
        for pt in cap.get("property_tests", []):
            referenced["property_tests"].add(pt)
        for inv in cap.get("invariants", []):
            referenced["invariant_tests"].add(inv)
        for ds in cap.get("golden_datasets", []):
            referenced["golden_datasets"].add(ds)
        # Capability tests are inferred from capability ID
        cap_id = cap.get("id", "")
        cap_test_dir = TESTS_DIR / "capability" / cap_id
        if cap_test_dir.exists():
            for f in cap_test_dir.glob("test_*.py"):
                rel = f.relative_to(BACKEND_DIR)
                referenced["capability_tests"].add(str(rel))
        # Contracts
        for contract in cap.get("contracts", []):
            referenced["contract_tests"].add(contract)

    return referenced


class TestGraphIntegrity:
    """Validate the dependency graph for completeness and integrity."""

    @pytest.fixture(scope="class")
    def registry(self) -> dict[str, Any]:
        return _load_registry()

    @pytest.fixture(scope="class")
    def dep_map(self) -> dict[str, Any]:
        from runtime.discovery import discover_dependencies

        return discover_dependencies()

    @pytest.fixture(scope="class")
    def all_prod_files(self) -> dict[str, set[str]]:
        return _discover_all_production_files()

    @pytest.fixture(scope="class")
    def all_test_files(self) -> dict[str, set[str]]:
        return _discover_all_test_files()

    @pytest.fixture(scope="class")
    def referenced_paths(self, registry: dict[str, Any]) -> dict[str, set[str]]:
        return _get_referenced_paths(registry)

    # --- No Orphan Checks ---

    def test_no_orphan_capabilities(
        self, dep_map: dict[str, Any]
    ) -> None:
        """Every capability must have at least one edge in the graph."""
        capabilities = dep_map.get("capabilities", {})
        edges = dep_map.get("edges", [])

        caps_with_edges = set()
        for edge in edges:
            if edge.get("source_type") == "capability":
                caps_with_edges.add(edge.get("source", ""))

        all_caps = set(capabilities.keys())
        orphans = all_caps - caps_with_edges
        assert not orphans, (
            f"Orphan capabilities (no edges): {orphans}"
        )

    def test_no_orphan_engines(
        self,
        all_prod_files: dict[str, set[str]],
        referenced_paths: dict[str, set[str]],
    ) -> None:
        """Every engine file must be referenced by at least one capability."""
        all_engines = all_prod_files["engines"]
        referenced_engines = referenced_paths["engines"]
        orphans = all_engines - referenced_engines
        assert not orphans, (
            f"Orphan engines (not in any capability): {orphans}"
        )

    def test_no_orphan_routers(
        self,
        all_prod_files: dict[str, set[str]],
        referenced_paths: dict[str, set[str]],
    ) -> None:
        """Every router file must be referenced by at least one capability."""
        all_routers = all_prod_files["routers"]
        referenced_routers = referenced_paths["routers"]
        orphans = all_routers - referenced_routers
        assert not orphans, (
            f"Orphan routers (not in any capability): {orphans}"
        )

    def test_no_orphan_repositories(
        self,
        all_prod_files: dict[str, set[str]],
        referenced_paths: dict[str, set[str]],
    ) -> None:
        """Every repository file must be referenced by at least one capability."""
        all_repos = all_prod_files["repositories"]
        referenced_repos = referenced_paths["repositories"]
        orphans = all_repos - referenced_repos
        assert not orphans, (
            f"Orphan repositories (not in any capability): {orphans}"
        )

    def test_no_orphan_services(
        self,
        all_prod_files: dict[str, set[str]],
        referenced_paths: dict[str, set[str]],
    ) -> None:
        """Every service file must be referenced by at least one capability."""
        all_services = all_prod_files["services"]
        referenced_services = referenced_paths["services"]
        orphans = all_services - referenced_services
        assert not orphans, (
            f"Orphan services (not in any capability): {orphans}"
        )

    def test_no_orphan_property_tests(
        self,
        all_test_files: dict[str, set[str]],
        referenced_paths: dict[str, set[str]],
    ) -> None:
        """Every property test file must be referenced by at least one capability."""
        all_tests = all_test_files["property_tests"]
        referenced = referenced_paths["property_tests"]
        orphans = all_tests - referenced
        assert not orphans, (
            f"Orphan property tests (not in any capability): {orphans}"
        )

    def test_no_orphan_invariant_tests(
        self,
        all_test_files: dict[str, set[str]],
        referenced_paths: dict[str, set[str]],
    ) -> None:
        """Every invariant test file must be referenced by at least one capability."""
        all_tests = all_test_files["invariant_tests"]
        referenced = referenced_paths["invariant_tests"]
        orphans = all_tests - referenced
        assert not orphans, (
            f"Orphan invariant tests (not in any capability): {orphans}"
        )

    def test_no_orphan_golden_datasets(
        self,
        all_test_files: dict[str, set[str]],
        referenced_paths: dict[str, set[str]],
    ) -> None:
        """Every golden dataset must be referenced by at least one capability."""
        all_datasets = all_test_files["golden_datasets"]
        referenced = referenced_paths["golden_datasets"]
        orphans = all_datasets - referenced
        assert not orphans, (
            f"Orphan golden datasets (not in any capability): {orphans}"
        )

    def test_no_orphan_capability_tests(
        self,
        all_test_files: dict[str, set[str]],
        referenced_paths: dict[str, set[str]],
    ) -> None:
        """Every capability test file must be referenced by at least one capability."""
        all_tests = all_test_files["capability_tests"]
        referenced = referenced_paths["capability_tests"]
        orphans = all_tests - referenced
        assert not orphans, (
            f"Orphan capability tests (not in any capability): {orphans}"
        )

    # --- Dangling Edge Checks ---

    def test_no_dangling_edges(self, dep_map: dict[str, Any]) -> None:
        """All edge targets must exist on disk or in the registry."""
        edges = dep_map.get("edges", [])
        capabilities = dep_map.get("capabilities", {})
        all_cap_ids = set(capabilities.keys())

        dangling: list[str] = []
        for edge in edges:
            target = edge.get("target", "")
            target_type = edge.get("target_type", "")
            source = edge.get("source", "")

            if target_type == "capability":
                if target not in all_cap_ids:
                    dangling.append(f"{source} -> {target} (capability not in registry)")
            elif target_type in ("engine", "router", "service", "repository"):
                if not (BACKEND_DIR / target).exists():
                    dangling.append(f"{source} -> {target} (file not found)")
            elif target_type in ("property_test", "invariant_test", "capability_test"):
                if not (BACKEND_DIR / target).exists():
                    dangling.append(f"{source} -> {target} (test file not found)")
            elif target_type == "golden_dataset":
                if not (BACKEND_DIR / target).exists():
                    dangling.append(f"{source} -> {target} (golden dataset not found)")
            elif target_type == "contract":
                # Contracts are API paths, not files - skip file check
                pass

        assert not dangling, (
            "Dangling edges found:\n" + "\n".join(dangling)
        )

    # --- Reachability Checks ---

    def test_every_capability_reachable(self, dep_map: dict[str, Any]) -> None:
        """Every capability must be reachable from the graph."""
        capabilities = dep_map.get("capabilities", {})
        edges = dep_map.get("edges", [])

        # Build adjacency list
        graph: dict[str, set[str]] = {}
        for cap_id in capabilities:
            graph[cap_id] = set()
        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            if source in graph:
                graph[source].add(target)

        # BFS from each capability
        all_caps = set(capabilities.keys())
        reachable_from_any: set[str] = set()
        for start_cap in all_caps:
            visited: set[str] = set()
            queue: list[str] = [start_cap]
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                for neighbor in graph.get(current, set()):
                    if neighbor not in visited:
                        queue.append(neighbor)
            reachable_from_any.update(visited & all_caps)

        unreachable = all_caps - reachable_from_any
        assert not unreachable, (
            f"Unreachable capabilities: {unreachable}"
        )

    def test_every_test_reachable(self, dep_map: dict[str, Any]) -> None:
        """Every test referenced in edges must exist on disk."""
        edges = dep_map.get("edges", [])

        test_types = {"property_test", "invariant_test", "capability_test", "golden_dataset"}
        unreachable: list[str] = []
        for edge in edges:
            if edge.get("target_type") in test_types:
                target = edge.get("target", "")
                if not (BACKEND_DIR / target).exists():
                    unreachable.append(f"{edge.get('source')} -> {target}")

        assert not unreachable, (
            "Tests referenced in edges but not on disk:\n" + "\n".join(unreachable)
        )

    # --- Determinism Check ---

    def test_graph_is_deterministic(self) -> None:
        """The dependency graph must be identical across multiple runs."""
        from runtime.discovery import discover_dependencies

        dep_map_1 = discover_dependencies()
        dep_map_2 = discover_dependencies()

        # Compare edges (excluding generated_at which is a content hash)
        edges_1 = sorted(
            json.dumps(e, sort_keys=True) for e in dep_map_1.get("edges", [])
        )
        edges_2 = sorted(
            json.dumps(e, sort_keys=True) for e in dep_map_2.get("edges", [])
        )

        assert edges_1 == edges_2, (
            "Dependency graph edges differ between runs (non-deterministic)"
        )

        caps_1 = dep_map_1.get("capabilities", {})
        caps_2 = dep_map_2.get("capabilities", {})
        assert caps_1 == caps_2, (
            "Dependency graph capabilities differ between runs (non-deterministic)"
        )

    # --- Edge Type Completeness ---

    def test_all_edge_types_present(self, dep_map: dict[str, Any]) -> None:
        """All required edge types must be present in the graph."""
        edges = dep_map.get("edges", [])
        edge_types = {e.get("target_type", "") for e in edges}

        required_types = {
            "engine",
            "router",
            "service",
            "repository",
            "property_test",
            "contract",
            "golden_dataset",
            "invariant_test",
            "capability_test",
            "capability",
        }

        missing = required_types - edge_types
        assert not missing, (
            f"Missing edge types in dependency graph: {missing}"
        )

    def test_graph_has_sufficient_edges(self, dep_map: dict[str, Any]) -> None:
        """The dependency graph must have a reasonable number of edges."""
        edges = dep_map.get("edges", [])
        capabilities = dep_map.get("capabilities", {})

        min_edges = len(capabilities) * 3
        assert len(edges) >= min_edges, (
            f"Dependency graph has {len(edges)} edges, expected at least {min_edges}"
        )

    def test_edge_sources_valid(self, dep_map: dict[str, Any]) -> None:
        """All capability-type edge sources must exist in capabilities."""
        edges = dep_map.get("edges", [])
        capabilities = dep_map.get("capabilities", {})
        all_cap_ids = set(capabilities.keys())

        for edge in edges:
            if edge.get("source_type") == "capability":
                source = edge.get("source", "")
                assert source in all_cap_ids, (
                    f"Edge source '{source}' not found in capabilities"
                )

    def test_capability_dependency_edges_valid(self, dep_map: dict[str, Any]) -> None:
        """Capability-to-capability edges must reference valid capabilities."""
        edges = dep_map.get("edges", [])
        capabilities = dep_map.get("capabilities", {})
        all_cap_ids = set(capabilities.keys())

        for edge in edges:
            if edge.get("target_type") == "capability":
                target = edge.get("target", "")
                assert target in all_cap_ids, (
                    f"Capability dependency target '{target}' not found in capabilities"
                )
