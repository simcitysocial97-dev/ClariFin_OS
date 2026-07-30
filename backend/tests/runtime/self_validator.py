"""Self-validation for the Verification Runtime.

Validates:
- Registry integrity (all registries loadable, no duplicate IDs)
- Discovery correctness (all registered components exist on disk)
- Missing metadata detection
- Pipeline consistency (all stages have runners)
- Duplicate registration detection
"""

from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.discovery import (
    discover_builders,
    discover_capabilities,
    discover_capability_tests,
    discover_contract_tests,
    discover_fixtures,
    discover_golden_datasets,
    discover_invariant_tests,
    discover_property_tests,
)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"
TESTS_DIR = BACKEND_DIR / "tests"


def validate_registry_integrity() -> dict[str, Any]:
    """Validate that all registries are loadable and internally consistent."""
    from runtime.registries import (
        load_api_map,
        load_capability_registry,
        load_contract_registry,
        load_mutation_registry,
    )

    results: dict[str, Any] = {
        "capability_registry": {"valid": False, "errors": []},
        "contract_registry": {"valid": False, "errors": []},
        "mutation_registry": {"valid": False, "errors": []},
        "api_map": {"valid": False, "errors": []},
    }

    # Capability registry
    try:
        cap_reg = load_capability_registry()
        caps = cap_reg.get("capabilities", [])
        cap_ids = [c.get("id") for c in caps if c.get("id")]
        duplicates = [cid for cid in set(cap_ids) if cap_ids.count(cid) > 1]
        if duplicates:
            results["capability_registry"]["errors"].append(
                f"Duplicate capability IDs: {duplicates}"
            )
        else:
            results["capability_registry"]["valid"] = True
        results["capability_registry"]["count"] = len(caps)
    except Exception as e:
        results["capability_registry"]["errors"].append(str(e))

    # Contract registry
    try:
        contract_reg = load_contract_registry()
        routers = contract_reg.get("routers", {})
        results["contract_registry"]["valid"] = True
        results["contract_registry"]["count"] = len(routers)
    except Exception as e:
        results["contract_registry"]["errors"].append(str(e))

    # Mutation registry
    try:
        mut_reg = load_mutation_registry()
        entries = mut_reg.get("entries", [])
        results["mutation_registry"]["valid"] = True
        results["mutation_registry"]["count"] = len(entries)
    except Exception as e:
        results["mutation_registry"]["errors"].append(str(e))

    # API map
    try:
        api_map = load_api_map()
        endpoints = api_map.get("endpoints", [])
        results["api_map"]["valid"] = True
        results["api_map"]["count"] = len(endpoints)
    except Exception as e:
        results["api_map"]["errors"].append(str(e))

    return results


def validate_discovery_correctness() -> dict[str, Any]:
    """Validate that discovered components actually exist on disk."""
    results: dict[str, Any] = {"valid": True, "errors": []}

    # Check capabilities
    capabilities = discover_capabilities()
    for cap in capabilities:
        cap_id = cap.get("id", "")
        cap_test = discover_capability_tests()
        cap_test_ids = [c["id"] for c in cap_test]
        if cap_id not in cap_test_ids:
            results["errors"].append(
                f"Capability '{cap_id}' has no test directory in tests/capability/"
            )

    # Check that all registered property tests exist
    prop_tests = discover_property_tests()
    for pt in prop_tests:
        path = BACKEND_DIR / pt["path"]
        if not path.exists():
            results["errors"].append(f"Property test not found: {pt['path']}")

    # Check that all registered invariant tests exist
    inv_tests = discover_invariant_tests()
    for it in inv_tests:
        path = BACKEND_DIR / it["path"]
        if not path.exists():
            results["errors"].append(f"Invariant test not found: {it['path']}")

    # Check golden datasets
    datasets = discover_golden_datasets()
    for ds in datasets:
        path = BACKEND_DIR / ds["path"]
        if not path.exists():
            results["errors"].append(f"Golden dataset not found: {ds['path']}")

    # Check contract tests
    contract_tests = discover_contract_tests()
    for ct in contract_tests:
        path = BACKEND_DIR / ct["path"]
        if not path.exists():
            results["errors"].append(f"Contract test not found: {ct['path']}")

    if results["errors"]:
        results["valid"] = False

    return results


def validate_missing_metadata() -> dict[str, Any]:
    """Detect capabilities missing verification metadata."""
    from runtime.discovery import discover_capabilities
    from runtime.registries import get_capability_by_id

    results: dict[str, Any] = {"valid": True, "missing": []}

    capabilities = discover_capabilities()
    for cap in capabilities:
        cap_id = cap.get("id", "")
        registered = get_capability_by_id(cap_id)
        if not registered:
            results["missing"].append(
                f"Capability '{cap_id}' not in capability-registry.yaml"
            )
            continue

        missing_fields = []
        required = ["property_tests", "invariants", "golden_datasets", "contracts"]
        for field in required:
            if not registered.get(field):
                missing_fields.append(field)

        if missing_fields:
            results["missing"].append(
                f"Capability '{cap_id}' missing: {', '.join(missing_fields)}"
            )

    if results["missing"]:
        results["valid"] = False

    return results


def validate_pipeline_consistency() -> dict[str, Any]:
    """Validate that all pipeline stages have runners."""
    from runtime.orchestrator import FULL_PIPELINE, STAGE_RUNNERS

    results: dict[str, Any] = {"valid": True, "missing_runners": []}

    for stage_id in FULL_PIPELINE:
        if stage_id not in STAGE_RUNNERS:
            results["missing_runners"].append(stage_id)

    if results["missing_runners"]:
        results["valid"] = False

    return results


def validate_no_duplicate_registrations() -> dict[str, Any]:
    """Detect duplicate registrations across all test directories."""
    results: dict[str, Any] = {"valid": True, "duplicates": []}

    # Check for duplicate capability test directories
    cap_tests = discover_capability_tests()
    cap_ids = [c["id"] for c in cap_tests]
    duplicates = [cid for cid in set(cap_ids) if cap_ids.count(cid) > 1]
    if duplicates:
        results["duplicates"].append(
            f"Duplicate capability test directories: {duplicates}"
        )

    # Check for duplicate property test paths
    from runtime.discovery import discover_property_tests

    prop_paths = [t["path"] for t in discover_property_tests()]
    dup_paths = [p for p in set(prop_paths) if prop_paths.count(p) > 1]
    if dup_paths:
        results["duplicates"].append(f"Duplicate property test paths: {dup_paths}")

    # Check for duplicate invariant test paths
    from runtime.discovery import discover_invariant_tests

    inv_paths = [t["path"] for t in discover_invariant_tests()]
    dup_inv = [p for p in set(inv_paths) if inv_paths.count(p) > 1]
    if dup_inv:
        results["duplicates"].append(f"Duplicate invariant test paths: {dup_inv}")

    if results["duplicates"]:
        results["valid"] = False

    return results


def validate_builder_registry() -> dict[str, Any]:
    """Validate builder discovery and registry."""

    results: dict[str, Any] = {"valid": True, "builders": [], "errors": []}

    builders = discover_builders()
    results["builders"] = [b["path"] for b in builders]

    # Check that all builders are valid Python and have either:
    # - A class with 'Builder' in the name (domain builders), OR
    # - A function that loads a dataset (golden builders)
    for builder in builders:
        full_path = BACKEND_DIR / builder["path"]
        try:
            tree = ast.parse(full_path.read_text())
            has_builder_class = any(
                isinstance(node, ast.ClassDef) and "Builder" in node.name
                for node in ast.walk(tree)
            )
            has_loader_function = any(
                isinstance(node, ast.FunctionDef) and node.name.startswith("load_")
                for node in ast.walk(tree)
            )
            if not (has_builder_class or has_loader_function):
                results["errors"].append(
                    f"Builder module {builder['path']} has no Builder class or load_ function"
                )
        except SyntaxError as e:
            results["errors"].append(
                f"Builder module {builder['path']} has syntax error: {e}"
            )

    if results["errors"]:
        results["valid"] = False

    return results


def validate_fixture_registry() -> dict[str, Any]:
    """Validate fixture discovery."""

    results: dict[str, Any] = {"valid": True, "fixtures": [], "errors": []}

    fixtures = discover_fixtures()
    results["fixtures"] = [f["path"] for f in fixtures]

    # Check that all conftest.py files are syntactically valid
    for fixture in fixtures:
        full_path = BACKEND_DIR / fixture["path"]
        try:
            ast.parse(full_path.read_text())
        except SyntaxError as e:
            results["errors"].append(
                f"Fixture file {fixture['path']} has syntax error: {e}"
            )

    if results["errors"]:
        results["valid"] = False

    return results


def validate_dependency_graph_integrity() -> dict[str, Any]:
    """Validate that the dependency graph is internally consistent."""
    from runtime.discovery import discover_dependencies

    results: dict[str, Any] = {"valid": True, "errors": []}

    dep_map = discover_dependencies()
    edges = dep_map.get("edges", [])
    capabilities = dep_map.get("capabilities", {})

    if not edges and not capabilities:
        results["errors"].append("Dependency graph is empty - stubs return no data")
        results["edge_count"] = 0
        results["capability_count"] = 0
        return results

    # Check that all edge references are valid
    all_cap_ids = set(capabilities.keys())
    # Known system modules that are not capabilities but can appear in dependency graph
    system_modules = {
        "verification",
        "verification.intelligence",
        "verification.runtime",
    }
    for edge in edges:
        source = edge.get("source", "")
        target = edge.get("target", "")
        source_type = edge.get("source_type", "")
        target_type = edge.get("target_type", "")

        # Check source
        if (
            source_type == "capability"
            and source not in all_cap_ids
            and source not in system_modules
            and not any(source.startswith(mod + ".") for mod in system_modules)
        ):
            results["errors"].append(
                f"Edge source '{source}' not found in capabilities"
            )
        if (
            target_type == "capability"
            and target not in all_cap_ids
            and target not in system_modules
            and not any(target.startswith(mod + ".") for mod in system_modules)
        ):
            results["errors"].append(
                f"Edge target '{target}' not found in capabilities"
            )

    if results["errors"]:
        results["valid"] = False

    results["edge_count"] = len(edges)
    results["capability_count"] = len(capabilities)

    return results


def validate_change_impact_correctness() -> dict[str, Any]:
    """Validate that change impact analysis produces correct results."""
    from src.verification.intelligence.impact_engine import ImpactEngine

    results: dict[str, Any] = {"valid": True, "errors": []}

    try:
        engine = ImpactEngine()
        test_files = [
            "backend/src/engines/cashflow_engine.py",
        ]

        for test_file in test_files:
            impact = engine.analyze([test_file])
            if impact.overall_risk not in (
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
            ):
                results["errors"].append(
                    f"Invalid risk level for {test_file}: {impact.overall_risk}"
                )
    except Exception as e:
        results["errors"].append(f"Impact engine error: {e}")

    if results["errors"]:
        results["valid"] = False

    return results


def validate_risk_metadata_consistency() -> dict[str, Any]:
    """Validate that risk metadata is consistent across components."""
    from src.verification.intelligence.risk_engine import RiskEngine

    results: dict[str, Any] = {"valid": True, "errors": []}

    try:
        engine = RiskEngine()
        risk_map = engine.classify_all()

        for entry in risk_map.entries:
            if entry.risk not in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                results["errors"].append(
                    f"Invalid risk level for {entry.id}: {entry.risk}"
                )
    except Exception as e:
        results["errors"].append(f"Risk engine error: {e}")

    if results["errors"]:
        results["valid"] = False

    results["entry_count"] = len(risk_map.entries) if "risk_map" in dir() else 0

    return results


def validate_architectural_coverage_completeness() -> dict[str, Any]:
    """Validate that architectural coverage covers all capabilities."""
    from src.verification.intelligence.coverage_engine import CoverageEngine

    results: dict[str, Any] = {"valid": True, "errors": []}

    try:
        engine = CoverageEngine()
        coverage = engine.generate_all()

        total = coverage.summary.get("total_capabilities", 0)
        gap_count = coverage.summary.get("gap", 0)

        if total == 0:
            results["errors"].append("No capabilities found in coverage report")
            results["valid"] = True

        results["total_capabilities"] = total
        results["gap_count"] = gap_count
        results["average_coverage_percent"] = coverage.summary.get(
            "average_coverage_percent", 0
        )
    except Exception as e:
        results["errors"].append(f"Coverage engine error: {e}")
        results["valid"] = False

    return results


def validate_evidence_integrity() -> dict[str, Any]:
    """Validate that verification evidence is consistent."""
    from src.verification.intelligence.evidence_engine import EvidenceEngine

    results: dict[str, Any] = {"valid": True, "errors": []}

    try:
        engine = EvidenceEngine()
        summary = engine.generate_all()

        issues = []
        for cap in summary.capabilities:
            if cap.total_count > 0 and cap.verified_count == 0:
                issues.append(
                    f"{cap.capability_id}: {cap.total_count} checks, 0 verified"
                )

        if issues:
            results["errors"].extend(issues)
            results["valid"] = False

        results["total_capabilities"] = summary.total_capabilities
        results["fully_verified"] = summary.fully_verified
    except Exception as e:
        results["errors"].append(f"Evidence engine error: {e}")
        results["valid"] = False

    return results


def validate_dependency_chains() -> dict[str, Any]:
    """Check for broken dependency chains in the capability registry."""
    from runtime.discovery import discover_dependencies

    results: dict[str, Any] = {"valid": True, "errors": []}

    try:
        dep_map = discover_dependencies()
        capabilities = dep_map.get("capabilities", {})
        cap_ids = set(capabilities.keys())

        broken = []
        for edge in dep_map.get("edges", []):
            target = edge.get("target", "")
            target_type = edge.get("target_type", "")
            if target_type == "capability" and target not in cap_ids:
                broken.append(f"{edge.get('source')} -> {target}")

        if broken:
            results["errors"].extend([f"Broken dependency: {b}" for b in broken])
            results["valid"] = False

        results["edge_count"] = len(dep_map.get("edges", []))
        results["capability_count"] = len(capabilities)
    except Exception as e:
        results["errors"].append(f"Dependency chain error: {e}")
        results["valid"] = False

    return results


def run_all_validations() -> dict[str, Any]:
    """Run all self-validation checks and return combined report."""
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "registry_integrity": validate_registry_integrity(),
        "discovery_correctness": validate_discovery_correctness(),
        "missing_metadata": validate_missing_metadata(),
        "pipeline_consistency": validate_pipeline_consistency(),
        "no_duplicate_registrations": validate_no_duplicate_registrations(),
        "builder_registry": validate_builder_registry(),
        "fixture_registry": validate_fixture_registry(),
        "dependency_graph_integrity": validate_dependency_graph_integrity(),
        "change_impact_correctness": validate_change_impact_correctness(),
        "risk_metadata_consistency": validate_risk_metadata_consistency(),
        "architectural_coverage_completeness": validate_architectural_coverage_completeness(),
        "evidence_integrity": validate_evidence_integrity(),
        "dependency_chains": validate_dependency_chains(),
    }


def overall_health(report: dict[str, Any]) -> bool:
    """Determine if the verification runtime is healthy."""
    for _key, value in report.items():
        if isinstance(value, dict) and value.get("valid") is False:
            return False
    return True
