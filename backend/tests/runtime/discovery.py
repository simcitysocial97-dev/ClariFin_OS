"""Automatic discovery mechanisms for the Verification Runtime.

Discovers verification components without manual wiring:
- Engines (src/engines/)
- Services (src/services/)
- Repositories (src/repositories/)
- Routers (src/routers/)
- Capabilities (via capability-registry.yaml)
- Builders (tests/domain/builders/, tests/golden/builders/)
- Fixtures (conftest.py files)
- Property tests (tests/properties/)
- Invariant tests (tests/invariants/)
- Golden datasets (tests/golden/datasets/)
- Contract tests (tests/contract/generated/)
- Capability tests (tests/capability/)
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from runtime.registries import get_capability_by_id

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
SRC_DIR = BACKEND_DIR / "src"
TESTS_DIR = BACKEND_DIR / "tests"

# =============================================================================
# Production Code Discovery
# =============================================================================

def discover_engines() -> list[dict[str, Any]]:
    """Discover all engine modules in src/engines/."""
    engines: list[dict[str, Any]] = []
    engines_dir = SRC_DIR / "engines"
    if not engines_dir.exists():
        return engines

    for py_file in engines_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        rel_path = py_file.relative_to(BACKEND_DIR)
        engines.append(
            {
                "path": str(rel_path),
                "name": py_file.stem,
                "module": f"src.engines.{py_file.relative_to(engines_dir).with_suffix('').as_posix().replace('/', '.')}",
            }
        )
    return sorted(engines, key=lambda e: e["path"])

def discover_services() -> list[dict[str, Any]]:
    """Discover all service modules in src/services/."""
    services: list[dict[str, Any]] = []
    services_dir = SRC_DIR / "services"
    if not services_dir.exists():
        return services

    for py_file in services_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        rel_path = py_file.relative_to(BACKEND_DIR)
        services.append(
            {
                "path": str(rel_path),
                "name": py_file.stem,
                "module": f"src.services.{py_file.stem}",
            }
        )
    return sorted(services, key=lambda s: s["path"])

def discover_repositories() -> list[dict[str, Any]]:
    """Discover all repository modules in src/repositories/."""
    repos: list[dict[str, Any]] = []
    repos_dir = SRC_DIR / "repositories"
    if not repos_dir.exists():
        return repos

    for py_file in repos_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        rel_path = py_file.relative_to(BACKEND_DIR)
        repos.append(
            {
                "path": str(rel_path),
                "name": py_file.stem,
                "module": f"src.repositories.{py_file.stem}",
            }
        )
    return sorted(repos, key=lambda r: r["path"])

def discover_routers() -> list[dict[str, Any]]:
    """Discover all router modules in src/routers/."""
    routers: list[dict[str, Any]] = []
    routers_dir = SRC_DIR / "routers"
    if not routers_dir.exists():
        return routers

    for py_file in routers_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        rel_path = py_file.relative_to(BACKEND_DIR)
        routers.append(
            {
                "path": str(rel_path),
                "name": py_file.stem,
                "module": f"src.routers.{py_file.stem}",
            }
        )
    return sorted(routers, key=lambda r: r["path"])

# =============================================================================
# Test Infrastructure Discovery
# =============================================================================

def discover_builders() -> list[dict[str, Any]]:
    """Discover all builder modules in tests/domain/builders/ and tests/golden/builders/."""
    builders: list[dict[str, Any]] = []
    for builder_dir in [
        TESTS_DIR / "domain" / "builders",
        TESTS_DIR / "golden" / "builders",
    ]:
        if not builder_dir.exists():
            continue
        for py_file in builder_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            rel_path = py_file.relative_to(BACKEND_DIR)
            builders.append(
                {
                    "path": str(rel_path),
                    "name": py_file.stem,
                    "type": "domain" if "domain" in str(builder_dir) else "golden",
                }
            )
    return sorted(builders, key=lambda b: b["path"])

def discover_fixtures() -> list[dict[str, Any]]:
    """Discover all conftest.py files and their fixtures."""
    fixtures: list[dict[str, Any]] = []
    for conftest in TESTS_DIR.rglob("conftest.py"):
        rel_path = conftest.relative_to(BACKEND_DIR)
        fixtures.append(
            {
                "path": str(rel_path),
                "scope": _get_fixture_scope(conftest),
            }
        )
    return sorted(fixtures, key=lambda f: f["path"])

def _get_fixture_scope(conftest_path: Path) -> str:
    """Determine fixture scope from conftest location."""
    parts = conftest_path.relative_to(TESTS_DIR).parts
    if len(parts) == 1:
        return "global"
    return "/".join(parts[:-1])

def discover_golden_datasets() -> list[dict[str, Any]]:
    """Discover all golden dataset JSON files."""
    datasets: list[dict[str, Any]] = []
    datasets_dir = TESTS_DIR / "golden" / "datasets"
    if not datasets_dir.exists():
        return datasets

    for json_file in datasets_dir.glob("*.json"):
        rel_path = json_file.relative_to(BACKEND_DIR)
        datasets.append(
            {
                "path": str(rel_path),
                "name": json_file.stem,
            }
        )
    return sorted(datasets, key=lambda d: d["name"])

def discover_property_tests() -> list[dict[str, Any]]:
    """Discover all property test files."""
    tests: list[dict[str, Any]] = []
    props_dir = TESTS_DIR / "properties"
    if not props_dir.exists():
        return tests

    for py_file in props_dir.rglob("test_*.py"):
        rel_path = py_file.relative_to(BACKEND_DIR)
        tests.append(
            {
                "path": str(rel_path),
                "name": py_file.stem,
                "capability": _infer_capability_from_path(py_file),
            }
        )
    return sorted(tests, key=lambda t: t["path"])

def discover_invariant_tests() -> list[dict[str, Any]]:
    """Discover all invariant test files."""
    tests: list[dict[str, Any]] = []
    inv_dir = TESTS_DIR / "invariants"
    if not inv_dir.exists():
        return tests

    for py_file in inv_dir.rglob("test_*.py"):
        rel_path = py_file.relative_to(BACKEND_DIR)
        tests.append(
            {
                "path": str(rel_path),
                "name": py_file.stem,
            }
        )
    return sorted(tests, key=lambda t: t["path"])

def discover_invariant_modules() -> list[dict[str, Any]]:
    """Discover all invariant assertion modules (non-test files)."""
    modules: list[dict[str, Any]] = []
    inv_dir = TESTS_DIR / "invariants"
    if not inv_dir.exists():
        return modules

    for py_file in inv_dir.glob("*.py"):
        if py_file.name.startswith("test_") or py_file.name == "__init__.py":
            continue
        rel_path = py_file.relative_to(BACKEND_DIR)
        functions = _extract_assert_functions(py_file)
        modules.append(
            {
                "path": str(rel_path),
                "name": py_file.stem,
                "functions": functions,
            }
        )
    return sorted(modules, key=lambda m: m["name"])

def discover_contract_tests() -> list[dict[str, Any]]:
    """Discover all generated contract test files."""
    tests: list[dict[str, Any]] = []
    contract_dir = TESTS_DIR / "contract" / "generated"
    if not contract_dir.exists():
        return tests

    for py_file in contract_dir.glob("test_*.py"):
        rel_path = py_file.relative_to(BACKEND_DIR)
        tests.append(
            {
                "path": str(rel_path),
                "name": py_file.stem,
            }
        )
    return sorted(tests, key=lambda t: t["path"])

def discover_capability_tests() -> list[dict[str, Any]]:
    """Discover all capability test directories."""
    caps: list[dict[str, Any]] = []
    caps_dir = TESTS_DIR / "capability"
    if not caps_dir.exists():
        return caps

    for cap_dir in sorted(caps_dir.iterdir()):
        if not cap_dir.is_dir():
            continue
        test_files = list(cap_dir.glob("test_*.py"))
        caps.append(
            {
                "id": cap_dir.name,
                "path": str(cap_dir.relative_to(BACKEND_DIR)),
                "test_files": [str(f.relative_to(BACKEND_DIR)) for f in test_files],
            }
        )
    return caps

# =============================================================================
# Capability Registry Integration
# =============================================================================

def discover_capabilities() -> list[dict[str, Any]]:
    """Discover capabilities from capability-registry.yaml."""
    from runtime.registries import load_capability_registry

    registry = load_capability_registry()
    return registry.get("capabilities", [])

def get_capability_test_paths(capability_id: str) -> dict[str, list[str]]:
    """Get all test paths for a capability from the registry."""
    cap = get_capability_by_id(capability_id)
    if not cap:
        return {}

    return {
        "property_tests": cap.get("property_tests", []),
        "invariants": cap.get("invariants", []),
        "golden_datasets": cap.get("golden_datasets", []),
        "architecture_tests": cap.get("architecture_tests", []),
        "contracts": cap.get("contracts", []),
    }

# =============================================================================
# Helper Functions
# =============================================================================

def _infer_capability_from_path(path: Path) -> str | None:
    """Infer capability ID from a test file path."""
    parts = path.relative_to(TESTS_DIR / "properties").parts
    if parts:
        return parts[0]
    return None

def _extract_assert_functions(py_file: Path) -> list[str]:
    """Extract function names starting with assert_ from a Python file."""
    functions: list[str] = []
    try:
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("assert_"):
                functions.append(node.name)
    except SyntaxError:
        pass
    return functions

# =============================================================================
# Full System Discovery
# =============================================================================

def discover_all() -> dict[str, Any]:
    """Run all discovery mechanisms and return a complete system map.

    This is the single source of truth for what exists in the verification system.
    """
    return {
        "engines": discover_engines(),
        "services": discover_services(),
        "repositories": discover_repositories(),
        "routers": discover_routers(),
        "capabilities": discover_capabilities(),
        "builders": discover_builders(),
        "fixtures": discover_fixtures(),
        "golden_datasets": discover_golden_datasets(),
        "property_tests": discover_property_tests(),
        "invariant_tests": discover_invariant_tests(),
        "invariant_modules": discover_invariant_modules(),
        "contract_tests": discover_contract_tests(),
        "capability_tests": discover_capability_tests(),
    }

def get_verification_map() -> dict[str, Any]:
    """Get a capability-centric verification map.

    For each capability, lists all associated verification components.
    """
    capabilities = discover_capabilities()
    cap_tests = {c["id"]: c for c in discover_capability_tests()}
    prop_tests = discover_property_tests()
    inv_tests = discover_invariant_tests()
    datasets = discover_golden_datasets()

    verification_map: dict[str, Any] = {}

    for cap in capabilities:
        cap_id = cap["id"]
        cap_test = cap_tests.get(cap_id, {})
        registry_paths = get_capability_test_paths(cap_id)

        verification_map[cap_id] = {
            "name": cap.get("name", cap_id),
            "criticality": cap.get("criticality", "unknown"),
            "risk": cap.get("risk", "unknown"),
            "capability_test_path": cap_test.get("path"),
            "property_tests": [
                t["path"] for t in prop_tests if t.get("capability") == cap_id
            ]
            + registry_paths.get("property_tests", []),
            "invariant_tests": [
                t["path"]
                for t in inv_tests
                if t["path"] in registry_paths.get("invariants", [])
            ],
            "golden_datasets": [
                d["path"]
                for d in datasets
                if d["path"] in registry_paths.get("golden_datasets", [])
            ],
            "contracts": registry_paths.get("contracts", []),
            "engines": cap.get("engines", []),
            "services": cap.get("services", []),
            "routers": cap.get("routers", []),
            "repositories": cap.get("repositories", []),
        }

    return verification_map

# =============================================================================
# Dependency Intelligence (Workstream 1)
# =============================================================================

def discover_dependencies() -> dict[str, Any]:
    """Discover component dependencies using the intelligence layer.

    Returns a dict with 'edges' and 'capabilities' keys.
    Generates all 8 required edge types:
    - capability → source (engines)
    - capability → routers
    - capability → services
    - capability → repositories
    - capability → engines
    - capability → unit tests
    - capability → property tests
    - capability → contract tests
    - capability → capability tests
    - capability → golden datasets
    - capability → invariant tests

    Falls back to capability registry data if intelligence layer unavailable.
    """
    # Try the full DependencyEngine first (generates all edge types)
    try:
        from src.verification.intelligence.dependency_engine import (
            DependencyEngine,
        )

        engine = DependencyEngine()
        graph = engine.discover()
        return graph.to_dict()
    except (ImportError, Exception):
        pass

    try:
        from verification.intelligence.dependency_engine import (
            DependencyEngine,
        )

        engine = DependencyEngine()
        graph = engine.discover()
        return graph.to_dict()
    except (ImportError, Exception):
        pass

    # Fallback: derive all edge types from capability registry + filesystem
    from runtime.registries import load_capability_registry

    registry = load_capability_registry()
    edges: list[dict[str, Any]] = []
    capabilities: dict[str, dict[str, Any]] = {}

    # Discover test files from filesystem
    cap_tests = {c["id"]: c for c in discover_capability_tests()}

    for cap in registry.get("capabilities", []):
        cap_id = cap.get("id", "")
        capabilities[cap_id] = {
            "name": cap.get("name", cap_id),
            "risk": cap.get("risk", "unknown"),
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

        # capability → engines (source)
        for engine in cap.get("engines", []):
            edges.append(
                {
                    "source": cap_id,
                    "source_type": "capability",
                    "target": engine,
                    "target_type": "engine",
                    "confidence": 1.0,
                    "evidence": "capability_registry.engines",
                }
            )

        # capability → routers
        for router in cap.get("routers", []):
            edges.append(
                {
                    "source": cap_id,
                    "source_type": "capability",
                    "target": router,
                    "target_type": "router",
                    "confidence": 1.0,
                    "evidence": "capability_registry.routers",
                }
            )

        # capability → services
        for service in cap.get("services", []):
            edges.append(
                {
                    "source": cap_id,
                    "source_type": "capability",
                    "target": service,
                    "target_type": "service",
                    "confidence": 1.0,
                    "evidence": "capability_registry.services",
                }
            )

        # capability → repositories
        for repo in cap.get("repositories", []):
            edges.append(
                {
                    "source": cap_id,
                    "source_type": "capability",
                    "target": repo,
                    "target_type": "repository",
                    "confidence": 1.0,
                    "evidence": "capability_registry.repositories",
                }
            )

        # capability → unit tests
        for prop_test in cap.get("property_tests", []):
            if "unit" in prop_test or "tests/unit/" in prop_test:
                edges.append(
                    {
                        "source": cap_id,
                        "source_type": "capability",
                        "target": prop_test,
                        "target_type": "unit_test",
                        "confidence": 0.9,
                        "evidence": "capability_registry.property_tests",
                    }
                )

        # capability → property tests
        for prop_test in cap.get("property_tests", []):
            edges.append(
                {
                    "source": cap_id,
                    "source_type": "capability",
                    "target": prop_test,
                    "target_type": "property_test",
                    "confidence": 0.9,
                    "evidence": "capability_registry.property_tests",
                }
            )

        # capability → contract tests
        for contract in cap.get("contracts", []):
            edges.append(
                {
                    "source": cap_id,
                    "source_type": "capability",
                    "target": contract,
                    "target_type": "contract",
                    "confidence": 0.8,
                    "evidence": "capability_registry.contracts",
                }
            )

        # capability → capability tests (from filesystem discovery)
        if cap_id in cap_tests:
            for test_file in cap_tests[cap_id].get("test_files", []):
                edges.append(
                    {
                        "source": cap_id,
                        "source_type": "capability",
                        "target": test_file,
                        "target_type": "capability_test",
                        "confidence": 0.95,
                        "evidence": "discovery:capability_test",
                    }
                )

        # capability → golden datasets
        for dataset in cap.get("golden_datasets", []):
            edges.append(
                {
                    "source": cap_id,
                    "source_type": "capability",
                    "target": dataset,
                    "target_type": "golden_dataset",
                    "confidence": 0.9,
                    "evidence": "capability_registry.golden_datasets",
                }
            )

        # capability → invariant tests
        for inv in cap.get("invariants", []):
            edges.append(
                {
                    "source": cap_id,
                    "source_type": "capability",
                    "target": inv,
                    "target_type": "invariant_test",
                    "confidence": 0.9,
                    "evidence": "capability_registry.invariants",
                }
            )

        # capability → capability dependencies
        for dep_cap in cap.get("dependencies", []):
            edges.append(
                {
                    "source": cap_id,
                    "source_type": "capability",
                    "target": dep_cap,
                    "target_type": "capability",
                    "confidence": 0.9,
                    "evidence": "capability_registry.dependencies",
                }
            )

    return {"edges": edges, "capabilities": capabilities, "generated_at": None}

def get_capability_dependencies(capability_id: str) -> list[dict[str, Any]]:
    """Get all dependencies for a specific capability."""
    dep_map = discover_dependencies()
    return [
        e
        for e in dep_map.get("edges", [])
        if e.get("source") == capability_id or e.get("target") == capability_id
    ]

def get_transitive_dependencies(
    capability_id: str, dep_map: dict[str, Any] | None = None
) -> set[str]:
    """Get all transitive dependencies for a capability."""
    if dep_map is None:
        dep_map = discover_dependencies()

    visited: set[str] = {capability_id}
    queue: list[str] = [capability_id]

    while queue:
        current = queue.pop(0)
        for edge in dep_map.get("edges", []):
            if edge.get("source") == current and edge.get("target") not in visited:
                visited.add(edge["target"])
                queue.append(edge["target"])
            if edge.get("target") == current and edge.get("source") not in visited:
                visited.add(edge["source"])
                queue.append(edge["source"])

    visited.discard(capability_id)
    return visited

def get_dependents(
    capability_id: str, dep_map: dict[str, Any] | None = None
) -> list[str]:
    """Get all capabilities that depend on the given capability."""
    if dep_map is None:
        dep_map = discover_dependencies()

    dependents: list[str] = []
    for edge in dep_map.get("edges", []):
        if (
            edge.get("target") == capability_id
            and edge.get("source_type") == "capability"
        ):
            dependents.append(edge["source"])
    return dependents
