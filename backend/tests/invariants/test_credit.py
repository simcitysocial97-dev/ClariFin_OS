"""Credit invariant tests."""

from __future__ import annotations

from invariants.credit import (  # noqa: F401,F403
    assert_credit_invariants,
    assert_emi_conversion_valid,
    assert_minimum_due_valid,
    assert_utilization_valid,
)


def test_credit_invariant_module_exists() -> None:
    """Verify credit invariant module functions are callable."""
    assert callable(assert_credit_invariants)
    assert callable(assert_utilization_valid)
    assert callable(assert_emi_conversion_valid)
    assert callable(assert_minimum_due_valid)
    assert_credit_invariants({"credit_limit_paise": 100000, "outstanding_paise": 50000})
    assert_utilization_valid(available_credit=50000, limit=100000, outstanding=50000)
