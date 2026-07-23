"""Coverage Integrity Tests.

These tests validate that the generated artifacts are valid and all referenced
paths in capability manifests actually exist.
"""

from __future__ import annotations

import json
import pathlib

import yaml

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
GENERATED_DIR = PROJECT_ROOT / "memory-bank" / "generated"
CAPABILITIES_DIR = PROJECT_ROOT / "memory-bank" / "capabilities"
BACKEND_DIR = PROJECT_ROOT / "backend"


def test_coverage_json_exists() -> None:
    """coverage.json must exist in memory-bank/generated/."""
    assert (GENERATED_DIR / "coverage.json").exists(), "coverage.json not found - run check_coverage.py first"


def test_coverage_json_valid() -> None:
    """coverage.json must be valid JSON with expected structure."""
    with open(GENERATED_DIR / "coverage.json") as f:
        data = json.load(f)

    assert "generated_at" in data, "coverage.json missing 'generated_at'"
    assert "capabilities" in data, "coverage.json missing 'capabilities'"
    assert isinstance(data["capabilities"], list), "'capabilities' must be a list"

    for cap in data["capabilities"]:
        assert "id" in cap, "Capability missing 'id'"
        assert "name" in cap, "Capability missing 'name'"
        assert "overall_maturity" in cap, "Capability missing 'overall_maturity'"


def test_capability_registry_exists() -> None:
    """capability-registry.yaml must exist in memory-bank/generated/."""
    assert (GENERATED_DIR / "capability-registry.yaml").exists(), "capability-registry.yaml not found - run check_coverage.py first"


def test_capability_registry_matches_manifests() -> None:
    """capability-registry.yaml must match the individual capability manifests."""
    with open(GENERATED_DIR / "capability-registry.yaml") as f:
        registry = yaml.safe_load(f)

    # Load all individual manifests
    manifest_ids: set[str] = set()
    for yaml_file in CAPABILITIES_DIR.glob("*.yaml"):
        with open(yaml_file) as f:
            manifest = yaml.safe_load(f)
            if manifest and "id" in manifest:
                manifest_ids.add(manifest["id"])

    # Check registry contains all manifests
    registry_ids = {cap["id"] for cap in registry.get("capabilities", [])}
    assert registry_ids == manifest_ids, f"Registry IDs {registry_ids} don't match manifest IDs {manifest_ids}"


def test_all_capability_references_exist() -> None:
    """All referenced paths in capability manifests must exist."""
    errors: list[str] = []

    for yaml_file in CAPABILITIES_DIR.glob("*.yaml"):
        with open(yaml_file) as f:
            manifest = yaml.safe_load(f)

        if not manifest:
            continue

        cap_id = manifest.get("id", "unknown")

        # Check routers
        for router in manifest.get("routers", []):
            path = BACKEND_DIR / router
            if not path.exists():
                errors.append(f"{cap_id}: router {router} NOT FOUND")

        # Check services
        for service in manifest.get("services", []):
            path = BACKEND_DIR / service
            if not path.exists():
                errors.append(f"{cap_id}: service {service} NOT FOUND")

        # Check engines
        for engine in manifest.get("engines", []):
            path = BACKEND_DIR / engine
            if not path.exists():
                errors.append(f"{cap_id}: engine {engine} NOT FOUND")

        # Check repositories
        for repo in manifest.get("repositories", []):
            path = BACKEND_DIR / repo
            if not path.exists():
                errors.append(f"{cap_id}: repository {repo} NOT FOUND")

        # Check golden datasets
        for dataset in manifest.get("golden_datasets", []):
            path = BACKEND_DIR / dataset
            if not path.exists():
                errors.append(f"{cap_id}: golden dataset {dataset} NOT FOUND")

        # Check property tests
        for test in manifest.get("property_tests", []):
            path = BACKEND_DIR / test
            if not path.exists():
                errors.append(f"{cap_id}: property test {test} NOT FOUND")

        # Check invariants - try both locations
        for inv in manifest.get("invariants", []):
            path = BACKEND_DIR / inv
            alt_path = BACKEND_DIR / inv.replace("tests/invariants/test_", "tests/domain/invariants/").replace("_", "")
            if not path.exists() and not alt_path.exists():
                errors.append(f"{cap_id}: invariant {inv} NOT FOUND")

    assert not errors, "Missing references:\n" + "\n".join(errors)


def test_coverage_report_md_exists() -> None:
    """coverage.md must exist in memory-bank/generated/."""
    assert (GENERATED_DIR / "coverage.md").exists(), "coverage.md not found - run check_coverage.py first"


def test_traceability_md_exists() -> None:
    """traceability.md must exist in memory-bank/generated/."""
    assert (GENERATED_DIR / "traceability.md").exists(), "traceability.md not found - run check_coverage.py first"


def test_change_impact_md_exists() -> None:
    """change-impact.md must exist in memory-bank/generated/."""
    assert (GENERATED_DIR / "change-impact.md").exists(), "change-impact.md not found - run check_coverage.py first"


def test_generated_files_have_content() -> None:
    """Generated files must not be empty."""
    for filename in ["coverage.md", "coverage.json", "traceability.md", "change-impact.md", "capability-registry.yaml"]:
        path = GENERATED_DIR / filename
        if path.exists():
            content = path.read_text()
            assert len(content) > 100, f"{filename} is suspiciously short ({len(content)} bytes)"
