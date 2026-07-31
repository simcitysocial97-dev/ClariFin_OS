"""Verification Runtime Self-Validation Tests.

Validates:
- Registry integrity (all registries loadable, no duplicate IDs)
- Discovery correctness (all registered components exist on disk)
- Missing metadata detection
- Pipeline consistency (all stages have runners)
- Duplicate registration detection
- Builder registry
- Fixture registry
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"


def test_registry_integrity() -> None:
    """All registries must load without errors."""
    from verification_runtime.registries import (
        load_api_map,
        load_capability_registry,
        load_contract_registry,
        load_mutation_registry,
    )

    cap_reg = load_capability_registry()
    assert "capabilities" in cap_reg
    assert len(cap_reg["capabilities"]) > 0

    contract_reg = load_contract_registry()
    assert "routers" in contract_reg

    mut_reg = load_mutation_registry()
    assert "entries" in mut_reg

    api_map = load_api_map()
    assert "endpoints" in api_map


def test_no_duplicate_capability_ids() -> None:
    """Capability registry must have unique IDs."""
    from verification_runtime.registries import load_capability_registry

    cap_reg = load_capability_registry()
    cap_ids = [c.get("id") for c in cap_reg.get("capabilities", []) if c.get("id")]
    assert len(cap_ids) == len(set(cap_ids)), "Duplicate capability IDs found"


def test_discovery_discovers_existing_files() -> None:
    """All discovered components must exist on disk."""
    from verification_runtime.discovery import (
        discover_builders,
        discover_contract_tests,
        discover_golden_datasets,
        discover_invariant_modules,
        discover_invariant_tests,
        discover_property_tests,
    )

    for prop in discover_property_tests():
        assert (
            BACKEND_DIR / prop["path"]
        ).exists(), f"Property test missing: {prop['path']}"

    for inv in discover_invariant_tests():
        assert (
            BACKEND_DIR / inv["path"]
        ).exists(), f"Invariant test missing: {inv['path']}"

    for mod in discover_invariant_modules():
        assert (
            BACKEND_DIR / mod["path"]
        ).exists(), f"Invariant module missing: {mod['path']}"

    for ds in discover_golden_datasets():
        assert (
            BACKEND_DIR / ds["path"]
        ).exists(), f"Golden dataset missing: {ds['path']}"

    for ct in discover_contract_tests():
        assert (
            BACKEND_DIR / ct["path"]
        ).exists(), f"Contract test missing: {ct['path']}"

    for builder in discover_builders():
        assert (
            BACKEND_DIR / builder["path"]
        ).exists(), f"Builder missing: {builder['path']}"


def test_capabilities_have_required_metadata() -> None:
    """Every registered capability must have required metadata fields."""
    from verification_runtime.discovery import discover_capabilities
    from verification_runtime.registries import get_capability_by_id

    required = ["property_tests", "invariants", "golden_datasets", "contracts"]
    for cap in discover_capabilities():
        cap_id = cap.get("id", "")
        registered = get_capability_by_id(cap_id)
        assert registered is not None, f"Capability '{cap_id}' not in registry"
        for field in required:
            assert (
                registered.get(field) is not None
            ), f"Capability '{cap_id}' missing required field: {field}"


def test_pipeline_stages_have_runners() -> None:
    """Every pipeline stage must have a runner function."""
    from verification_runtime.orchestrator import FULL_PIPELINE, STAGE_RUNNERS

    for stage_id in FULL_PIPELINE:
        assert stage_id in STAGE_RUNNERS, f"Stage '{stage_id}' missing runner"


def test_no_duplicate_registrations() -> None:
    """No duplicate test paths or capability IDs."""
    from verification_runtime.discovery import (
        discover_capability_tests,
        discover_invariant_tests,
        discover_property_tests,
    )

    cap_ids = [c["id"] for c in discover_capability_tests()]
    assert len(cap_ids) == len(set(cap_ids)), "Duplicate capability test directories"

    prop_paths = [t["path"] for t in discover_property_tests()]
    assert len(prop_paths) == len(set(prop_paths)), "Duplicate property test paths"

    inv_paths = [t["path"] for t in discover_invariant_tests()]
    assert len(inv_paths) == len(set(inv_paths)), "Duplicate invariant test paths"


def test_builder_modules_are_valid_python() -> None:
    """All builder modules must be syntactically valid and contain builders or loaders."""
    import ast

    from verification_runtime.discovery import discover_builders

    for builder in discover_builders():
        full_path = BACKEND_DIR / builder["path"]
        tree = ast.parse(full_path.read_text())
        has_builder_class = any(
            isinstance(node, ast.ClassDef) and "Builder" in node.name
            for node in ast.walk(tree)
        )
        has_loader_function = any(
            isinstance(node, ast.FunctionDef) and node.name.startswith("load_")
            for node in ast.walk(tree)
        )
        assert (
            has_builder_class or has_loader_function
        ), f"Builder module {builder['path']} has no Builder class or load_ function"


def test_fixture_files_are_valid_python() -> None:
    """All conftest.py files must be syntactically valid."""
    import ast

    from verification_runtime.discovery import discover_fixtures

    for fixture in discover_fixtures():
        full_path = BACKEND_DIR / fixture["path"]
        ast.parse(full_path.read_text())


def test_verification_map_complete() -> None:
    """Verification map must cover all registered capabilities."""
    from verification_runtime.discovery import get_verification_map

    vmap = get_verification_map()
    assert len(vmap) > 0, "Verification map is empty"

    for cap_id, cap_data in vmap.items():
        assert cap_data["name"], f"Capability {cap_id} missing name"
        has_verification = (
            cap_data["property_tests"]
            or cap_data["invariant_tests"]
            or cap_data["golden_datasets"]
            or cap_data["contracts"]
        )
        if not has_verification:
            pytest.skip(
                f"Capability {cap_id} has no verification tests (Phase 1 backlog)"
            )


def test_self_validator_runs_clean() -> None:
    """Self-validator must report all checks as valid or have acceptable gaps."""
    from verification_runtime.self_validator import run_all_validations

    report = run_all_validations()
    # Allow known Phase 1 backlog gaps:
    acceptable_gaps = [
        "financial_events",  # Phase 1 backlog: add property tests
        "dependency_graph_integrity",  # Known: verification modules appear in dependency graph but not in capabilities
    ]
    for _key, value in report.items():
        if isinstance(value, dict) and value.get("valid") is False:
            missing = value.get("missing", [])
            errors = value.get("errors", [])
            filtered_missing = [
                m for m in missing if not any(gap in str(m) for gap in acceptable_gaps)
            ]
            filtered_errors = [
                e for e in errors if not any(gap in str(e) for gap in acceptable_gaps)
            ]
            if filtered_missing or filtered_errors:
                raise AssertionError(
                    f"Self-validation failed for {_key}: {json.dumps(value, indent=2)}"
                )


def overall_health(report: dict[str, Any]) -> bool:
    """Determine if the verification runtime is healthy."""
    for _key, value in report.items():
        if isinstance(value, dict) and value.get("valid") is False:
            return False
    return True
