"""Unit ↔ Registry Mapping Tests (VEA-2 Phase 2, M2)

Tests for `UNIT_TO_WORKFLOW`, `resolve_unit_workflow()` and the `UNMAPPED` sentinel.

Why these tests exist
---------------------
The intelligence pipeline produces `VerificationUnit` objects carrying C11 provenance
but never executes anything. The orchestrator executes `run_*.sh` scripts but carries no
provenance. This mapping is the explicit join between the two.

The hard invariant these tests enforce:

    PROVEN   over  PROBABLE
    UNKNOWN  over  GUESSED

Any join by keyword match, substring match, category inference or "first entry wins" is
prohibited — that is the defect class that produced E-4, where
`_find_chain_for_failure()` returned the first chain-map entry regardless of which test
actually failed. These tests are written to fail loudly if such inference is ever
reintroduced.

The coverage test is the load-bearing one: it fails CI when a new optimizer unit is added
without a mapping decision. **That is its purpose**, not an inconvenience.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from runtime.foundation.verification.registry import (
    UNIT_TO_WORKFLOW,
    UNMAPPED,
    VerificationRegistry,
    resolve_unit_workflow,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OPTIMIZER = REPO_ROOT / "runtime/foundation/intelligence/platform/optimizer.py"

#: The closed set of optimizer unit IDs, as specified by the Phase 2 plan §M2.
#: Duplicated here deliberately: if the optimizer changes, the discovery test below
#: detects the drift against this literal, rather than both sides moving together
#: silently.
EXPECTED_UNIT_IDS = frozenset(
    {
        "unit-targeted",
        "contracts-schemathesis",
        "backend-integration",
        "backend-unit",
        "frontend-unit",
        "frontend-typecheck-build",
        "playwright-e2e",
        "runtime-self-test",
        "mutation-run",
        "golden-regression",
    }
)

#: Units that the optimizer only ever *skips* — they are cost-gated (>= 600s) and
#: require an explicit request, so they never appear in `selected`.
COST_GATED_UNITS = frozenset({"mutation-run", "golden-regression"})


def _discover_optimizer_unit_ids() -> set[str]:
    """Scrape the optimizer's declared unit IDs from source.

    Deliberately source-derived rather than hard-coded, so that adding a unit to the
    optimizer is *detected* rather than assumed. The two cost-gated suites are declared
    in a loop over tuples rather than as `id="..."` kwargs, so both forms are matched.
    """
    source = OPTIMIZER.read_text()
    ids = set(re.findall(r'\bid="([a-z0-9-]+)"', source))
    # Heavy suites declared as ("mutation-run", "mutation", ...) tuples.
    ids |= set(re.findall(r'\(\s*"([a-z0-9-]+)",\s*"(?:mutation|golden)"', source))
    return ids


class TestClosedUnitSet:
    """The unit set must stay closed and known."""

    def test_optimizer_declares_exactly_the_expected_units(self):
        """Drift detector: the optimizer's unit set must match the plan's closed set.

        If this fails, a unit was added or removed in the optimizer. That is a mapping
        decision that must be made consciously, not absorbed silently.
        """
        assert _discover_optimizer_unit_ids() == set(EXPECTED_UNIT_IDS)

    def test_expected_set_has_ten_units(self):
        assert len(EXPECTED_UNIT_IDS) == 10


class TestMappingCoverage:
    """COVERAGE TEST — the milestone's central guard."""

    def test_every_optimizer_unit_has_a_mapping_decision(self):
        """Every one of the 10 unit IDs must appear in the table.

        A unit may map to a registry workflow *or* to an intentional UNMAPPED, but it
        may not be absent. This test exists to fail CI when a new optimizer unit is
        added without a mapping decision.
        """
        missing = sorted(set(EXPECTED_UNIT_IDS) - set(UNIT_TO_WORKFLOW))
        assert not missing, (
            f"Optimizer unit(s) {missing} have no mapping decision in UNIT_TO_WORKFLOW. "
            "Add an explicit row (a workflow ID, or UNMAPPED if there is genuinely no "
            "executed counterpart). Do not infer the mapping."
        )

    def test_coverage_is_derived_from_the_optimizer_not_just_the_literal(self):
        """Same guard, but sourced from the optimizer, closing the drift loophole."""
        missing = sorted(_discover_optimizer_unit_ids() - set(UNIT_TO_WORKFLOW))
        assert not missing, f"Unmapped optimizer units: {missing}"

    def test_table_contains_no_unknown_units(self):
        """The table must not accumulate rows for units that no longer exist."""
        stale = sorted(set(UNIT_TO_WORKFLOW) - set(EXPECTED_UNIT_IDS))
        assert not stale, f"UNIT_TO_WORKFLOW has stale rows: {stale}"


class TestMappingTargetsAreReal:
    """A mapping is worthless if it points at a workflow that does not exist."""

    def test_every_mapped_workflow_is_registered(self):
        registry = VerificationRegistry()
        registry.load()
        for unit_id, workflow_id in sorted(UNIT_TO_WORKFLOW.items()):
            if workflow_id == UNMAPPED:
                continue
            assert registry.get_workflow(workflow_id) is not None, (
                f"Unit '{unit_id}' maps to workflow '{workflow_id}', "
                "which is not registered."
            )

    def test_mapped_workflows_have_an_executable_command(self):
        """The join is only useful if the target actually executes something."""
        registry = VerificationRegistry()
        registry.load()
        for unit_id, workflow_id in sorted(UNIT_TO_WORKFLOW.items()):
            if workflow_id == UNMAPPED:
                continue
            workflow = registry.get_workflow(workflow_id)
            assert workflow is not None and workflow.command, (
                f"Unit '{unit_id}' maps to workflow '{workflow_id}' with no command."
            )

    def test_get_workflow_for_unit_returns_the_workflow_object(self):
        registry = VerificationRegistry()
        workflow = registry.get_workflow_for_unit("backend-unit")
        assert workflow is not None
        assert workflow.id == "backend"


class TestManyToOneIsExplicit:
    """Many-to-one is permitted, but it must be a stated decision."""

    def test_both_backend_unit_units_resolve_to_the_backend_script(self):
        """`unit-targeted` and `backend-unit` deliberately share one executed script."""
        assert resolve_unit_workflow("unit-targeted") == "backend"
        assert resolve_unit_workflow("backend-unit") == "backend"

    def test_both_frontend_units_resolve_to_the_frontend_script(self):
        """One script runs lint+typecheck+build+test behind a single exit code."""
        assert resolve_unit_workflow("frontend-unit") == "frontend"
        assert resolve_unit_workflow("frontend-typecheck-build") == "frontend"

    def test_many_to_one_collapses_are_exactly_the_documented_ones(self):
        """Guards against an unnoticed new collapse appearing.

        An undocumented many-to-one collapse means two independently-justified units
        became indistinguishable in evidence without anyone deciding that was correct.
        """
        by_workflow: dict[str, list[str]] = {}
        for unit_id, workflow_id in UNIT_TO_WORKFLOW.items():
            by_workflow.setdefault(workflow_id, []).append(unit_id)
        collapsed = {
            workflow_id: sorted(units)
            for workflow_id, units in by_workflow.items()
            if len(units) > 1
        }
        assert collapsed == {
            "backend": ["backend-unit", "unit-targeted"],
            "frontend": ["frontend-typecheck-build", "frontend-unit"],
        }


class TestCostGatedUnits:
    """Cost-gated units must resolve without error, per plan M2."""

    @pytest.mark.parametrize("unit_id", sorted(COST_GATED_UNITS))
    def test_cost_gated_unit_resolves_without_error(self, unit_id):
        resolved = resolve_unit_workflow(unit_id)
        assert resolved != UNMAPPED
        assert isinstance(resolved, str) and resolved

    def test_mutation_and_golden_map_to_their_own_workflows(self):
        assert resolve_unit_workflow("mutation-run") == "mutation"
        assert resolve_unit_workflow("golden-regression") == "golden"

    def test_cost_gated_units_are_never_selected_by_the_optimizer(self):
        """Documents *why* these rows exist despite never being selected.

        They map so that an explicitly-requested heavy run can still be joined to unit
        identity.
        """
        source = OPTIMIZER.read_text()
        for unit_id in sorted(COST_GATED_UNITS):
            assert f'VerificationUnit(\n                id="{unit_id}"' not in source


class TestUnmappedIsReachableAndNeverGuessed:
    """UNKNOWN over GUESSED — the §1 hard invariant."""

    def test_unknown_unit_returns_unmapped(self):
        assert resolve_unit_workflow("does-not-exist") == UNMAPPED

    def test_unknown_unit_does_not_raise(self):
        resolve_unit_workflow("totally-unknown-unit")  # must not raise

    @pytest.mark.parametrize(
        "unit_id",
        [
            "",
            "backend",  # a registry workflow ID, not a unit ID
            "backend-",
            "BACKEND-UNIT",  # wrong case must not match
            "backend-unit-extra",
            "unit",
            "frontend",
        ],
    )
    def test_near_miss_ids_are_unmapped_not_guessed(self, unit_id):
        """PROHIBITED: substring/prefix/case-insensitive matching.

        `backend-unit-extra` contains `backend-unit`; `BACKEND-UNIT` differs only in
        case; `backend` is a real *workflow* ID. A lookup that "helpfully" resolved any
        of these would be inference, and would silently misattribute failures.
        """
        assert resolve_unit_workflow(unit_id) == UNMAPPED

    def test_unmapped_is_a_distinct_sentinel_not_none_or_empty(self):
        """UNMAPPED must be visible in reports, so it cannot be falsy."""
        assert UNMAPPED == "UNMAPPED"
        assert UNMAPPED is not None
        assert bool(UNMAPPED) is True

    def test_unmapped_is_not_a_registered_workflow_id(self):
        """The sentinel must never collide with a real workflow."""
        registry = VerificationRegistry()
        registry.load()
        assert registry.get_workflow(UNMAPPED) is None

    def test_get_workflow_for_unit_returns_none_for_unknown_unit(self):
        registry = VerificationRegistry()
        assert registry.get_workflow_for_unit("does-not-exist") is None


class TestDeterminism:
    """The join must be stable; attribution built on it must be reproducible."""

    def test_resolution_is_deterministic(self):
        for unit_id in sorted(EXPECTED_UNIT_IDS) + ["unknown-unit"]:
            results = {resolve_unit_workflow(unit_id) for _ in range(5)}
            assert len(results) == 1

    def test_registry_accessor_agrees_with_module_function(self):
        registry = VerificationRegistry()
        for unit_id in sorted(EXPECTED_UNIT_IDS) + ["unknown-unit"]:
            assert registry.resolve_unit(unit_id) == resolve_unit_workflow(unit_id)
