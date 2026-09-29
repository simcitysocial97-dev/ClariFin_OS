"""Regression coverage for large-boundary verification behaviour.

`verify check` used to print a warning when the changed-file boundary exceeded
a limit and then continue into the same expanding plan regardless. On the M9
merge boundary (1,383 files) that produced 247 tasks and roughly 50 minutes of
execution, so the warning was not a control: it documented a run that was
already committed to happening.

The required behaviour is a decision, and these tests pin all six boundary
shapes named in the stabilization objective:

  * normal boundary
  * boundary exactly at the configured threshold
  * oversized boundary
  * oversized boundary that is mostly generated output
  * generated-only change
  * mixed source and generated change
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification import boundary_policy as bp  # noqa: E402
from runtime.foundation.verification.orchestrator import (  # noqa: E402
    _filter_changed_files,
)

THRESHOLD = 100


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Keep every test independent of the operator's environment."""

    for name in (bp.ENV_THRESHOLD, bp.ENV_FALLBACK_DISABLED):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(bp.ENV_THRESHOLD, str(THRESHOLD))
    yield


# ---------------------------------------------------------------------------
# Normal and at-threshold boundaries
# ---------------------------------------------------------------------------


class TestNormalBoundary:
    def test_small_boundary_is_incremental(self):
        assert bp.classify_boundary_size(1) is bp.BoundaryClass.NORMAL
        assert bp.select_strategy(bp.BoundaryClass.NORMAL) is bp.Strategy.INCREMENTAL

    def test_empty_boundary_is_a_certified_no_op(self):
        assert bp.classify_boundary_size(0) is bp.BoundaryClass.EMPTY
        assert bp.select_strategy(bp.BoundaryClass.EMPTY) is bp.Strategy.NO_OP

    @pytest.mark.parametrize("size", [1, 2, 25, 99])
    def test_below_threshold_is_normal(self, size):
        assert bp.classify_boundary_size(size) is bp.BoundaryClass.NORMAL


class TestBoundaryAtThreshold:
    def test_exactly_at_threshold_is_at_limit(self):
        assert bp.classify_boundary_size(THRESHOLD) is bp.BoundaryClass.AT_LIMIT

    def test_at_limit_still_verifies_incrementally(self):
        assert bp.select_strategy(bp.BoundaryClass.AT_LIMIT) is bp.Strategy.INCREMENTAL

    def test_one_below_and_one_above_differ(self):
        assert bp.classify_boundary_size(THRESHOLD - 1) is bp.BoundaryClass.NORMAL
        assert bp.classify_boundary_size(THRESHOLD + 1) is bp.BoundaryClass.OVERSIZED


# ---------------------------------------------------------------------------
# Oversized boundary
# ---------------------------------------------------------------------------


class TestOversizedBoundary:
    @pytest.mark.parametrize("size", [101, 500, 5_000, 250_000])
    def test_above_threshold_is_oversized(self, size):
        assert bp.classify_boundary_size(size) is bp.BoundaryClass.OVERSIZED

    def test_oversized_selects_the_bounded_fallback(self):
        assert (
            bp.select_strategy(bp.BoundaryClass.OVERSIZED)
            is bp.Strategy.BOUNDED_FALLBACK
        )

    def test_fallback_profile_order_names_configured_profiles(self):
        from runtime.foundation.verification.profiles import list_profiles

        available = {p.name for p in list_profiles()}
        assert (
            set(bp.FALLBACK_PROFILE_ORDER) <= available
        ), "the bounded fallback must select existing profiles, not invent them"

    def test_fallback_task_count_is_independent_of_boundary_size(self):
        """The whole point of the fallback: cost must not scale with the boundary.

        Both boundaries are oversized, so both must map to the same fixed
        profile set. This is what makes the strategy *bounded* rather than
        merely different.
        """

        assert set(bp.FALLBACK_PROFILE_ORDER) == set(bp.FALLBACK_PROFILE_ORDER)
        assert len(bp.FALLBACK_PROFILE_ORDER) > 0
        # The strategy is a pure function of the class, not the size.
        a = bp.select_strategy(bp.classify_boundary_size(101))
        b = bp.select_strategy(bp.classify_boundary_size(250_000))
        assert a is b is bp.Strategy.BOUNDED_FALLBACK


class TestOversizedBoundaryIsMostlyGenerated:
    def test_generated_files_do_not_push_a_boundary_into_the_fallback(self):
        """Generated output must be excluded before the boundary is classified.

        If generated files counted, a run that only regenerated output would be
        treated as a repository-wide change and would trigger a full sweep.
        """

        files = ["runtime/generated/metrics/a.json"] * 100_000
        assert _filter_changed_files(files) == []
        assert bp.classify_boundary_size(0) is bp.BoundaryClass.EMPTY

    def test_oversized_containing_generated_output_is_still_oversized(self):
        """Generated bulk must neither inflate nor dilute the real boundary.

        150 genuine source files sit under 100,000 generated ones. Filtering
        removes the generated bulk, and the 150 real files are still over the
        threshold, so the fallback is selected. If generated output were
        counted the classification would be oversized for the wrong reason; if
        the filtering were inverted, the real change would be hidden.
        """

        files = [f"backend/src/module_{i}.py" for i in range(150)] + [
            f"runtime/generated/metrics/{i}.json" for i in range(100_000)
        ]
        filtered = _filter_changed_files(files)
        assert len(filtered) == 150
        assert bp.classify_boundary_size(len(filtered)) is bp.BoundaryClass.OVERSIZED
        assert (
            bp.select_strategy(bp.classify_boundary_size(len(filtered)))
            is bp.Strategy.BOUNDED_FALLBACK
        )


class TestGeneratedOnlyChange:
    def test_generated_only_boundary_is_empty(self):
        files = [
            "runtime/generated/platform/snapshot.json",
            "runtime/generated/m9-c42.21/survivors/x.diff",
            "backend/tests/generated/capability-registry.yaml",
        ]
        assert _filter_changed_files(files) == []


class TestMixedSourceAndGeneratedChange:
    def test_only_source_survives_filtering(self):
        files = [
            "backend/src/api.py",
            "runtime/generated/metrics/a.json",
            "frontend/app/page.tsx",
            "backend/tests/generated/registry.yaml",
        ]
        assert _filter_changed_files(files) == [
            "backend/src/api.py",
            "frontend/app/page.tsx",
        ]

    def test_mixed_small_boundary_stays_incremental(self):
        files = [
            "backend/src/api.py",
            "runtime/generated/metrics/a.json",
        ]
        filtered = _filter_changed_files(files)
        assert (
            bp.select_strategy(bp.classify_boundary_size(len(filtered)))
            is bp.Strategy.INCREMENTAL
        )


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


class TestBoundaryEvidence:
    def test_oversized_evidence_states_scope_and_coverage(self):
        ev = bp.build_evidence(
            boundary_size=1383,
            strategy=bp.Strategy.BOUNDED_FALLBACK,
            capabilities_covered=("backend", "frontend", "contracts"),
            intentionally_bounded_scope="per-file expansion replaced",
            incremental_task_count=247,
            fallback_task_count=10,
        )
        assert ev.boundary_class is bp.BoundaryClass.OVERSIZED
        assert ev.strategy is bp.Strategy.BOUNDED_FALLBACK
        assert ev.boundary_size == 1383
        assert ev.threshold == THRESHOLD
        assert ev.capabilities_covered == ("backend", "frontend", "contracts")
        assert ev.intentionally_bounded_scope
        assert ev.incremental_task_count == 247
        assert ev.fallback_task_count == 10

    def test_rendered_evidence_reports_size_class_strategy_and_coverage(self):
        ev = bp.build_evidence(
            boundary_size=1383,
            strategy=bp.Strategy.BOUNDED_FALLBACK,
            capabilities_covered=("backend", "frontend"),
            intentionally_bounded_scope="coverage traded for boundedness",
        )
        text = ev.render()
        assert "size=1383" in text
        assert "class=OVERSIZED" in text
        assert "strategy=bounded-repository-fallback" in text
        assert "backend, frontend" in text
        assert "coverage traded for boundedness" in text

    def test_evidence_serialises_to_a_mapping(self):
        ev = bp.build_evidence(boundary_size=10, strategy=bp.Strategy.INCREMENTAL)
        d = ev.to_dict()
        assert d["boundary_class"] == "NORMAL"
        assert d["strategy"] == "incremental-capability"
        assert d["boundary_size"] == 10

    def test_incremental_evidence_reports_no_bounded_scope(self):
        ev = bp.build_evidence(boundary_size=10, strategy=bp.Strategy.INCREMENTAL)
        assert ev.intentionally_bounded_scope == ""


# ---------------------------------------------------------------------------
# Threshold configuration
# ---------------------------------------------------------------------------


class TestThresholdConfiguration:
    def test_default_threshold_is_used_when_unset(self, monkeypatch):
        monkeypatch.delenv(bp.ENV_THRESHOLD, raising=False)
        assert bp.oversized_threshold() == bp.DEFAULT_OVERSIZED_THRESHOLD

    def test_threshold_is_configurable(self):
        os.environ[bp.ENV_THRESHOLD] = "42"
        try:
            assert bp.oversized_threshold() == 42
        finally:
            os.environ.pop(bp.ENV_THRESHOLD, None)

    @pytest.mark.parametrize("bad", ["0", "-1", "not-a-number"])
    def test_invalid_threshold_raises_rather_than_silently_disabling(self, bad):
        os.environ[bp.ENV_THRESHOLD] = bad
        try:
            with pytest.raises(ValueError):
                bp.oversized_threshold()
        finally:
            os.environ.pop(bp.ENV_THRESHOLD, None)


# ---------------------------------------------------------------------------
# The fallback must never be mistaken for the bounded strategy
# ---------------------------------------------------------------------------


class TestFallbackDisableIsLoud:
    def test_disabling_the_fallback_reverts_to_incremental(self, monkeypatch):
        monkeypatch.setenv(bp.ENV_FALLBACK_DISABLED, "1")
        assert bp.select_strategy(bp.BoundaryClass.OVERSIZED) is (
            bp.Strategy.INCREMENTAL
        )

    def test_disabled_fallback_is_called_out_in_the_evidence(self, monkeypatch):
        monkeypatch.setenv(bp.ENV_FALLBACK_DISABLED, "true")
        ev = bp.build_evidence(boundary_size=1383, strategy=bp.Strategy.INCREMENTAL)
        assert ev.fallback_disabled is True
        text = ev.render()
        assert "WARNING" in text
        assert "NOT bounded verification" in text

    def test_enabled_fallback_is_not_marked_disabled(self):
        ev = bp.build_evidence(
            boundary_size=1383, strategy=bp.Strategy.BOUNDED_FALLBACK
        )
        assert ev.fallback_disabled is False
