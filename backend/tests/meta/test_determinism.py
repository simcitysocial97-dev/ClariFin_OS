"""Determinism tests for all generators.

Verifies that generated artifacts are byte-for-byte identical across
repeated runs unless the source actually changes.

No timestamp-only diffs allowed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"


def _hash_file(path: Path) -> str:
    """Return SHA-256 hash of a file's contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_generator_twice_and_compare(
    generator_name: str, run_func, files: list[Path]
) -> None:
    """Run a generator twice and assert all output files are identical."""

    # First run
    run_func()

    # Snapshot hashes after first run
    hashes_after_first = {f: _hash_file(f) for f in files if f.exists()}

    # Second run
    run_func()

    # Snapshot hashes after second run
    hashes_after_second = {f: _hash_file(f) for f in files if f.exists()}

    # Assert first and second runs produce identical output
    for f in files:
        if f.exists():
            assert hashes_after_first[f] == hashes_after_second[f], (
                f"{generator_name}: file {f.name} differs between run 1 and run 2 "
                f"(timestamp-only diff detected)"
            )


def test_dependency_engine_determinism() -> None:
    """DependencyEngine.discover() must produce identical output across runs."""
    from src.verification.intelligence.dependency_engine import DependencyEngine

    engine = DependencyEngine()
    graph1 = engine.discover()
    graph2 = engine.discover()

    d1 = graph1.to_dict()
    d2 = graph2.to_dict()

    # Compare without generated_at (which is a content hash, should be same)
    assert d1 == d2, "DependencyEngine output differs between runs"


def test_selective_engine_determinism() -> None:
    """SelectiveEngine.plan() must produce identical output for same inputs."""
    from src.verification.intelligence.selective_engine import SelectiveEngine

    engine = SelectiveEngine()
    changed_files = ["backend/src/engines/cashflow_engine.py"]

    plan1 = engine.plan(changed_files)
    plan2 = engine.plan(changed_files)

    d1 = plan1.to_dict()
    d2 = plan2.to_dict()

    assert d1 == d2, "SelectiveEngine output differs between runs"


def test_ci_targets_determinism() -> None:
    """CI targets must be identical across calls."""
    from tests.runtime.ci_targets import (
        get_capability_targets,
        get_contract_targets,
        get_golden_targets,
        get_invariant_targets,
        get_mutation_targets,
        get_property_targets,
    )

    assert get_property_targets() == get_property_targets()
    assert get_contract_targets() == get_contract_targets()
    assert get_capability_targets() == get_capability_targets()
    assert get_invariant_targets() == get_invariant_targets()
    assert get_golden_targets() == get_golden_targets()
    assert get_mutation_targets() == get_mutation_targets()


def test_generated_artifacts_no_timestamp_only_diff() -> None:
    """Generated artifacts must not contain timestamp-only diffs.

    Checks that generated_at fields are content hashes, not timestamps.
    """
    # Check api-map.json
    api_map_path = GENERATED_DIR / "api-map.json"
    if api_map_path.exists():
        with open(api_map_path) as f:
            data = json.load(f)
        generated_at = data.get("generated_at", "")
        # Content hash should be 16 hex chars, not an ISO timestamp
        assert (
            len(generated_at) == 16
        ), f"api-map.json generated_at is not a content hash: {generated_at}"
        assert all(
            c in "0123456789abcdef" for c in generated_at
        ), f"api-map.json generated_at contains non-hex chars: {generated_at}"

    # Check contract-registry.json
    contract_path = GENERATED_DIR / "contract-registry.json"
    if contract_path.exists():
        with open(contract_path) as f:
            data = json.load(f)
        generated_at = data.get("generated_at", "")
        if generated_at:
            assert (
                len(generated_at) == 16
            ), f"contract-registry.json generated_at is not a content hash: {generated_at}"
            assert all(
                c in "0123456789abcdef" for c in generated_at
            ), f"contract-registry.json generated_at contains non-hex chars: {generated_at}"

    # Check selective-plan.json
    selective_path = GENERATED_DIR / "selective-plan.json"
    if selective_path.exists():
        with open(selective_path) as f:
            data = json.load(f)
        generated_at = data.get("generated_at", "")
        if generated_at:
            assert (
                len(generated_at) == 16
            ), f"selective-plan.json generated_at is not a content hash: {generated_at}"
            assert all(
                c in "0123456789abcdef" for c in generated_at
            ), f"selective-plan.json generated_at contains non-hex chars: {generated_at}"


def test_contract_generator_no_timestamp_in_output() -> None:
    """Contract test generator must not embed timestamps in generated files."""
    contract_dir = BACKEND_DIR / "tests" / "contract" / "generated"
    if not contract_dir.exists():
        pytest.skip("No generated contract tests found")

    import re

    timestamp_pattern = re.compile(r"# Generated: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    for py_file in contract_dir.glob("test_*.py"):
        content = py_file.read_text()
        # Check for ISO timestamp pattern
        assert not timestamp_pattern.search(content), (
            f"Contract test {py_file.name} contains ISO timestamp - "
            f"should use content hash instead"
        )
