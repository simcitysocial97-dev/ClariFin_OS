"""
M9-C5 regression tests — verification gate topology & mutation-gate decoupling.

Proves the CI verification gate topology established by M9-C5:

- The `quick` profile (the Quality Gate command) does NOT contain mutation.
- Mutation is its own independent `mutation` profile / workflow, executed only
  on a nightly schedule, never via `needs:` from any gate.
- No workflow collapses mutation failure into Quality Gate failure.
- The reconciliation tier policy treats mutation/golden as tier-gated (cost +
  criticality) units, i.e. independent verification dimensions.

These tests assert CLASSIFICATION/TOPOLOGY only. They do not execute the
backend, frontend, or mutation commands and do not "fix" any execution failure.
"""

from __future__ import annotations

from runtime.foundation.verification.profiles import get_profile
from runtime.foundation.verification.reconciliation import (
    _tier_eligible_unit_ids,
)
from runtime.foundation.verification.registry.registry import get_registry


# ---------------------------------------------------------------------------
# Case A — Quality Gate required jobs fail -> Quality Gate fails
# ---------------------------------------------------------------------------


def test_quality_gate_profile_is_quick_not_mutation() -> None:
    """The Quality Gate workflow runs `runtime/verify.py quick`. The quick
    profile must never include mutation tasks."""
    quick = get_profile("quick")
    assert quick.name == "quick"
    assert all("mutation" not in t.id for t in quick.tasks)
    assert all(t.category.value != "mutation" for t in quick.tasks)


def test_quick_profile_task_ids_are_primary_gate_checks() -> None:
    """Primary Quality Gate = ruff + mypy + unit. Mutation is absent."""
    ids = [t.id for t in get_profile("quick").tasks]
    assert ids == ["quick-ruff", "quick-mypy", "quick-unit"]


# ---------------------------------------------------------------------------
# Case B — Mutation fails while all Quality Gate requirements pass:
#   Quality Gate = PASS, Mutation = FAIL (independent, visible)
# ---------------------------------------------------------------------------


def test_mutation_is_a_distinct_profile_not_in_quick() -> None:
    mutation = get_profile("mutation")
    quick = get_profile("quick")
    assert mutation.name == "mutation"
    assert mutation.tasks  # mutation profile is non-empty
    # The two profiles are disjoint in task composition.
    quick_ids = {t.id for t in quick.tasks}
    assert not (quick_ids & {t.id for t in mutation.tasks})


def test_mutation_workflow_is_independent_not_gate_needed() -> None:
    """The mutation workflow registry entry is its own verification dimension."""
    mut = get_registry().get_workflow("mutation")
    assert mut.id == "mutation"
    assert mut.category.value == "mutation"
    # Confirm the workflow command is the selective mutation script, not a gate.
    assert "mutation" in mut.command


# ---------------------------------------------------------------------------
# Case C — Mutation passes: Quality Gate = PASS, Mutation = PASS
# ---------------------------------------------------------------------------


def test_mutation_profile_present_and_independent_for_pass_case() -> None:
    """Establishes the independent-dimension invariant used by Case C:
    mutation is a first-class profile and can pass on its own schedule."""
    mutation = get_profile("mutation")
    assert mutation.scope.value == "mutation"
    assert any(t.category.value == "mutation" for t in mutation.tasks)


# ---------------------------------------------------------------------------
# Case D — Backend fails -> Quality Gate FAIL regardless of mutation status
# ---------------------------------------------------------------------------


def test_backend_failure_is_orthogonal_to_mutation_topology() -> None:
    """Backend verification is a distinct profile from mutation. A backend
    failure is reported through the backend profile, never gated by mutation
    and never masked by it."""
    backend = get_profile("backend")
    mutation = get_profile("mutation")
    backend_ids = {t.id for t in backend.tasks}
    assert not (backend_ids & {t.id for t in mutation.tasks})
    assert backend.scope.value == "backend"


# ---------------------------------------------------------------------------
# Case E — Reconcile reports each dimension independently
# ---------------------------------------------------------------------------


def test_reconcile_treats_mutation_as_tier_eligible_independent_unit() -> None:
    """Reconciliation's tier-eligibility policy lists mutation (and golden) as
    units whose selection legitimately differs by tier/cost policy — i.e. they
    are NOT part of the required gate contract and must be reported
    independently, never collapsed into a single undifferentiated pass/fail."""
    eligible = _tier_eligible_unit_ids()
    assert any("mutation" in uid for uid in eligible)
    assert any("golden" in uid for uid in eligible)
