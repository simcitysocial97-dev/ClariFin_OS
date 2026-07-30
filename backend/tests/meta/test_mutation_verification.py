"""Mutation Verification Tests.

Tests that programmatic mutations of capability files produce correct
impact analysis results.

Part B of Phase 3.2 — Capability Validation & Real-World Verification.
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


def _get_engine_files_for_capability(cap_id: str) -> list[str]:
    """Get all engine files for a capability from the registry."""
    registry = _load_registry()
    for cap in registry.get("capabilities", []):
        if cap.get("id") == cap_id:
            return cap.get("engines", [])
    return []


def _get_capability_pairs() -> list[tuple[str, str]]:
    """Get (capability_id, engine_file) pairs for testing."""
    registry = _load_registry()
    pairs = []
    for cap in registry.get("capabilities", []):
        cap_id = cap.get("id", "")
        engines = cap.get("engines", [])
        if engines:
            pairs.append((cap_id, engines[0]))
    return pairs


class TestMutationVerification:
    """Verify that mutations produce correct impact analysis."""

    @pytest.fixture(scope="class")
    def mutation_targets(self) -> list[tuple[str, str]]:
        return _get_capability_pairs()

    def test_all_capabilities_have_mutation_targets(
        self, mutation_targets: list[tuple[str, str]]
    ) -> None:
        """Every capability must have at least one engine file to mutate."""
        registry = _load_registry()
        registered_ids = {
            c.get("id") for c in registry.get("capabilities", []) if c.get("id")
        }
        target_ids = {pair[0] for pair in mutation_targets}
        missing = registered_ids - target_ids
        assert not missing, f"Capabilities without mutation targets: {missing}"

    @pytest.mark.parametrize("cap_id,engine_file", _get_capability_pairs())
    def test_mutation_affects_correct_capability(
        self, cap_id: str, engine_file: str
    ) -> None:
        """Mutating an engine file must affect the correct capability."""
        from src.verification.intelligence.impact_engine import ImpactEngine

        engine = ImpactEngine()
        impact = engine.analyze([engine_file])

        affected_caps = {c.id for c in impact.affected_capabilities}

        assert cap_id in affected_caps, (
            f"Mutating {engine_file} should affect capability {cap_id}, "
            f"but affected capabilities are: {affected_caps}"
        )

    @pytest.mark.parametrize("cap_id,engine_file", _get_capability_pairs())
    def test_mutation_produces_ci_plan(self, cap_id: str, engine_file: str) -> None:
        """Mutating an engine file must produce a valid CI plan."""
        from src.verification.intelligence.selective_engine import SelectiveEngine

        engine = SelectiveEngine()
        plan = engine.plan([engine_file])

        assert plan.strategy in (
            "fast",
            "full",
            "selective",
        ), f"Invalid strategy for {engine_file}: {plan.strategy}"
        assert len(plan.must_run_jobs) > 0, f"No must-run jobs for {engine_file}"

    @pytest.mark.parametrize("cap_id,engine_file", _get_capability_pairs())
    def test_mutation_dependency_graph_consistent(
        self, cap_id: str, engine_file: str
    ) -> None:
        """Mutating an engine file must produce consistent dependency graph."""
        from runtime.discovery import discover_dependencies

        dep_map = discover_dependencies()
        all_cap_ids = set(dep_map.get("capabilities", {}).keys())

        from src.verification.intelligence.impact_engine import ImpactEngine

        engine = ImpactEngine()
        impact = engine.analyze([engine_file])

        for affected_cap in impact.affected_capabilities:
            assert (
                affected_cap.id in all_cap_ids
            ), f"Affected capability {affected_cap.id} not in dependency graph"

    @pytest.mark.parametrize("cap_id,engine_file", _get_capability_pairs())
    def test_mutation_no_false_negatives(self, cap_id: str, engine_file: str) -> None:
        """Mutation must not produce false negatives (missing required tests)."""
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
                    if target_type in (
                        "property_test",
                        "invariant_test",
                        "capability_test",
                        "golden_dataset",
                    ):
                        required_tests.add(edge.get("target", ""))

        # Get scheduled tests from CI plan
        scheduled_tests: set[str] = set()
        for job in plan.must_run_jobs:
            for target_path in job.targets:
                if "tests/" in target_path:
                    scheduled_tests.add(target_path)

        # Check for false negatives
        false_negatives = required_tests - scheduled_tests
        assert not false_negatives, (
            f"False negatives for {engine_file}: {false_negatives} "
            f"required but not scheduled"
        )

    @pytest.mark.parametrize("cap_id,engine_file", _get_capability_pairs())
    def test_mutation_file_restored(self, cap_id: str, engine_file: str) -> None:
        """After mutation verification, the file must be restored."""
        from tools.mutation_verification import verify_mutation

        registry = _load_registry()
        cap = next(
            (c for c in registry.get("capabilities", []) if c.get("id") == cap_id), {}
        )

        # Get original content
        file_path = BACKEND_DIR / engine_file
        original_content = file_path.read_text()

        # Run mutation verification (which mutates and restores)
        verify_mutation(cap)

        # Verify file is restored
        restored_content = file_path.read_text()
        assert (
            restored_content == original_content
        ), f"File {engine_file} was not properly restored after mutation"
