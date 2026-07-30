"""Account invariant tests."""

from __future__ import annotations

from invariants.account import (  # noqa: F401,F403
    assert_account_closed_valid,
    assert_account_state_valid,
    assert_owner_scope_valid,
)


def test_account_invariant_module_exists() -> None:
    """Verify account invariant module functions are callable."""
    assert callable(assert_account_state_valid)
    assert callable(assert_owner_scope_valid)
    assert callable(assert_account_closed_valid)
    assert_account_state_valid({"status": "active", "credit_limit_paise": 1000})
    assert_owner_scope_valid({"owner_id": 1, "scope": "individual"})
    assert_account_closed_valid(is_active=False, last_transaction_date="2024-01-01")
