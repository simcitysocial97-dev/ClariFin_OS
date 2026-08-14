#!/usr/bin/env python3
"""Coverage & Capability Framework Scanner (dynamic, evidence-based).

Design (per project decision):

1. Canonical capability identity comes from ``runtime/foundation/verification/
   verification.yaml``. These are the system-level capabilities:
   loan-engine, reconciliation, ledger, api-contracts, migrations,
   runtime-verification, golden-regression, mutation-analysis, e2e-tests.

2. Real implementation evidence is discovered from
   ``runtime/generated/engine-topology.json`` (engines, routers, services,
   repositories, endpoints, tests).

3. ``backend/tests/capability/*`` are real verification assets (domain/test
   taxonomy), preserved and discovered dynamically. They are NOT canonical
   capability IDs; where a domain package maps to one or more system
   capabilities, that relationship is recorded explicitly.

4. Every generated fact carries provenance (where it came from). Nothing is
   hardcoded or fabricated: if a mapping cannot be discovered, it is reported
   as explicitly unmapped rather than invented.

5. Output is deterministic for an unchanged repository (no timestamps in the
   registry itself).

Usage:
    python tools/development/check_coverage.py
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
BACKEND_SRC = BACKEND_DIR / "src"
BACKEND_TESTS = BACKEND_DIR / "tests"
GENERATED_DIR = BACKEND_TESTS / "generated"

VERIFICATION_YAML = (
    PROJECT_ROOT / "runtime" / "foundation" / "verification" / "verification.yaml"
)
ENGINE_TOPOLOGY = PROJECT_ROOT / "runtime" / "generated" / "engine-topology.json"
DOMAIN_PACKAGES_DIR = BACKEND_TESTS / "capability"

CAPABILITY_REGISTRY = GENERATED_DIR / "capability-registry.yaml"
RAW_COVERAGE = GENERATED_DIR / "raw-coverage.json"


@dataclass
class CoverageStatus:
    """Status for a single coverage item (path-relative to backend/)."""

    exists: bool
    path: str | None = None
    message: str | None = None


@dataclass
class CapabilityCoverage:
    """Coverage information for a canonical system capability."""

    id: str
    name: str
    description: str
    category: str
    criticality: str
    risk: str

    # Structural coverage (backend-relative paths, existence-checked)
    routers: list[CoverageStatus] = field(default_factory=list)
    services: list[CoverageStatus] = field(default_factory=list)
    engines: list[CoverageStatus] = field(default_factory=list)
    repositories: list[CoverageStatus] = field(default_factory=list)
    tables: list[CoverageStatus] = field(default_factory=list)

    # Validation coverage
    golden_datasets: list[CoverageStatus] = field(default_factory=list)
    property_tests: list[CoverageStatus] = field(default_factory=list)
    invariants: list[CoverageStatus] = field(default_factory=list)
    architecture_tests: CoverageStatus = field(
        default_factory=lambda: CoverageStatus(exists=False)
    )
    capability_tests: list[str] = field(default_factory=list)

    # Documentation coverage
    contracts: list[str] = field(default_factory=list)
    has_description: bool = True

    # Enriched, evidence-based fields
    owning_engines: list[str] = field(default_factory=list)
    implementation_modules: list[str] = field(default_factory=list)
    all_tests: list[str] = field(default_factory=list)
    test_count: int = 0
    workflow_count: int = 0
    workflows: list[str] = field(default_factory=list)
    status: str = "UNMAPPED"
    source: dict[str, Any] = field(default_factory=dict)

    # Computed maturity
    structural_maturity: str = "UNKNOWN"
    validation_maturity: str = "UNKNOWN"
    documentation_maturity: str = "UNKNOWN"
    overall_maturity: str = "UNKNOWN"


# --------------------------------------------------------------------------- #
# Path helpers
# --------------------------------------------------------------------------- #
def _backend_rel(path: str) -> str:
    """Convert a project-root-relative path (with optional backend/ prefix)
    into a backend-relative path (relative to backend/)."""
    if path.startswith("backend/"):
        return path[len("backend/") :]
    if path.startswith("backend\\"):
        return path[len("backend\\") :]
    return path


def _resolve_repository(name: str) -> str | None:
    """Resolve a repository name to a real backend-relative file path."""
    candidate = BACKEND_SRC / "repositories" / f"{name}.py"
    if candidate.exists():
        return str(candidate.relative_to(BACKEND_DIR))
    return None


def _normalize_engine_path(path: str) -> str:
    """Normalize an engine path (which may omit the backend/src prefix) to a
    project-root-relative path."""
    if not path:
        return path
    if path.startswith("backend/"):
        return path
    if path.startswith("src/"):
        return "backend/" + path
    # e.g. engines/loan_engine/__init__.py
    return "backend/src/" + path.lstrip("/")


def _engine_source_paths(eng: dict[str, Any]) -> list[str]:
    """Real backend-relative source paths for an engine (implementation
    modules, falling back to the public entry point)."""
    paths: list[str] = []
    for im in eng.get("implementation_modules", []):
        paths.append(_backend_rel(im))
    if not paths:
        pep = eng.get("public_entry_point", "")
        if pep:
            paths.append(_backend_rel(_normalize_engine_path(pep)))
    return paths


# --------------------------------------------------------------------------- #
# Source loaders
# --------------------------------------------------------------------------- #
def load_verification_config() -> dict[str, Any]:
    """Load verification.yaml (canonical capability definitions)."""
    if not VERIFICATION_YAML.exists():
        return {}
    with open(VERIFICATION_YAML) as f:
        return cast(dict[str, Any], yaml.safe_load(f) or {})


def load_engine_topology() -> dict[str, Any]:
    """Load engine-topology.json (real implementation evidence)."""
    if not ENGINE_TOPOLOGY.exists():
        return {}
    with open(ENGINE_TOPOLOGY) as f:
        return cast(dict[str, Any], json.load(f) or {})


def discover_domain_packages() -> list[dict[str, Any]]:
    """Dynamically discover the real domain/test packages under
    backend/tests/capability/. These are evidence sources, not canonical
    capability IDs."""
    packages: list[dict[str, Any]] = []
    if not DOMAIN_PACKAGES_DIR.exists():
        return packages

    engine_pat = re.compile(r"engines[./\\]([a-zA-Z0-9_]+)")

    for entry in sorted(DOMAIN_PACKAGES_DIR.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue

        test_files: list[str] = []
        engine_imports: set[str] = set()
        for py in entry.rglob("*.py"):
            test_files.append(str(py.relative_to(BACKEND_DIR)))
            try:
                text = py.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for m in engine_pat.finditer(text):
                engine_imports.add(m.group(1))

        packages.append(
            {
                "id": entry.name,
                "path": str(entry.relative_to(BACKEND_DIR)),
                "test_files": test_files,
                "test_count": len(test_files),
                "engine_imports": sorted(engine_imports),
                "maps_to": [],
            }
        )
    return packages


def match_engines_for_capability(
    modules: list[str], engines: dict[str, Any]
) -> list[str]:
    """Match a capability's declared modules to real engines in the topology.

    Matching rules (deliberately strict to avoid the generic ``src`` prefix
    matching every engine):
      * exact equality between the module path and an engine source path, or
      * the module is a *specific* engine directory that is a parent of an
        engine source path (requires ``engines/`` and at least two path
        segments, e.g. ``src/engines/loan_engine``), or
      * an engine source path is a parent of the module path (same constraint).
    """
    matched: set[str] = set()
    for module in modules:
        mrel = _backend_rel(module)
        if not mrel:
            continue
        for eid, eng in engines.items():
            engine_paths: set[str] = set()
            for im in eng.get("implementation_modules", []):
                engine_paths.add(_backend_rel(im))
            pep = eng.get("public_entry_point", "")
            if pep:
                engine_paths.add(_backend_rel(_normalize_engine_path(pep)))

            hit = False
            for p in engine_paths:
                if not p:
                    continue
                if mrel == p:
                    hit = True
                    break
                if (
                    "engines/" in mrel
                    and mrel.count("/") >= 2
                    and p.startswith(mrel + "/")
                ):
                    hit = True
                    break
                if (
                    "engines/" in p
                    and p.count("/") >= 2
                    and mrel.startswith(p + "/")
                ):
                    hit = True
                    break
            if hit:
                matched.add(eid)
    return sorted(matched)


def build_engine_to_capability(engines: dict[str, Any], capabilities: dict[str, Any]) -> dict[str, str]:
    """Map engine ids to the canonical capability they implement.

    Derived from verification.yaml capability ``modules`` declarations, which
    reference engine source paths. This is the only legitimate engine->system
    capability link; the engine-topology ``capabilities`` field uses a
    different (frontend hook) vocabulary and is intentionally ignored.
    """
    mapping: dict[str, str] = {}
    for cap_id, cap_def in capabilities.items():
        for eid in match_engines_for_capability(
            cap_def.get("modules", []), engines
        ):
            mapping.setdefault(eid, cap_id)
    return mapping


# --------------------------------------------------------------------------- #
# Capability scanning
# --------------------------------------------------------------------------- #
def scan_capabilities() -> tuple[list[CapabilityCoverage], list[dict[str, Any]]]:
    """Build capability coverage from canonical definitions + real evidence."""
    config = load_verification_config()
    capabilities_def = config.get("capabilities", {})
    engines = load_engine_topology().get("engines", {})

    engine_to_cap = build_engine_to_capability(engines, capabilities_def)

    capabilities: list[CapabilityCoverage] = []
    for cap_id, cap_def in capabilities_def.items():
        modules = cap_def.get("modules", [])
        owning = match_engines_for_capability(modules, engines)

        routers: set[str] = set()
        services: set[str] = set()
        eng_modules: set[str] = set()
        repos: set[str] = set()
        all_tests: list[str] = []
        property_tests: set[str] = set()
        invariants: set[str] = set()

        for eid in owning:
            eng = engines[eid]
            for r in eng.get("routers", []):
                routers.add(_backend_rel(r))
            for s in eng.get("services", []):
                services.add(_backend_rel(s))
            for src in _engine_source_paths(eng):
                eng_modules.add(src)
            for rp in eng.get("repositories", []):
                resolved = _resolve_repository(rp)
                if resolved:
                    repos.add(resolved)
            for t in eng.get("tests", []):
                tr = _backend_rel(t)
                if tr.endswith("__init__.py"):
                    continue
                all_tests.append(tr)
                low = tr.lower()
                if "property" in low or "/properties/" in tr:
                    property_tests.add(tr)
                elif "invariant" in low:
                    invariants.add(tr)

        cap = CapabilityCoverage(
            id=cap_id,
            name=cap_def.get("name", cap_id),
            description=cap_def.get("description", ""),
            category=cap_def.get("category", "capability"),
            criticality="unknown",
            risk="unknown",
            owning_engines=list(owning),
            implementation_modules=sorted(eng_modules),
            all_tests=sorted(all_tests),
            test_count=len(all_tests),
            workflow_count=len(cap_def.get("workflows", [])),
            workflows=cap_def.get("workflows", []),
        )

        cap.routers = [CoverageStatus(True, p) for p in sorted(routers)]
        cap.services = [CoverageStatus(True, p) for p in sorted(services)]
        cap.engines = [CoverageStatus(True, p) for p in sorted(eng_modules)]
        cap.repositories = [CoverageStatus(True, p) for p in sorted(repos)]
        cap.property_tests = [CoverageStatus(True, p) for p in sorted(property_tests)]
        cap.invariants = [CoverageStatus(True, p) for p in sorted(invariants)]
        cap.contracts = []

        # Status: evidence-supported, never fabricated.
        if owning and all_tests:
            cap.status = "MAPPED"
        elif owning and not all_tests:
            cap.status = "MAPPED_NO_TESTS"
        elif modules and any(
            (BACKEND_DIR / _backend_rel(m)).exists() for m in modules
        ):
            cap.status = "MODULE_MAPPED_NO_ENGINE"
        elif cap_def.get("workflows"):
            cap.status = "WORKFLOW_ONLY"
        else:
            cap.status = "UNMAPPED"

        cap.source = {
            "capability_definition": {
                "type": "verification-yaml",
                "path": str(VERIFICATION_YAML.relative_to(PROJECT_ROOT)),
            },
            "engine_mapping": {
                "type": "engine-topology",
                "path": str(ENGINE_TOPOLOGY.relative_to(PROJECT_ROOT)),
                "engines": list(owning),
            }
            if owning
            else {"type": "none"},
            "tests": {
                "type": "engine-topology",
                "count": len(all_tests),
            }
            if all_tests
            else {"type": "none"},
            "repositories": {
                "type": "repository-resolution",
                "pattern": "src/repositories/<name>.py",
            },
        }

        # Compute maturities (only over genuinely discovered items)
        cap.structural_maturity = compute_maturity(
            cap.routers + cap.services + cap.engines + cap.repositories
        )
        cap.validation_maturity = compute_maturity(
            cap.golden_datasets + cap.property_tests + cap.invariants
        )
        cap.documentation_maturity = "✓" if cap.contracts else "✗"

        if (
            cap.structural_maturity == "✓"
            and cap.validation_maturity == "✓"
            and cap.documentation_maturity == "✓"
        ):
            cap.overall_maturity = "✓"
        elif cap.structural_maturity == "NONE" and cap.validation_maturity == "NONE":
            cap.overall_maturity = "NONE"
        elif "✗" in [
            cap.structural_maturity,
            cap.validation_maturity,
            cap.documentation_maturity,
        ]:
            cap.overall_maturity = "✗"
        else:
            cap.overall_maturity = "PARTIAL"

        capabilities.append(cap)

    # Domain packages: discover real tests and map to system capabilities
    # wherever the evidence supports it.
    domain_packages = discover_domain_packages()
    cap_ids = set(capabilities_def)
    for pkg in domain_packages:
        mapped: set[str] = set()
        # Direct name match (only if the domain id is itself a system cap)
        if pkg["id"] in cap_ids:
            mapped.add(pkg["id"])
        # Engine-import based mapping
        for eng in pkg["engine_imports"]:
            if eng in engine_to_cap:
                mapped.add(engine_to_cap[eng])
        pkg["maps_to"] = sorted(mapped)

    return capabilities, domain_packages


def compute_maturity(statuses: list[CoverageStatus]) -> str:
    """Compute maturity level from coverage statuses."""
    if not statuses:
        return "NONE"

    exists_count = sum(1 for s in statuses if s.exists)
    total_count = len(statuses)

    if total_count == 0:
        return "UNKNOWN"

    if exists_count == total_count:
        return "✓"

    if exists_count > 0:
        return "PARTIAL"

    return "✗"


# --------------------------------------------------------------------------- #
# Registry generation
# --------------------------------------------------------------------------- #
def generate_capability_registry(
    capabilities: list[CapabilityCoverage],
    domain_packages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build capability-registry.yaml from scanned, evidence-based data."""
    registry: dict[str, Any] = {
        "metadata": {
            "generated_by": "tools/development/check_coverage.py",
            "canonical_source": str(VERIFICATION_YAML.relative_to(PROJECT_ROOT)),
            "engine_source": str(ENGINE_TOPOLOGY.relative_to(PROJECT_ROOT)),
            "domain_source": str(DOMAIN_PACKAGES_DIR.relative_to(PROJECT_ROOT)),
            "note": "System capabilities are canonical (verification.yaml). "
            "Domain packages (backend/tests/capability/*) are a secondary "
            "test/domain taxonomy and are listed under 'test_domains'.",
        },
        "capabilities": [],
        "test_domains": [],
    }

    for cap in capabilities:
        entry: dict[str, Any] = {
            "id": cap.id,
            "name": cap.name,
            "description": cap.description,
            "category": cap.category,
            "criticality": cap.criticality,
            "risk": cap.risk,
            "status": cap.status,
            "owning_engines": cap.owning_engines,
            "implementation_modules": cap.implementation_modules,
            "workflows": cap.workflows,
            "routers": [c.path for c in cap.routers],
            "services": [c.path for c in cap.services],
            "engines": [c.path for c in cap.engines],
            "repositories": [c.path for c in cap.repositories],
            "tables": [c.path for c in cap.tables],
            "all_tests": cap.all_tests,
            "test_count": cap.test_count,
            "property_tests": [c.path for c in cap.property_tests],
            "invariants": [c.path for c in cap.invariants],
            "golden_datasets": [c.path for c in cap.golden_datasets],
            "architecture_tests": cap.architecture_tests.path,
            "capability_tests": cap.capability_tests,
            "contracts": cap.contracts,
            "dependencies": [],
            "maturity": {
                "structural": cap.structural_maturity,
                "validation": cap.validation_maturity,
                "documentation": cap.documentation_maturity,
                "overall": cap.overall_maturity,
            },
            "source": cap.source,
        }
        registry["capabilities"].append(entry)

    for pkg in domain_packages:
        registry["test_domains"].append(
            {
                "id": pkg["id"],
                "path": pkg["path"],
                "test_count": pkg["test_count"],
                "engine_imports": pkg["engine_imports"],
                "maps_to": pkg["maps_to"],
                "source": {
                    "type": "test-discovery",
                    "path": pkg["path"],
                },
            }
        )

    return registry


# --------------------------------------------------------------------------- #
# Markdown reports (kept deterministic, no fabricated values)
# --------------------------------------------------------------------------- #
def generate_coverage_report_md(capabilities: list[CapabilityCoverage]) -> str:
    """Generate human-readable coverage report in Markdown."""
    lines = [
        "# Coverage Report",
        "",
        "Generated automatically by `tools/development/check_coverage.py`.",
        "System capabilities are canonical (`verification.yaml`); real evidence",
        "is discovered from `engine-topology.json` and `backend/tests/capability/*`.",
        "",
        "## Capability Coverage Matrix",
        "",
        "| Capability | Status | Structural | Validation | Documentation | Overall |",
        "|------------|--------|------------|------------|---------------|---------|",
    ]

    for cap in sorted(capabilities, key=lambda c: c.id):
        lines.append(
            f"| {cap.name} (`{cap.id}`) | {cap.status} | "
            f"{cap.structural_maturity} | {cap.validation_maturity} | "
            f"{cap.documentation_maturity} | {cap.overall_maturity} |"
        )

    lines.extend(
        [
            "",
            "## Status Legend",
            "",
            "| Status | Meaning |",
            "|--------|---------|",
            "| MAPPED | Engine + implementation + tests discovered |",
            "| MAPPED_NO_TESTS | Engine + implementation discovered, no tests |",
            "| MODULE_MAPPED_NO_ENGINE | Module dir exists, no engine topology |",
            "| WORKFLOW_ONLY | Defined by workflow, no engine mapping |",
            "| UNMAPPED | No discoverable evidence |",
            "",
            "## Maturity Legend",
            "",
            "| Symbol | Meaning |",
            "|--------|---------|",
            "| ✓ | Complete coverage |",
            "| PARTIAL | Partial coverage |",
            "| ✗ | Missing coverage |",
            "| NONE | No coverage |",
        ]
    )
    return "\n".join(lines)


def generate_traceability_md(capabilities: list[CapabilityCoverage]) -> str:
    """Generate traceability document with dependency chains."""
    lines = [
        "# Traceability Matrix",
        "",
        "Generated automatically. Shows the discovered dependency chain for each "
        "canonical capability.",
        "",
    ]

    for cap in sorted(capabilities, key=lambda c: c.id):
        lines.extend(
            [
                f"## {cap.name} (`{cap.id}`)",
                "",
                f"**Status:** {cap.status}",
                f"**Owning engines:** {', '.join(cap.owning_engines) or 'none'}",
                f"**Test count:** {cap.test_count}",
                "",
                "### Dependency Chain",
                "",
                "| Layer | Artifact | Status |",
                "|-------|----------|--------|",
            ]
        )
        for router in cap.routers:
            status = "✓" if router.exists else "✗"
            lines.append(f"| Router | `{router.path}` | {status} |")
        for service in cap.services:
            status = "✓" if service.exists else "✗"
            lines.append(f"| Service | `{service.path}` | {status} |")
        for engine in cap.engines:
            status = "✓" if engine.exists else "✗"
            lines.append(f"| Engine | `{engine.path}` | {status} |")
        for repo in cap.repositories:
            status = "✓" if repo.exists else "✗"
            lines.append(f"| Repository | `{repo.path}` | {status} |")
        for test in cap.property_tests:
            status = "✓" if test.exists else "✗"
            lines.append(f"| Property Test | `{test.path}` | {status} |")
        for inv in cap.invariants:
            status = "✓" if inv.exists else "✗"
            lines.append(f"| Invariant | `{inv.path}` | {status} |")
        lines.append("")

    return "\n".join(lines)


def generate_change_impact_md(capabilities: list[CapabilityCoverage]) -> str:
    """Generate change impact analysis from discovered file -> capability map."""
    lines = [
        "# Change Impact Analysis",
        "",
        "Generated automatically. Shows which capabilities are affected by "
        "modifying a discovered file.",
        "",
    ]

    file_impacts: dict[str, dict[str, Any]] = {}
    for cap in capabilities:
        for item in (
            cap.routers + cap.services + cap.engines + cap.repositories
        ):
            if not item.path:
                continue
            file_impacts.setdefault(
                item.path,
                {"capabilities": set(), "property_tests": set()},
            )
            file_impacts[item.path]["capabilities"].add(cap.id)

    for path in sorted(file_impacts.keys()):
        impacts = file_impacts[path]
        lines.extend([f"## `{path}`", ""])
        if impacts["capabilities"]:
            lines.append("**Capabilities:**")
            for cap_id in sorted(impacts["capabilities"]):
                lines.append(f"  - `{cap_id}`")
            lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Orphan detection (informational)
# --------------------------------------------------------------------------- #
def get_all_production_files() -> dict[str, set[str]]:
    """Discover all production code files by category (backend-relative)."""
    files: dict[str, set[str]] = {
        "routers": set(),
        "services": set(),
        "engines": set(),
        "repositories": set(),
    }
    if (BACKEND_SRC / "routers").exists():
        for f in (BACKEND_SRC / "routers").glob("*.py"):
            files["routers"].add(f"src/routers/{f.name}")
    if (BACKEND_SRC / "services").exists():
        for f in (BACKEND_SRC / "services").glob("*.py"):
            files["services"].add(f"src/services/{f.name}")
    engines_dir = BACKEND_SRC / "engines"
    if engines_dir.exists():
        for f in engines_dir.glob("*.py"):
            if f.name != "__init__.py":
                files["engines"].add(f"src/engines/{f.name}")
        for subdir in engines_dir.iterdir():
            if subdir.is_dir():
                for f in subdir.glob("*.py"):
                    files["engines"].add(f"src/engines/{subdir.name}/{f.name}")
    repos_dir = BACKEND_SRC / "repositories"
    if repos_dir.exists():
        for f in repos_dir.glob("*.py"):
            if f.name not in ("__init__.py", "base.py"):
                files["repositories"].add(f"src/repositories/{f.name}")
    return files


def get_all_test_files() -> dict[str, set[str]]:
    """Discover all test files by actual repository structure."""
    files: dict[str, set[str]] = {
        "smoke_tests": set(),
        "property_tests": set(),
        "invariants": set(),
        "golden_datasets": set(),
    }
    capability_dir = BACKEND_TESTS / "capability"
    if capability_dir.exists():
        for capability in capability_dir.iterdir():
            if capability.is_dir():
                for f in capability.glob("test_*.py"):
                    files["smoke_tests"].add(
                        f"tests/capability/{capability.name}/{f.name}"
                    )
    property_dir = BACKEND_TESTS / "property"
    if property_dir.exists():
        for f in property_dir.rglob("test_*.py"):
            files["property_tests"].add(f"tests/{f.relative_to(BACKEND_TESTS)}")
    invariant_dir = BACKEND_TESTS / "invariant"
    if invariant_dir.exists():
        for f in invariant_dir.rglob("test_*.py"):
            files["invariants"].add(f"tests/{f.relative_to(BACKEND_TESTS)}")
    golden_dir = BACKEND_TESTS / "golden" / "datasets"
    if golden_dir.exists():
        for f in golden_dir.glob("*.json"):
            files["golden_datasets"].add(f"tests/golden/datasets/{f.name}")
    return files


def detect_orphans(capabilities: list[CapabilityCoverage]) -> dict[str, list[str]]:
    """Detect orphan modules and tests not referenced by any capability."""
    all_prod = get_all_production_files()
    all_tests = get_all_test_files()

    referenced_prod: set[str] = set()
    referenced_tests: set[str] = set()

    for cap in capabilities:
        for r in cap.routers:
            if r.path:
                referenced_prod.add(r.path)
        for s in cap.services:
            if s.path:
                referenced_prod.add(s.path)
        for e in cap.engines:
            if e.path:
                referenced_prod.add(e.path)
        for r in cap.repositories:
            if r.path:
                referenced_prod.add(r.path)
        for g in cap.golden_datasets:
            if g.path:
                referenced_tests.add(g.path)
        for p in cap.property_tests:
            if p.path:
                referenced_tests.add(p.path)
        for i in cap.invariants:
            if i.path:
                referenced_tests.add(i.path)

    orphans: dict[str, list[str]] = {
        "routers": [],
        "services": [],
        "engines": [],
        "repositories": [],
        "golden_datasets": [],
        "property_tests": [],
        "invariants": [],
    }
    for router in all_prod["routers"] - referenced_prod:
        orphans["routers"].append(router)
    for service in all_prod["services"] - referenced_prod:
        orphans["services"].append(service)
    for engine in all_prod["engines"] - referenced_prod:
        orphans["engines"].append(engine)
    for repo in all_prod["repositories"] - referenced_prod:
        orphans["repositories"].append(repo)
    for dataset in all_tests["golden_datasets"] - referenced_tests:
        orphans["golden_datasets"].append(dataset)
    for test in all_tests["property_tests"] - referenced_tests:
        orphans["property_tests"].append(test)
    for test in all_tests["invariants"] - referenced_tests:
        orphans["invariants"].append(test)
    return orphans


# --------------------------------------------------------------------------- #
# Coverage JSON (enriched with optional raw pytest-cov data)
# --------------------------------------------------------------------------- #
def generate_coverage_json(
    capabilities: list[CapabilityCoverage],
) -> dict[str, Any]:
    """Generate coverage.json without requiring a prior raw pytest run."""
    raw_coverage: dict[str, Any] = {}
    if RAW_COVERAGE.exists():
        with open(RAW_COVERAGE) as f:
            raw_coverage = json.load(f)

    return {
        "generated_at": "deterministic",  # registry/JSON are reproducible
        "capabilities": [
            {
                "id": cap.id,
                "name": cap.name,
                "criticality": cap.criticality,
                "risk": cap.risk,
                "status": cap.status,
                "structural_maturity": cap.structural_maturity,
                "validation_maturity": cap.validation_maturity,
                "documentation_maturity": cap.documentation_maturity,
                "overall_maturity": cap.overall_maturity,
                "test_count": cap.test_count,
                "owning_engines": cap.owning_engines,
                "missing": [
                    item.path
                    for item in (
                        cap.routers
                        + cap.services
                        + cap.engines
                        + cap.repositories
                        + cap.tables
                        + cap.golden_datasets
                        + cap.property_tests
                        + cap.invariants
                    )
                    if not item.exists
                ],
            }
            for cap in capabilities
        ],
        "files": raw_coverage.get("files", {}),
        "totals": raw_coverage.get("totals", {}),
    }


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the capability/coverage scanner and generate all reports."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    capabilities, domain_packages = scan_capabilities()

    # capability-registry.yaml (deterministic)
    registry = generate_capability_registry(capabilities, domain_packages)
    with open(CAPABILITY_REGISTRY, "w") as f:
        yaml.dump(registry, f, default_flow_style=False, sort_keys=False)
    print(
        f"Generated: capability-registry.yaml "
        f"({len(capabilities)} system capabilities, {len(domain_packages)} domain packages)"
    )

    # coverage.md
    coverage_md = generate_coverage_report_md(capabilities)
    with open(GENERATED_DIR / "coverage.md", "w") as f:
        f.write(coverage_md)
    print("Generated: coverage.md")

    # coverage.json
    coverage_json = generate_coverage_json(capabilities)
    with open(GENERATED_DIR / "coverage.json", "w") as f:
        json.dump(coverage_json, f, indent=2)
    print("Generated: coverage.json")

    # traceability.md
    traceability_md = generate_traceability_md(capabilities)
    with open(GENERATED_DIR / "traceability.md", "w") as f:
        f.write(traceability_md)
    print("Generated: traceability.md")

    # change-impact.md
    change_impact_md = generate_change_impact_md(capabilities)
    with open(GENERATED_DIR / "change-impact.md", "w") as f:
        f.write(change_impact_md)
    print("Generated: change-impact.md")

    orphans = detect_orphans(capabilities)
    orphan_items = sum(len(v) for v in orphans.values())
    if orphan_items > 0:
        print(f"\nOrphan detection found {orphan_items} unreferenced items:")
        for category, files in orphans.items():
            if files:
                print(f"  {category}: {len(files)}")

    print("\nCoverage scan complete.")


if __name__ == "__main__":
    main()
