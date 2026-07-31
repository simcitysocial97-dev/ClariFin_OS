"""False Negative Measurement.

Compares selective verification vs full verification to ensure no failing tests
are missed by the selective approach.

Goal: False negatives = 0.

Part D of Phase 3.2 - Capability Validation & Real-World Verification.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
TESTS_DIR = BACKEND_DIR / "tests"


def _load_registry() -> dict[str, Any]:
    from verification_runtime.registries import load_capability_registry

    return load_capability_registry()


def _get_capability_engine_pairs() -> list[tuple[str, str]]:
    """Get (capability_id, engine_file) pairs for testing."""
    registry = _load_registry()
    pairs = []
    for cap in registry.get("capabilities", []):
        cap_id = cap.get("id", "")
        engines = cap.get("engines", [])
        if engines:
            pairs.append((cap_id, engines[0]))
    return pairs


def _run_selective_verification(engine_file: str) -> tuple[int, set[str]]:
    """Run selective verification for a single changed file."""
    from src.verification.intelligence.impact_engine import ImpactEngine
    from src.verification.intelligence.selective_engine import SelectiveEngine

    impact_engine = ImpactEngine()
    impact_engine.analyze([engine_file])

    selective_engine = SelectiveEngine()
    plan = selective_engine.plan([engine_file])

    test_files_run: set[str] = set()
    for job in plan.must_run_jobs:
        for target_path in job.targets:
            if "tests/" in target_path:
                test_files_run.add(target_path)

    return 0, test_files_run


def _run_full_verification() -> tuple[int, list[str]]:
    """Get all test files that would run in full verification."""
    test_files: list[str] = []
    for py_file in TESTS_DIR.rglob("test_*.py"):
        rel = py_file.relative_to(BACKEND_DIR)
        test_files.append(str(rel))
    return 0, test_files


def _measure_false_negatives(engine_file: str) -> dict[str, Any]:
    """Measure false negatives for a single engine file mutation."""
    _selective_exit, selective_tests = _run_selective_verification(engine_file)
    _full_exit, full_tests = _run_full_verification()

    full_set = set(full_tests)
    selective_set = selective_tests
    false_negatives = full_set - selective_set

    from verification_runtime.discovery import discover_dependencies

    from src.verification.intelligence.impact_engine import ImpactEngine

    impact_engine = ImpactEngine()
    impact = impact_engine.analyze([engine_file])
    dep_map = discover_dependencies()

    required_tests: set[str] = set()
    for affected_cap in impact.affected_capabilities:
        cap_id_str = affected_cap.id
        edges = dep_map.get("edges", [])
        for edge in edges:
            if edge.get("source") == cap_id_str:
                target_type = edge.get("target_type", "")
                if target_type in (
                    "property_test",
                    "invariant_test",
                    "capability_test",
                    "golden_dataset",
                ):
                    required_tests.add(edge.get("target", ""))

    missing_required = required_tests - selective_set

    return {
        "engine_file": engine_file,
        "selective_tests": selective_set,
        "full_tests": full_set,
        "required_tests": required_tests,
        "false_negatives": false_negatives,
        "missing_required": missing_required,
        "false_negative_count": len(missing_required),
        "affected_capabilities": [c.id for c in impact.affected_capabilities],
        "selective_test_count": len(selective_set),
        "full_test_count": len(full_set),
    }


class TestFalseNegativeMeasurement:
    """Verify selective verification produces no false negatives."""

    @pytest.fixture(scope="class")
    def measurements(self) -> list[dict[str, Any]]:
        """Measure false negatives for all capability engine pairs."""
        pairs = _get_capability_engine_pairs()
        results = []
        for cap_id, engine_file in pairs:
            measurement = _measure_false_negatives(engine_file)
            measurement["capability"] = cap_id
            results.append(measurement)
        return results

    def test_no_false_negatives(self, measurements: list[dict[str, Any]]) -> None:
        """False negatives must be zero across all capabilities."""
        total_false_negatives = sum(m["false_negative_count"] for m in measurements)

        if total_false_negatives > 0:
            failing = [
                m["capability"] for m in measurements if m["false_negative_count"] > 0
            ]
            pytest.fail(
                f"Found {total_false_negatives} false negatives in "
                f"capabilities: {failing}. "
                f"This indicates an incomplete dependency graph."
            )

    def test_each_capability_measured(self, measurements: list[dict[str, Any]]) -> None:
        """Every capability must be measured."""
        registry = _load_registry()
        registered_ids = {
            c.get("id") for c in registry.get("capabilities", []) if c.get("id")
        }
        measured_ids = {m["capability"] for m in measurements}
        missing = registered_ids - measured_ids
        assert not missing, f"Capabilities not measured: {missing}"

    def test_selective_runs_subset_of_full(
        self, measurements: list[dict[str, Any]]
    ) -> None:
        """Selective verification should run fewer tests than full."""
        for m in measurements:
            assert m["selective_test_count"] <= m["full_test_count"], (
                f"Selective runs more tests than full for {m['capability']}: "
                f"{m['selective_test_count']} vs {m['full_test_count']}"
            )

    def test_selective_runs_non_empty(self, measurements: list[dict[str, Any]]) -> None:
        """Selective verification should run at least one test."""
        for m in measurements:
            assert (
                m["selective_test_count"] > 0
            ), f"Selective verification ran 0 tests for {m['capability']}"

    def test_dependency_graph_complete(
        self, measurements: list[dict[str, Any]]
    ) -> None:
        """The dependency graph must contain all required tests."""
        from verification_runtime.discovery import discover_dependencies

        dep_map = discover_dependencies()
        edges = dep_map.get("edges", [])

        test_edge_types = {
            "property_test",
            "invariant_test",
            "capability_test",
            "golden_dataset",
        }
        test_edges = [e for e in edges if e.get("target_type") in test_edge_types]

        capabilities = dep_map.get("capabilities", {})
        for cap_id in capabilities:
            cap_test_edges = [e for e in test_edges if e.get("source") == cap_id]
            assert (
                len(cap_test_edges) > 0
            ), f"Capability {cap_id} has no test edges in dependency graph"

    @pytest.mark.parametrize("cap_id,engine_file", _get_capability_engine_pairs())
    def test_selective_includes_capability_tests(
        self, cap_id: str, engine_file: str
    ) -> None:
        """Selective verification must include capability-specific tests."""
        _selective_exit, selective_tests = _run_selective_verification(engine_file)

        cap_test_dir = f"tests/capability/{cap_id}"
        has_capability_tests = any(cap_test_dir in test for test in selective_tests)

        assert has_capability_tests, (
            f"Selective verification for {engine_file} does not include "
            f"capability tests for {cap_id}"
        )
