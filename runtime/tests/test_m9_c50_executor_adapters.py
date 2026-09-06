"""
M9-C50 — Executor Adapter Completeness Tests.

Acceptance tests proving that all registered verification task kinds have
adapters in executor_pipeline.ADAPTERS. Each adapter produces a classified
task (either executable or explicitly not_executable_yet).

No adapter may silently disappear or produce undefined behavior.
"""

from __future__ import annotations

import pytest

from runtime.foundation.verification.executor_pipeline import (
    ADAPTERS,
    adapt_mutation_task,
    adapt_unit_task,
)


@pytest.fixture
def sample_planned_task():
    from runtime.foundation.verification.evidence_planner import PlannedTask

    return PlannedTask(
        task_id="test-task-001",
        task_kind="mutation",
        target="credit_card_engine",
        disposition="selected_fresh",
        cause="test",
    )


@pytest.fixture
def sample_fingerprints():
    from runtime.foundation.verification.executor_pipeline import TaskFingerprints

    return TaskFingerprints(
        source="abc123",
        test="def456",
        config="ghi789",
        toolchain="jkl012",
    )


class TestAllAdaptersRegistered:
    """Every VerificationKind has an adapter entry."""

    def test_adapters_registered(self):
        assert len(ADAPTERS) >= 1, "At least one adapter must be registered"

    def test_unit_adapter_exists(self):
        assert "unit" in ADAPTERS

    def test_mutation_adapter_exists(self):
        assert "mutation" in ADAPTERS

    def test_all_kinds_have_entries(self):
        """All kinds in VerificationKind Literal have ADAPTERS entries."""
        # VerificationKind is a Literal; check known kinds
        known_kinds = {
            "unit",
            "property",
            "invariant",
            "contract",
            "coverage",
            "mutation",
            "golden",
            "capability",
        }
        for kind in known_kinds:
            assert kind in ADAPTERS, f"Missing adapter for kind={kind!r}"


class TestAdapterClassification:
    """Every adapter classifies its task explicitly."""

    def test_no_adapter_is_none(self):
        for kind, adapter in ADAPTERS.items():
            assert adapter is not None, f"Adapter for {kind!r} is None"

    def test_adapters_are_callable(self):
        for kind, adapter in ADAPTERS.items():
            assert callable(adapter), f"Adapter for {kind!r} is not callable"


class TestSpecificAdapters:
    """Verify canonical adapters are correctly wired."""

    def test_unit_adapter_is_canonical(self):
        assert ADAPTERS["unit"] is adapt_unit_task

    def test_mutation_adapter_is_canonical(self):
        assert ADAPTERS["mutation"] is adapt_mutation_task


class TestAdapterOutput:
    """Verify adapters produce structured tasks."""

    def test_unit_produces_executable_task(
        self, sample_planned_task, sample_fingerprints
    ):
        result = adapt_unit_task(sample_planned_task, sample_fingerprints)
        assert result.executable == "executable"
        assert result.evidence_kind == "pytest-junit"

    def test_mutation_produces_classified_task(
        self, sample_planned_task, sample_fingerprints
    ):
        result = adapt_mutation_task(sample_planned_task, sample_fingerprints)
        # Mutation adapter may produce executable or not_executable_yet
        # depending on whether mutation targets are configured
        assert result.executable in ("executable", "not_executable_yet")
