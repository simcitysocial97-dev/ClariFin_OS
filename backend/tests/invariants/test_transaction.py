"""Transaction invariant tests."""

from __future__ import annotations

from invariants.transaction import (  # noqa: F401,F403
    assert_amount_sign_convention,
    assert_reconciliation_match_valid,
    assert_transaction_ordering_valid,
)


def test_transaction_invariant_module_exists() -> None:
    """Verify transaction invariant module functions are callable."""
    assert callable(assert_transaction_ordering_valid)
    assert callable(assert_amount_sign_convention)
    assert callable(assert_reconciliation_match_valid)
    assert_transaction_ordering_valid(
        [
            {"date_iso": "2024-01-01", "amount_paise": 1000},
            {"date_iso": "2024-01-02", "amount_paise": 2000},
        ]
    )
    assert_reconciliation_match_valid({"amount_paise": 1000, "confidence_bps": 5000})
