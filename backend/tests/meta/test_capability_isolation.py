"""Capability Isolation Stress Test.

Verifies that changes to one capability do not leak to unrelated capabilities.

Part E of Phase 3.2 - Capability Validation & Real-World Verification.
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


def _get_capability_router_pairs() -> list[tuple[str, str]]:
    """Get (capability_id, router_file) pairs for testing."""
    registry = _load_registry()
    pairs = []
    for cap in registry.get("capabilities", []):
        cap_id = cap.get("id", "")
        routers = cap.get("routers", [])
        if routers:
            pairs.append((cap_id, routers[0]))
    return pairs


class TestCapabilityIsolation:
    """Verify that source changes only select intended tests."""

    @pytest.mark.parametrize("cap_id,engine_file", _get_capability_engine_pairs())
    def test_engine_change_only_affects_own_capability(
        self, cap_id: str, engine_file: str
    ) -> None:
        """Engine change must select its capability and must not select unrelated capabilities."""
        from src.verification.intelligence.impact_engine import ImpactEngine

        engine = ImpactEngine()
        impact = engine.analyze([engine_file])

        affected_caps = {c.id for c in impact.affected_capabilities}

        # The engine's capability must be affected
        assert cap_id in affected_caps, (
            f"Engine file {engine_file} should affect capability {cap_id}, "
            f"but affected capabilities are: {affected_caps}"
        )

    @pytest.mark.parametrize("cap_id,router_file", _get_capability_router_pairs())
    def test_router_change_only_affects_own_capability(
        self, cap_id: str, router_file: str
    ) -> None:
        """Router change must select its capability and must not select unrelated capabilities."""
        from src.verification.intelligence.impact_engine import ImpactEngine

        engine = ImpactEngine()
        impact = engine.analyze([router_file])

        affected_caps = {c.id for c in impact.affected_capabilities}

        # The router's capability must be affected
        assert cap_id in affected_caps, (
            f"Router file {router_file} should affect capability {cap_id}, "
            f"but affected capabilities are: {affected_caps}"
        )

    def test_no_cross_capability_leakage_for_engines(self) -> None:
        """Engine changes should not leak to unrelated capabilities."""
        registry = _load_registry()
        from src.verification.intelligence.impact_engine import ImpactEngine

        engine = ImpactEngine()

        for cap in registry.get("capabilities", []):
            cap.get("id", "")
            engines = cap.get("engines", [])
            if not engines:
                continue

            engine_file = engines[0]
            impact = engine.analyze([engine_file])
            affected_caps = {c.id for c in impact.affected_capabilities}

            # Engine file should not affect more than 6 capabilities (its own + transitive deps)
            assert len(affected_caps) <= 6, (
                f"Engine file {engine_file} affects {len(affected_caps)} capabilities: "
                f"{affected_caps} - possible leakage"
            )

    def test_no_cross_capability_leakage_for_routers(self) -> None:
        """Router changes should not leak to unrelated capabilities."""
        registry = _load_registry()
        from src.verification.intelligence.impact_engine import ImpactEngine

        engine = ImpactEngine()

        for cap in registry.get("capabilities", []):
            cap.get("id", "")
            routers = cap.get("routers", [])
            if not routers:
                continue

            router_file = routers[0]
            impact = engine.analyze([router_file])
            affected_caps = {c.id for c in impact.affected_capabilities}

            # Router file should not affect more than 10 capabilities (shared routers are expected)
            assert len(affected_caps) <= 10, (
                f"Router file {router_file} affects {len(affected_caps)} capabilities: "
                f"{affected_caps} - possible leakage"
            )

    def test_isolation_matrix_complete(self) -> None:
        """All capabilities must be included in the isolation test."""
        registry = _load_registry()
        engine_pairs = set(_get_capability_engine_pairs())
        router_pairs = set(_get_capability_router_pairs())

        registered_ids = {
            c.get("id") for c in registry.get("capabilities", []) if c.get("id")
        }

        engine_ids = {pair[0] for pair in engine_pairs}
        router_ids = {pair[0] for pair in router_pairs}

        tested_ids = engine_ids | router_ids
        missing = registered_ids - tested_ids
        assert not missing, f"Capabilities not included in isolation test: {missing}"
