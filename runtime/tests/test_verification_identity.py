"""Verification Identity Spine — Model Tests (VEA-2 Phase 2, M1)

Tests for the `unit_id` + `provenance` identity fields added to `VerificationStep`
and `ExecutionResult`.

Why these tests exist
---------------------
Phase 2 establishes a durable join key from plan → execution → evidence. Before M1 there
was **no join key between planning and execution at all**: the intelligence pipeline
produced `VerificationUnit` objects carrying C11 provenance but never executed anything,
while the orchestrator executed commands but carried no provenance.

These tests protect two architectural invariants, not implementation details:

1. **Backwards compatibility is absolute.** The fields are optional and defaulted, so
   every pre-existing construction site (2 for `VerificationStep`, 5 for
   `ExecutionResult`) keeps working untouched. If this breaks, 291 baseline tests break.

2. **Identity survives construction verbatim.** A `unit_id` that silently changes,
   normalises or gets dropped would recreate the very defect class Phase 2 exists to
   remove (attribution by guessing). `None` must stay `None` — an absent unit is a
   legitimate, visible `UNMAPPED` outcome, never inferred away.
"""

from __future__ import annotations

import dataclasses

import pytest

from runtime.foundation.verification.models import (
    ExecutionResult,
    VerificationCategory,
    VerificationScope,
    VerificationStatus,
    VerificationStep,
    VerificationTarget,
)


# C11 provenance shape, as emitted by VerificationUnit.to_dict()["provenance"].
C11_PROVENANCE = {
    "capabilities": ["capability:useLoansCapability"],
    "impact_kinds": ["engine", "engine_module"],
    "source": "chain-map+blast-radius",
}


def _target(target_id: str = "target-loan-engine") -> VerificationTarget:
    """Minimal valid target; the identity spine does not depend on target content."""
    return VerificationTarget(
        id=target_id,
        name="Loan Engine",
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.BACKEND,
    )


def _step(**overrides) -> VerificationStep:
    kwargs = {
        "id": "step-0001",
        "target": _target(),
        "order": 1,
        "command": "bash .github/scripts/run_backend_verification.sh",
    }
    kwargs.update(overrides)
    return VerificationStep(**kwargs)


def _result(**overrides) -> ExecutionResult:
    kwargs = {
        "task_id": "step-0001",
        "command": "bash .github/scripts/run_backend_verification.sh",
        "status": VerificationStatus.PASSED,
        "exit_code": 0,
        "duration_seconds": 77.0,
        "stdout_path": "/tmp/stdout.log",
        "stderr_path": "/tmp/stderr.log",
    }
    kwargs.update(overrides)
    return ExecutionResult(**kwargs)


class TestBackwardsCompatibility:
    """The new fields must be invisible to every pre-existing construction site."""

    def test_step_constructs_without_new_fields(self):
        """NEGATIVE TEST: omitting the new fields must not raise.

        This is the guard for the 2 pre-existing VerificationStep sites in planner.py.
        """
        step = _step()  # constructed with no unit_id, no provenance
        assert step.id == "step-0001"

    def test_result_constructs_without_new_fields(self):
        """NEGATIVE TEST: omitting the new fields must not raise.

        This is the guard for the 5 pre-existing ExecutionResult sites in executor.py.
        """
        result = _result()  # constructed with no unit_id, no provenance
        assert result.task_id == "step-0001"

    def test_step_defaults_are_none_and_empty_dict(self):
        step = _step()
        assert step.unit_id is None
        assert step.provenance == {}

    def test_result_defaults_are_none_and_empty_dict(self):
        result = _result()
        assert result.unit_id is None
        assert result.provenance == {}

    def test_default_provenance_is_not_shared_between_instances(self):
        """A mutable default shared across instances would leak provenance between runs."""
        a = _step(id="step-0001")
        b = _step(id="step-0002")
        assert a.provenance is not b.provenance


class TestIdentityRoundTrip:
    """A step/result constructed with identity must retain it verbatim."""

    def test_step_retains_unit_id_and_provenance(self):
        step = _step(unit_id="backend-unit", provenance=C11_PROVENANCE)
        assert step.unit_id == "backend-unit"
        assert step.provenance == C11_PROVENANCE

    def test_result_retains_unit_id_and_provenance(self):
        result = _result(unit_id="backend-unit", provenance=C11_PROVENANCE)
        assert result.unit_id == "backend-unit"
        assert result.provenance == C11_PROVENANCE

    def test_provenance_carries_the_full_c11_shape(self):
        """Provenance must mirror C11: capabilities, impact_kinds, source."""
        step = _step(unit_id="frontend-typecheck-build", provenance=C11_PROVENANCE)
        assert set(step.provenance) == {"capabilities", "impact_kinds", "source"}
        assert step.provenance["source"] == "chain-map+blast-radius"
        assert step.provenance["impact_kinds"] == ["engine", "engine_module"]

    def test_unit_id_is_not_normalised_or_rewritten(self):
        """PROVEN over PROBABLE: the join key must survive byte-for-byte.

        Any normalisation (casing, stripping, slugifying) would silently break the join
        or, worse, make two distinct units collide.
        """
        for unit_id in (
            "unit-targeted",
            "contracts-schemathesis",
            "frontend-typecheck-build",
            "runtime-self-test",
        ):
            assert _step(unit_id=unit_id).unit_id == unit_id
            assert _result(unit_id=unit_id).unit_id == unit_id

    def test_step_identity_transfers_to_result_unchanged(self):
        """The M3 contract in miniature: result identity == step identity."""
        step = _step(unit_id="backend-unit", provenance=C11_PROVENANCE)
        result = _result(
            task_id=step.id, unit_id=step.unit_id, provenance=step.provenance
        )
        assert result.unit_id == step.unit_id
        assert result.provenance == step.provenance


class TestImmutabilityPreserved:
    """frozen=True, slots=True must still hold after adding the fields."""

    @pytest.mark.parametrize("factory", [_step, _result])
    def test_instances_are_frozen(self, factory):
        instance = factory(unit_id="backend-unit")
        with pytest.raises(dataclasses.FrozenInstanceError):
            instance.unit_id = "mutated"

    @pytest.mark.parametrize("cls", [VerificationStep, ExecutionResult])
    def test_slots_are_enabled(self, cls):
        """slots=True prevents attribute typos silently creating new attributes."""
        assert hasattr(cls, "__slots__")
        assert "unit_id" in cls.__slots__
        assert "provenance" in cls.__slots__

    @pytest.mark.parametrize("factory", [_step, _result])
    def test_cannot_set_undeclared_attribute(self, factory):
        """A typo'd field name must be rejected, never silently absorbed.

        Note: for a frozen+slots dataclass CPython raises TypeError (not AttributeError)
        for an undeclared name, because the generated frozen __setattr__ is reached
        before the slots machinery. The exact type is incidental; what matters is that
        the assignment does not succeed.
        """
        instance = factory()
        with pytest.raises((AttributeError, TypeError, dataclasses.FrozenInstanceError)):
            instance.unit_ID = "typo"
        assert not hasattr(instance, "unit_ID")


class TestUnmappedIsLegitimate:
    """UNKNOWN over GUESSED: an absent unit is a real outcome, not an error."""

    def test_none_unit_id_is_a_valid_state_not_an_error(self):
        step = _step(unit_id=None)
        result = _result(unit_id=None)
        assert step.unit_id is None
        assert result.unit_id is None

    def test_none_unit_id_is_distinguishable_from_empty_string(self):
        """`None` means "no mapping decision reached"; "" would be a bogus join key."""
        assert _step(unit_id=None).unit_id is None
        assert _step(unit_id="").unit_id == ""
        assert _step(unit_id="").unit_id is not None
