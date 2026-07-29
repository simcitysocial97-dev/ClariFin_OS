"""False Positive Measurement.

Measures over-selection: tests scheduled but not actually required.

Goal: False positives < 5%.

Part C of Phase 3.2 — Capability Validation & Real-World Verification.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
TESTS_DIR = BACKEND_DIR / "tests"


def _load_registry() -> dict[str, Any]:
    from runtime.registries import load_capability_registry

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


def _measure_false_positives(engine_file: str) -> dict[str, Any]:
    """Measure false positives for a single engine file mutation.

    Returns a dict with:
    - required_tests: set of tests that should run (from dependency graph)
    - scheduled_tests: set of tests that are scheduled (from CI plan)
    - false_positives: tests scheduled but not required
    - false_negative_count: required tests not scheduled
    - over_selection_rate: false_positives / total_scheduled
    """
    from runtime.discovery import discover_dependencies

    from src.verification.intelligence.impact_engine import ImpactEngine
    from src.verification.intelligence.selective_engine import SelectiveEngine

    # Analyze impact
    impact_engine = ImpactEngine()
    impact = impact_engine.analyze([engine_file])

    # Generate CI plan
    selective_engine = SelectiveEngine()
    plan = selective_engine.plan([engine_file])

    # Get dependency graph
    dep_map = discover_dependencies()

    # Get required tests from dependency graph
    required_tests: set[str] = set()
    for affected_cap in impact.affected_capabilities:
        cap_id_str = affected_cap.id
        edges = dep_map.get("edges", [])
        for edge in edges:
            if edge.get("source") == cap_id_str:
                target_type = edge.get("target_type", "")
                if target_type in ("property_test", "invariant_test", "capability_test"):
                    required_tests.add(edge.get("target", ""))

    # Get scheduled tests from CI plan
    scheduled_tests: set[str] = set()
    for job in plan.must_run_jobs:
        for target_path in job.targets:
            if "tests/" in target_path:
                scheduled_tests.add(target_path)

    # Also count test suites (broader)
    # Each must_run job represents a test suite
    total_scheduled_suites = len(plan.must_run_jobs)

    # False positives: tests scheduled but not required
    false_positives = scheduled_tests - required_tests
    false_negative_count = len(required_tests - scheduled_tests)

    # Over-selection rate: false positives / total scheduled
    total_scheduled = len(scheduled_tests)
    over_selection_rate = (
        len(false_positives) / total_scheduled if total_scheduled > 0 else 0.0
    )

    return {
        "engine_file": engine_file,
        "required_tests": required_tests,
        "scheduled_tests": scheduled_tests,
        "false_positives": false_positives,
        "false_positive_count": len(false_positives),
        "false_negative_count": false_negative_count,
        "total_scheduled": total_scheduled,
        "over_selection_rate": over_selection_rate,
        "must_run_jobs": [j.job_id for j in plan.must_run_jobs],
        "skipped_jobs": [j.job_id for j in plan.skipped_jobs],
        "strategy": plan.strategy,
        "overall_risk": plan.overall_risk,
        "affected_capabilities": [c.id for c in impact.affected_capabilities],
    }


class TestFalsePositiveMeasurement:
    """Measure over-selection in the selective verification framework."""

    @pytest.fixture(scope="class")
    def measurements(self) -> list[dict[str, Any]]:
        """Measure false positives for all capability engine pairs."""
        pairs = _get_capability_engine_pairs()
        results = []
        for cap_id, engine_file in pairs:
            measurement = _measure_false_positives(engine_file)
            measurement["capability"] = cap_id
            results.append(measurement)
        return results

    def test_false_positive_rate_below_5_percent(
        self, measurements: list[dict[str, Any]]
    ) -> None:
        """Overall false positive rate must be below 5%."""
        total_false_positives = sum(m["false_positive_count"] for m in measurements)
        total_scheduled = sum(m["total_scheduled"] for m in measurements)

        if total_scheduled == 0:
            pytest.skip("No tests scheduled")

        rate = total_false_positives / total_scheduled
        assert rate < 0.05, (
            f"False positive rate is {rate:.2%} ({total_false_positives}/{total_scheduled}), "
            f"must be below 5%"
        )

    def test_no_false_negatives(
        self, measurements: list[dict[str, Any]]
    ) -> None:
        """False negatives must be zero."""
        total_false_negatives = sum(m["false_negative_count"] for m in measurements)
        assert total_false_negatives == 0, (
            f"Found {total_false_negatives} false negatives across all mutations"
        )

    def test_each_capability_measured(
        self, measurements: list[dict[str, Any]]
    ) -> None:
        """Every capability must be measured."""
        registry = _load_registry()
        registered_ids = {
            c.get("id") for c in registry.get("capabilities", []) if c.get("id")
        }
        measured_ids = {m["capability"] for m in measurements}
        missing = registered_ids - measured_ids
        assert not missing, (
            f"Capabilities not measured: {missing}"
        )

    def test_over_selection_rate_per_capability(
        self, measurements: list[dict[str, Any]]
    ) -> None:
        """Each capability's over-selection rate must be reasonable."""
        for m in measurements:
            rate = m["over_selection_rate"]
            # Allow up to 10% per capability (some capabilities share test suites)
            assert rate < 0.10, (
                f"Over-selection rate for {m['capability']} is {rate:.2%}, "
                f"exceeds 10% threshold"
            )

    def test_measurement_report_generated(
        self, measurements: list[dict[str, Any]]
    ) -> None:
        """The measurement must produce a valid report structure."""
        assert len(measurements) > 0
        for m in measurements:
            assert "capability" in m
            assert "required_tests" in m
            assert "scheduled_tests" in m
            assert "false_positive_count" in m
            assert "false_negative_count" in m
            assert "over_selection_rate" in m
            assert "strategy" in m
            assert "overall_risk" in m
