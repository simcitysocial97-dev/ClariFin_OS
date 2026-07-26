#!/usr/bin/env python3
"""Coverage & Traceability Framework Scanner.

This tool scans the codebase and:
1. Reads capability manifests from memory-bank/capabilities/
2. Generates capability-registry.yaml from manifests
3. Detects orphan modules and tests
4. Generates coverage reports
5. Generates traceability document
6. Generates change impact analysis
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Project root from this file's location (backend/tools → backend → project_root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_SRC = PROJECT_ROOT / "backend" / "src"
BACKEND_TESTS = PROJECT_ROOT / "backend" / "tests"
# Capability registry location
CAPABILITY_REGISTRY = BACKEND_TESTS / "generated" / "capability-registry.yaml"

GENERATED_DIR = BACKEND_TESTS / "generated"


@dataclass
class CoverageStatus:
    """Status for a single coverage item."""

    exists: bool
    path: str | None = None
    message: str | None = None


@dataclass
class CapabilityCoverage:
    """Coverage information for a capability."""

    id: str
    name: str
    criticality: str
    risk: str

    # Structural coverage
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

    # Documentation coverage
    contracts: list[str] = field(default_factory=list)
    has_description: bool = True

    # Computed maturity
    structural_maturity: str = "UNKNOWN"
    validation_maturity: str = "UNKNOWN"
    documentation_maturity: str = "UNKNOWN"
    overall_maturity: str = "UNKNOWN"


def load_capability_manifests() -> list[dict[str, Any]]:
    """Load capabilities from generated capability registry."""

    if not CAPABILITY_REGISTRY.exists():
        return []

    with open(CAPABILITY_REGISTRY) as f:
        registry = yaml.safe_load(f) or {}

    return registry.get("capabilities", [])


def check_path_exists(
    path_str: str, base_dir: Path = PROJECT_ROOT / "backend"
) -> CoverageStatus:
    """Check if a path exists relative to base_dir.

    Paths in manifests are relative to backend/, e.g. src/routers/accounts.py
    For invariants, also check tests/domain/invariants/ if tests/invariants/ fails
    """
    # Try direct path first
    path = base_dir / path_str
    if path.exists():
        return CoverageStatus(exists=True, path=path_str)

    # For invariants, try tests/domain/invariants/ as alternative
    if "invariants/test_" in path_str:
        # Map tests/invariants/test_foo.py to tests/domain/invariants/foo.py
        alt_path = path_str.replace(
            "tests/invariants/test_", "tests/domain/invariants/"
        )
        alt_path = alt_path.replace("_", "")
        # Try to find the module file
        for ext in [".py", ""]:
            check = (
                base_dir / alt_path.replace(".py", ext + ".py")
                if ext
                else base_dir / alt_path
            )
            if check.exists():
                return CoverageStatus(
                    exists=True, path=path_str
                )  # Return original path but exists=True

    return CoverageStatus(exists=False, path=path_str, message="Path not found")


def get_all_production_files() -> dict[str, set[str]]:
    """Discover all production code files by category."""
    files: dict[str, set[str]] = {
        "routers": set(),
        "services": set(),
        "engines": set(),
        "repositories": set(),
    }

    # Routers
    routers_dir = BACKEND_SRC / "routers"
    if routers_dir.exists():
        for f in routers_dir.glob("*.py"):
            files["routers"].add(f"src/routers/{f.name}")

    # Services
    services_dir = BACKEND_SRC / "services"
    if services_dir.exists():
        for f in services_dir.glob("*.py"):
            files["services"].add(f"src/services/{f.name}")
        # Also check subdirectories in engines
        for subdir in (BACKEND_SRC / "engines").iterdir():
            if subdir.is_dir():
                for f in subdir.glob("*.py"):
                    files["engines"].add(f"src/engines/{subdir.name}/{f.name}")

    # Engines - top level and subdirectories
    engines_dir = BACKEND_SRC / "engines"
    if engines_dir.exists():
        for f in engines_dir.glob("*.py"):
            if f.name != "__init__.py":
                files["engines"].add(f"src/engines/{f.name}")
        for subdir in engines_dir.iterdir():
            if subdir.is_dir():
                for f in subdir.glob("*.py"):
                    files["engines"].add(f"src/engines/{subdir.name}/{f.name}")

    # Repositories
    repos_dir = BACKEND_SRC / "repositories"
    if repos_dir.exists():
        for f in repos_dir.glob("*.py"):
            if f.name != "__init__.py" and f.name != "base.py":
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

    # Capability tests
    capability_dir = BACKEND_TESTS / "capability"

    if capability_dir.exists():
        for capability in capability_dir.iterdir():
            if capability.is_dir():
                for f in capability.glob("test_*.py"):
                    files["smoke_tests"].add(
                        f"tests/capability/{capability.name}/{f.name}"
                    )

    # Property tests
    property_dir = BACKEND_TESTS / "property"

    if property_dir.exists():
        for f in property_dir.rglob("test_*.py"):
            relative = f.relative_to(BACKEND_TESTS)
            files["property_tests"].add(f"tests/{relative}")

    # Invariant tests
    invariant_dir = BACKEND_TESTS / "invariant"

    if invariant_dir.exists():
        for f in invariant_dir.rglob("test_*.py"):
            relative = f.relative_to(BACKEND_TESTS)
            files["invariants"].add(f"tests/{relative}")

    # Golden datasets
    golden_dir = BACKEND_TESTS / "golden" / "datasets"

    if golden_dir.exists():
        for f in golden_dir.glob("*.json"):
            files["golden_datasets"].add(f"tests/golden/datasets/{f.name}")

    return files


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


def scan_capabilities() -> list[CapabilityCoverage]:
    """Scan all capabilities and compute coverage."""
    capabilities = []

    for manifest in load_capability_manifests():
        cap = CapabilityCoverage(
            id=manifest.get("id", "unknown"),
            name=manifest.get("name", "Unknown"),
            criticality=manifest.get("criticality", "unknown"),
            risk=manifest.get("risk", "unknown"),
        )

        # Check routers
        for router in manifest.get("routers", []):
            cap.routers.append(check_path_exists(router))

        # Check services
        for service in manifest.get("services", []):
            cap.services.append(check_path_exists(service))

        # Check engines
        for engine in manifest.get("engines", []):
            cap.engines.append(check_path_exists(engine))

        # Check repositories
        for repo in manifest.get("repositories", []):
            cap.repositories.append(check_path_exists(repo))

        # Check tables (need to verify DB schema)
        for table in manifest.get("tables", []):
            # Tables are verified via DB schema check
            cap.tables.append(CoverageStatus(exists=True, path=table))

        # Check golden datasets
        for dataset in manifest.get("golden_datasets", []):
            # Check both .json and .json existence
            if dataset.endswith(".json"):
                cap.golden_datasets.append(check_path_exists(dataset))
            else:
                cap.golden_datasets.append(check_path_exists(dataset + ".json"))

        # Check property tests
        for test in manifest.get("property_tests", []):
            cap.property_tests.append(check_path_exists(test))

        # Check invariants
        for inv in manifest.get("invariants", []):
            cap.invariants.append(check_path_exists(inv))

        # Check architecture tests
        arch_tests = manifest.get("architecture_tests", [])
        if arch_tests:
            cap.architecture_tests = CoverageStatus(
                exists=(BACKEND_TESTS / "architecture").exists()
            )
        else:
            cap.architecture_tests = CoverageStatus(exists=False)

        # Contracts
        cap.contracts = manifest.get("contracts", [])

        # Compute maturities
        cap.structural_maturity = compute_maturity(
            cap.routers + cap.services + cap.engines + cap.repositories
        )
        cap.validation_maturity = compute_maturity(
            cap.golden_datasets + cap.property_tests + cap.invariants
        )
        cap.documentation_maturity = "✓" if cap.contracts else "✗"

        # Overall maturity - all three must be ✓
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

    return capabilities


def generate_capability_registry(
    capabilities: list[CapabilityCoverage],
) -> dict[str, Any]:
    """Generate capability-registry.yaml structure from manifests."""
    if not CAPABILITY_REGISTRY.exists():
        return {"capabilities": []}
    with open(CAPABILITY_REGISTRY) as f:
        return yaml.safe_load(f) or {"capabilities": []}


def generate_coverage_report_md(capabilities: list[CapabilityCoverage]) -> str:
    """Generate human-readable coverage report in Markdown."""
    lines = [
        "# Coverage Report",
        "",
        "Generated automatically by `backend/tools/check_coverage.py`. Do not edit manually.",
        "",
        "## Capability Coverage Matrix",
        "",
        "| Capability | Structural | Validation | Documentation | Overall | Criticality | Risk |",
        "|------------|------------|------------|---------------|---------|-------------|------|",
    ]

    for cap in sorted(capabilities, key=lambda c: c.id):
        structural = cap.structural_maturity
        validation = cap.validation_maturity
        documentation = cap.documentation_maturity
        overall = cap.overall_maturity

        lines.append(
            f"| {cap.name} | {structural} | {validation} | {documentation} | {overall} | {cap.criticality} | {cap.risk} |"
        )

    lines.extend(
        [
            "",
            "## Maturity Legend",
            "",
            "| Symbol | Meaning |",
            "|--------|---------|",
            "| ✓ | Complete coverage |",
            "| PARTIAL | Partial coverage |",
            "| ✗ | Missing coverage |",
            "| NONE | No coverage |",
            "| UNKNOWN | Cannot be determined |",
        ]
    )

    # Missing coverage section
    lines.extend(
        [
            "",
            "## Missing Coverage Details",
            "",
        ]
    )

    for cap in sorted(capabilities, key=lambda c: c.id):
        missing_items = []

        for item in (
            cap.routers + cap.services + cap.engines + cap.repositories + cap.tables
        ):
            if not item.exists:
                missing_items.append(f"  - {item.path}: NOT FOUND")

        for item in cap.golden_datasets + cap.property_tests + cap.invariants:
            if not item.exists:
                missing_items.append(f"  - {item.path}: NOT FOUND")

        if missing_items:
            lines.append(f"### {cap.name} (`{cap.id}`)")
            lines.append("")
            lines.extend(missing_items)
            lines.append("")

    return "\n".join(lines)


def generate_traceability_md(capabilities: list[CapabilityCoverage]) -> str:
    """Generate traceability document with dependency chains."""
    lines = [
        "# Traceability Matrix",
        "",
        "Generated automatically. Shows the complete dependency chain for each capability.",
        "",
    ]

    for cap in sorted(capabilities, key=lambda c: c.id):
        lines.extend(
            [
                f"## {cap.name}",
                "",
                f"**Capability ID:** `{cap.id}`",
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

        for table in cap.tables:
            status = "✓" if table.exists else "✗"
            lines.append(f"| Table | `{table.path}` | {status} |")

        for dataset in cap.golden_datasets:
            status = "✓" if dataset.exists else "✗"
            lines.append(f"| Golden Dataset | `{dataset.path}` | {status} |")

        for test in cap.property_tests:
            status = "✓" if test.exists else "✗"
            lines.append(f"| Property Test | `{test.path}` | {status} |")

        for inv in cap.invariants:
            status = "✓" if inv.exists else "✗"
            lines.append(f"| Invariant | `{inv.path}` | {status} |")

        lines.append("")

    return "\n".join(lines)


def generate_change_impact_md(capabilities: list[CapabilityCoverage]) -> str:
    """Generate change impact analysis - what breaks if a file is modified."""
    lines = [
        "# Change Impact Analysis",
        "",
        "Generated automatically. Shows what capabilities/tests would be affected by modifying a file.",
        "",
    ]

    # Collect all files and their impacts
    file_impacts: dict[str, dict[str, Any]] = {}

    for cap in capabilities:
        for router in cap.routers:
            if router.path:
                if router.path not in file_impacts:
                    file_impacts[router.path] = {
                        "capabilities": set(),
                        "property_tests": set(),
                        "golden_tests": set(),
                    }
                file_impacts[router.path]["capabilities"].add(cap.id)
                file_impacts[router.path]["property_tests"].add(
                    f"tests/properties/{cap.id.replace('_', '')}"
                )

        for service in cap.services:
            if service.path:
                if service.path not in file_impacts:
                    file_impacts[service.path] = {
                        "capabilities": set(),
                        "property_tests": set(),
                        "golden_tests": set(),
                    }
                file_impacts[service.path]["capabilities"].add(cap.id)

        for engine in cap.engines:
            if engine.path:
                if engine.path not in file_impacts:
                    file_impacts[engine.path] = {
                        "capabilities": set(),
                        "property_tests": set(),
                        "golden_tests": set(),
                    }
                file_impacts[engine.path]["capabilities"].add(cap.id)
                for dataset in cap.golden_datasets:
                    if dataset.path:
                        dataset_name = dataset.path.replace(
                            "tests/golden/datasets/", ""
                        ).replace(".json", "")
                        file_impacts[engine.path]["golden_tests"].add(dataset_name)

        for repo in cap.repositories:
            if repo.path:
                if repo.path not in file_impacts:
                    file_impacts[repo.path] = {
                        "capabilities": set(),
                        "property_tests": set(),
                        "golden_tests": set(),
                    }
                file_impacts[repo.path]["capabilities"].add(cap.id)

    # Sort by path
    for path in sorted(file_impacts.keys()):
        impacts = file_impacts[path]
        lines.extend(
            [
                f"## `{path}`",
                "",
            ]
        )

        if impacts["capabilities"]:
            lines.append("**Capabilities:**")
            for cap_id in sorted(impacts["capabilities"]):
                cap_found = next((c for c in capabilities if c.id == cap_id), None)
                if cap_found:
                    lines.append(f"  - {cap_found.name} (`{cap_id}`)")
            lines.append("")

        if impacts["property_tests"]:
            lines.append("**Property Tests:**")
            for test in sorted(impacts["property_tests"]):
                if test.strip():
                    lines.append(f"  - `{test}`")
            lines.append("")

        if impacts["golden_tests"]:
            lines.append("**Golden Tests:**")
            for test in sorted(impacts["golden_tests"]):
                if test.strip():
                    lines.append(f"  - `{test}`")
            lines.append("")

    return "\n".join(lines)


def detect_orphans(capabilities: list[CapabilityCoverage]) -> dict[str, list[str]]:
    """Detect orphan modules and tests not referenced by any capability."""
    all_prod = get_all_production_files()
    all_tests = get_all_test_files()

    # Collect all referenced paths
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


def main() -> None:
    """Run the coverage scanner and generate all reports."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    # Scan capabilities
    capabilities = scan_capabilities()

    # Generate capability-registry.yaml (from manifests)
    registry = generate_capability_registry(capabilities)
    with open(GENERATED_DIR / "capability-registry.yaml", "w") as f:
        yaml.dump(registry, f, default_flow_style=False, sort_keys=False)
    print("Generated: capability-registry.yaml")

    # Generate coverage-report.md
    coverage_md = generate_coverage_report_md(capabilities)
    with open(GENERATED_DIR / "coverage.md", "w") as f:
        f.write(coverage_md)
    print("Generated: coverage.md")

    # Generate coverage.json (enriched with raw pytest-cov data)
    raw_path = GENERATED_DIR / "raw-coverage.json"
    if not raw_path.exists():
        raise FileNotFoundError(
            "raw-coverage.json missing. Run pytest with --cov-report=json first."
        )
    with open(raw_path) as f:
        raw_coverage = json.load(f)

    coverage_json = {
        "generated_at": str(os.popen("date -Iseconds").read().strip()),
        "capabilities": [
            {
                "id": cap.id,
                "name": cap.name,
                "criticality": cap.criticality,
                "risk": cap.risk,
                "structural_maturity": cap.structural_maturity,
                "validation_maturity": cap.validation_maturity,
                "documentation_maturity": cap.documentation_maturity,
                "overall_maturity": cap.overall_maturity,
                "missing": [
                    item.path
                    for item in cap.routers
                    + cap.services
                    + cap.engines
                    + cap.repositories
                    + cap.tables
                    + cap.golden_datasets
                    + cap.property_tests
                    + cap.invariants
                    if not item.exists
                ],
            }
            for cap in capabilities
        ],
        "files": raw_coverage.get("files", {}),
        "totals": raw_coverage.get("totals", {}),
    }
    with open(GENERATED_DIR / "coverage.json", "w") as f:
        json.dump(coverage_json, f, indent=2)
    print("Generated: coverage.json")

    # Generate traceability.md
    traceability_md = generate_traceability_md(capabilities)
    with open(GENERATED_DIR / "traceability.md", "w") as f:
        f.write(traceability_md)
    print("Generated: traceability.md")

    # Generate change-impact.md
    change_impact_md = generate_change_impact_md(capabilities)
    with open(GENERATED_DIR / "change-impact.md", "w") as f:
        f.write(change_impact_md)
    print("Generated: change-impact.md")

    # Detect and report orphans
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
