"""Mutation Registry Meta Tests.

Tests for verifying the mutation-registry structure and references.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Test file is at: backend/tests/meta/test_mutation_registry.py
# Need 4 parents to reach project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
GENERATED_DIR = PROJECT_ROOT / "backend" / "tests" / "generated"

# Scripts are at backend/tools
MUTATION_DISCOVERY_SCRIPT = PROJECT_ROOT / "backend" / "tools" / "mutation_discovery.py"
TEST_STRENGTH_SCRIPT = PROJECT_ROOT / "backend" / "tools" / "test_strength.py"


def test_registry_exists() -> None:
    """mutation-registry.json must exist after generation."""
    result = subprocess.run(
        [sys.executable, str(MUTATION_DISCOVERY_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"mutation_discovery failed: {result.stderr}"

    registry_path = GENERATED_DIR / "mutation-registry.json"
    assert registry_path.exists(), "mutation-registry.json not generated"


def test_registry_schema() -> None:
    """mutation-registry.json must have required schema fields."""
    subprocess.run(
        [sys.executable, str(MUTATION_DISCOVERY_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
    )

    registry_path = GENERATED_DIR / "mutation-registry.json"
    with open(registry_path) as f:
        data = json.load(f)

    # Top-level fields
    assert "generated_at" in data, "Registry missing 'generated_at'"
    assert "entries" in data, "Registry missing 'entries'"

    # Each entry must have required fields
    for entry in data.get("entries", []):
        assert "module" in entry, "Entry missing 'module'"
        assert "function" in entry, "Entry missing 'function'"
        assert "capability" in entry, "Entry missing 'capability'"
        assert "risk" in entry, "Entry missing 'risk'"
        assert "mutation_types" in entry, "Entry missing 'mutation_types'"
        assert "existing_tests" in entry, "Entry missing 'existing_tests'"


def test_module_exists() -> None:
    """Every registered module must exist on disk."""
    subprocess.run(
        [sys.executable, str(MUTATION_DISCOVERY_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
    )

    registry_path = GENERATED_DIR / "mutation-registry.json"
    with open(registry_path) as f:
        data = json.load(f)

    for entry in data.get("entries", []):
        module_path = entry.get("module")
        full_path = PROJECT_ROOT / "backend" / module_path
        assert full_path.exists(), f"Registered module does not exist: {module_path}"


def test_capability_exists() -> None:
    """Every capability reference must be valid."""
    subprocess.run(
        [sys.executable, str(MUTATION_DISCOVERY_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
    )

    registry_path = GENERATED_DIR / "mutation-registry.json"
    with open(registry_path) as f:
        data = json.load(f)

    # Load capability registry to validate references
    cap_registry_path = GENERATED_DIR / "capability-registry.yaml"
    import yaml
    with open(cap_registry_path) as f:
        cap_registry = yaml.safe_load(f)

    valid_capabilities = {cap["id"] for cap in cap_registry.get("capabilities", [])}

    for entry in data.get("entries", []):
        cap_id = entry.get("capability")
        if cap_id and cap_id != "unknown":
            assert cap_id in valid_capabilities, f"Invalid capability reference: {cap_id}"


def test_mutation_types_valid() -> None:
    """Mutation types must be from known categories."""
    subprocess.run(
        [sys.executable, str(MUTATION_DISCOVERY_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
    )

    registry_path = GENERATED_DIR / "mutation-registry.json"
    with open(registry_path) as f:
        data = json.load(f)

    valid_types = {
        "Arithmetic", "Comparison", "Boolean",
        "Constant replacement", "Boundary conditions",
        "Off-by-one", "Loop termination", "Sign inversion"
    }

    for entry in data.get("entries", []):
        for mtype in entry.get("mutation_types", []):
            assert mtype in valid_types, f"Invalid mutation type: {mtype}"


def test_mutation_map_exists() -> None:
    """mutation-map.json must exist after generation."""
    subprocess.run(
        [sys.executable, str(MUTATION_DISCOVERY_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
    )

    map_path = GENERATED_DIR / "mutation-map.json"
    assert map_path.exists(), "mutation-map.json not generated"


def test_mutation_readiness_json_exists() -> None:
    """mutation-readiness.json must exist after generation."""
    subprocess.run(
        [sys.executable, str(MUTATION_DISCOVERY_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
    )

    readiness_path = GENERATED_DIR / "mutation-readiness.json"
    assert readiness_path.exists(), "mutation-readiness.json not generated"


def test_mutation_readiness_md_exists() -> None:
    """mutation-readiness.md must exist after generation."""
    subprocess.run(
        [sys.executable, str(MUTATION_DISCOVERY_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
    )

    md_path = GENERATED_DIR / "mutation-readiness.md"
    assert md_path.exists(), "mutation-readiness.md not generated"


def test_mutation_gaps_md_exists() -> None:
    """mutation-gaps.md must exist after generation."""
    subprocess.run(
        [sys.executable, str(MUTATION_DISCOVERY_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
    )

    gaps_path = GENERATED_DIR / "mutation-gaps.md"
    assert gaps_path.exists(), "mutation-gaps.md not generated"


def test_test_strength_json_exists() -> None:
    """test-strength.json must exist after test_strength runs."""
    result = subprocess.run(
        [sys.executable, str(TEST_STRENGTH_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"test_strength failed: {result.stderr}"

    strength_path = GENERATED_DIR / "test-strength.json"
    assert strength_path.exists(), "test-strength.json not generated"


def test_test_strength_md_exists() -> None:
    """test-strength.md must exist after test_strength runs."""
    subprocess.run(
        [sys.executable, str(TEST_STRENGTH_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
    )

    md_path = GENERATED_DIR / "test-strength.md"
    assert md_path.exists(), "test-strength.md not generated"


def test_test_strength_schema() -> None:
    """test-strength.json must have required schema fields."""
    subprocess.run(
        [sys.executable, str(TEST_STRENGTH_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
    )

    strength_path = GENERATED_DIR / "test-strength.json"
    with open(strength_path) as f:
        data = json.load(f)

    assert "generated_at" in data, "Missing generated_at"
    assert "capabilities" in data, "Missing capabilities"

    for cap in data.get("capabilities", []):
        assert "id" in cap, "Capability missing 'id'"
        assert "name" in cap, "Capability missing 'name'"
        assert "strength" in cap, "Capability missing 'strength'"
        assert "weighted_score" in cap, "Capability missing 'weighted_score'"
        assert "gaps" in cap, "Capability missing 'gaps'"
        assert "evidence" in cap, "Capability missing 'evidence'"
