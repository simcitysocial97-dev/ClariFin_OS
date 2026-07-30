"""Dependency Intelligence Engine.

Automatically discovers relationships between project components:
- Router -> Service
- Service -> Repository
- Engine -> Repository
- Capability -> Engines
- Capability -> Contracts
- Capability -> Golden Scenarios
- Capability -> Property Tests
- Capability -> Mutation Targets
- Capability -> Integration Tests

All information is derived automatically from the capability registry,
source code analysis, and filesystem discovery. No hardcoded dependency maps.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT
SRC_DIR = BACKEND_DIR / "src"
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"


@dataclass
class DependencyEdge:
    """A single dependency relationship between two components."""

    source: str
    source_type: str
    target: str
    target_type: str
    confidence: float = 1.0
    evidence: str = ""


@dataclass
class DependencyGraph:
    """Complete dependency graph for the project."""

    edges: list[DependencyEdge] = field(default_factory=list)
    capabilities: dict[str, dict[str, Any]] = field(default_factory=dict)
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "edges": [
                {
                    "source": e.source,
                    "source_type": e.source_type,
                    "target": e.target,
                    "target_type": e.target_type,
                    "confidence": e.confidence,
                    "evidence": e.evidence,
                }
                for e in self.edges
            ],
            "capabilities": self.capabilities,
            "generated_at": self.generated_at,
        }


class DependencyEngine:
    """Auto-discovers component dependencies from the codebase."""

    def __init__(self) -> None:
        self._edges: list[DependencyEdge] = []
        self._capabilities: dict[str, dict[str, Any]] = {}

    def discover(self) -> DependencyGraph:
        """Run all discovery passes and return the complete dependency graph."""
        self._edges = []
        self._capabilities = {}

        from src.verification.runtime.registries import load_capability_registry

        self._capability_registry = load_capability_registry()

        self._discover_from_capability_registry()
        self._discover_from_source_imports()
        self._discover_from_router_routing()
        self._discover_from_engine_references()
        self._discover_from_service_calls()
        self._discover_from_repository_usage()
        self._discover_capability_test_mapping()

        for cap in self._capability_registry.get("capabilities", []):
            cap_id = cap.get("id", "")
            self._capabilities[cap_id] = {
                "name": cap.get("name", cap_id),
                "risk": cap.get("risk", "unknown"),
                "criticality": cap.get("criticality", "unknown"),
                "engines": cap.get("engines", []),
                "services": cap.get("services", []),
                "routers": cap.get("routers", []),
                "repositories": cap.get("repositories", []),
                "dependencies": cap.get("dependencies", []),
                "contracts": cap.get("contracts", []),
                "golden_datasets": cap.get("golden_datasets", []),
                "property_tests": cap.get("property_tests", []),
                "invariants": cap.get("invariants", []),
                "architecture_tests": cap.get("architecture_tests", []),
            }

        import hashlib

        # Deterministic hash of edges + capabilities instead of timestamp
        content_hash = hashlib.sha256(
            str(
                sorted(
                    [
                        (e.source, e.source_type, e.target, e.target_type)
                        for e in self._edges
                    ]
                )
            ).encode()
        ).hexdigest()[:12]

        return DependencyGraph(
            edges=self._edges,
            capabilities=self._capabilities,
            generated_at=content_hash,
        )

    def _discover_from_capability_registry(self) -> None:
        """Discover dependencies from the capability registry's explicit fields."""
        from src.verification.runtime.registries import load_capability_registry

        registry = load_capability_registry()
        for cap in registry.get("capabilities", []):
            cap_id = cap.get("id", "")

            for engine in cap.get("engines", []):
                self._edges.append(
                    DependencyEdge(
                        source=cap_id,
                        source_type="capability",
                        target=engine,
                        target_type="engine",
                        confidence=1.0,
                        evidence="capability_registry.engines",
                    )
                )

            for service in cap.get("services", []):
                self._edges.append(
                    DependencyEdge(
                        source=cap_id,
                        source_type="capability",
                        target=service,
                        target_type="service",
                        confidence=1.0,
                        evidence="capability_registry.services",
                    )
                )

            for router in cap.get("routers", []):
                self._edges.append(
                    DependencyEdge(
                        source=cap_id,
                        source_type="capability",
                        target=router,
                        target_type="router",
                        confidence=1.0,
                        evidence="capability_registry.routers",
                    )
                )

            for repo in cap.get("repositories", []):
                self._edges.append(
                    DependencyEdge(
                        source=cap_id,
                        source_type="capability",
                        target=repo,
                        target_type="repository",
                        confidence=1.0,
                        evidence="capability_registry.repositories",
                    )
                )

            for dep_cap in cap.get("dependencies", []):
                self._edges.append(
                    DependencyEdge(
                        source=cap_id,
                        source_type="capability",
                        target=dep_cap,
                        target_type="capability",
                        confidence=0.9,
                        evidence="capability_registry.dependencies",
                    )
                )

            for contract in cap.get("contracts", []):
                self._edges.append(
                    DependencyEdge(
                        source=cap_id,
                        source_type="capability",
                        target=contract,
                        target_type="contract",
                        confidence=0.8,
                        evidence="capability_registry.contracts",
                    )
                )

            for dataset in cap.get("golden_datasets", []):
                self._edges.append(
                    DependencyEdge(
                        source=cap_id,
                        source_type="capability",
                        target=dataset,
                        target_type="golden_dataset",
                        confidence=0.9,
                        evidence="capability_registry.golden_datasets",
                    )
                )

            for prop_test in cap.get("property_tests", []):
                self._edges.append(
                    DependencyEdge(
                        source=cap_id,
                        source_type="capability",
                        target=prop_test,
                        target_type="property_test",
                        confidence=0.9,
                        evidence="capability_registry.property_tests",
                    )
                )

    def _discover_from_source_imports(self) -> None:
        """Discover dependencies from Python import statements in source files."""
        for py_file in SRC_DIR.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                source = py_file.read_text()
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            file_module = _path_to_module(py_file, SRC_DIR)
            if not file_module:
                continue

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and node.module.startswith("src.")
                ):
                    target_module = node.module
                    self._edges.append(
                        DependencyEdge(
                            source=file_module,
                            source_type="module",
                            target=target_module,
                            target_type="module",
                            confidence=0.7,
                            evidence=f"import_from:{node.module}",
                        )
                    )

    def _discover_from_router_routing(self) -> None:
        """Discover Router -> Service dependencies from router source code."""
        routers_dir = SRC_DIR / "routers"
        if not routers_dir.exists():
            return

        for py_file in routers_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                source = py_file.read_text()
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            router_name = py_file.stem
            router_module = f"src.routers.{router_name}"

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and "services" in node.module
                ):
                    self._edges.append(
                        DependencyEdge(
                            source=router_module,
                            source_type="router",
                            target=node.module,
                            target_type="service",
                            confidence=0.9,
                            evidence=f"router_import:{node.module}",
                        )
                    )

    def _discover_from_engine_references(self) -> None:
        """Discover Engine -> Repository dependencies from engine source code."""
        engines_dir = SRC_DIR / "engines"
        if not engines_dir.exists():
            return

        for py_file in engines_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                source = py_file.read_text()
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            engine_module = _path_to_module(py_file, SRC_DIR)
            if not engine_module:
                continue

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and "repositories" in node.module
                ):
                    self._edges.append(
                        DependencyEdge(
                            source=engine_module,
                            source_type="engine",
                            target=node.module,
                            target_type="repository",
                            confidence=0.9,
                            evidence=f"engine_import:{node.module}",
                        )
                    )

    def _discover_from_service_calls(self) -> None:
        """Discover Service -> Repository dependencies from service source code."""
        services_dir = SRC_DIR / "services"
        if not services_dir.exists():
            return

        for py_file in services_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                source = py_file.read_text()
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            service_module = _path_to_module(py_file, SRC_DIR)
            if not service_module:
                continue

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and "repositories" in node.module
                ):
                    self._edges.append(
                        DependencyEdge(
                            source=service_module,
                            source_type="service",
                            target=node.module,
                            target_type="repository",
                            confidence=0.9,
                            evidence=f"service_import:{node.module}",
                        )
                    )

    def _discover_from_repository_usage(self) -> None:
        """Discover Repository -> Model/DB dependencies from repository source code."""
        repos_dir = SRC_DIR / "repositories"
        if not repos_dir.exists():
            return

        for py_file in repos_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                source = py_file.read_text()
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            repo_module = _path_to_module(py_file, SRC_DIR)
            if not repo_module:
                continue

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and "models" in node.module
                ):
                    self._edges.append(
                        DependencyEdge(
                            source=repo_module,
                            source_type="repository",
                            target=node.module,
                            target_type="model",
                            confidence=0.85,
                            evidence=f"repo_import:{node.module}",
                        )
                    )

    def _discover_capability_test_mapping(self) -> None:
        """Map capabilities to their test files (property, invariant, golden, contract)."""
        from src.verification.runtime.discovery import (
            discover_capability_tests,
            discover_golden_datasets,
            discover_invariant_tests,
            discover_property_tests,
        )

        cap_tests = {c["id"]: c for c in discover_capability_tests()}

        for pt in discover_property_tests():
            cap_id = pt.get("capability")
            if cap_id and cap_id in cap_tests:
                self._edges.append(
                    DependencyEdge(
                        source=cap_id,
                        source_type="capability",
                        target=pt["path"],
                        target_type="property_test",
                        confidence=0.9,
                        evidence="discovery:property_test",
                    )
                )

        for cap_id, cap_data in cap_tests.items():
            for test_file in cap_data.get("test_files", []):
                self._edges.append(
                    DependencyEdge(
                        source=cap_id,
                        source_type="capability",
                        target=test_file,
                        target_type="capability_test",
                        confidence=1.0,
                        evidence="discovery:capability_test",
                    )
                )

        inv_paths = {inv["path"]: inv for inv in discover_invariant_tests()}
        for cap in self._capability_registry.get("capabilities", []):
            cap_id = cap.get("id", "")
            for inv_path in cap.get("invariants", []):
                if inv_path in inv_paths:
                    self._edges.append(
                        DependencyEdge(
                            source=cap_id,
                            source_type="capability",
                            target=inv_path,
                            target_type="invariant_test",
                            confidence=0.9,
                            evidence="discovery:invariant_test",
                        )
                    )

        gd_paths = {gd["path"]: gd for gd in discover_golden_datasets()}
        for cap in self._capability_registry.get("capabilities", []):
            cap_id = cap.get("id", "")
            for gd_path in cap.get("golden_datasets", []):
                if gd_path in gd_paths:
                    self._edges.append(
                        DependencyEdge(
                            source=cap_id,
                            source_type="capability",
                            target=gd_path,
                            target_type="golden_dataset",
                            confidence=0.9,
                            evidence="discovery:golden_dataset",
                        )
                    )


def _path_to_module(py_file: Path, base_dir: Path) -> str | None:
    """Convert a file path to a Python module name."""
    try:
        rel = py_file.relative_to(base_dir)
        parts = list(rel.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts)
    except ValueError:
        return None


def discover_dependencies() -> DependencyGraph:
    """Convenience function to discover all dependencies."""
    engine = DependencyEngine()
    return engine.discover()


def get_capability_dependencies(capability_id: str) -> list[DependencyEdge]:
    """Get all dependencies for a specific capability."""
    graph = discover_dependencies()
    return [
        e for e in graph.edges if e.source == capability_id or e.target == capability_id
    ]


def get_transitive_dependencies(
    capability_id: str, graph: DependencyGraph | None = None
) -> set[str]:
    """Get all transitive dependencies for a capability."""
    if graph is None:
        graph = discover_dependencies()

    visited: set[str] = {capability_id}
    queue: list[str] = [capability_id]

    while queue:
        current = queue.pop(0)
        for edge in graph.edges:
            if edge.source == current and edge.target not in visited:
                visited.add(edge.target)
                queue.append(edge.target)
            if edge.target == current and edge.source not in visited:
                visited.add(edge.source)
                queue.append(edge.source)

    visited.discard(capability_id)
    return visited


def get_dependents(
    capability_id: str, graph: DependencyGraph | None = None
) -> list[str]:
    """Get all capabilities that depend on the given capability."""
    if graph is None:
        graph = discover_dependencies()

    dependents: list[str] = []
    for edge in graph.edges:
        if edge.target == capability_id and edge.source_type == "capability":
            dependents.append(edge.source)
    return dependents
