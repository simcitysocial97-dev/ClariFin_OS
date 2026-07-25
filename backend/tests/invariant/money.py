"""Money Invariants - QEA-5 Rule: All amounts are integers representing paise."""

from __future__ import annotations

from typing import Any

PAISE_FIELDS = ("amount_paise", "balance_paise", "principal_paise", "outstanding_paise")
CONFIDENCE_BPS_FIELDS = ("confidence_bps",)


def assert_money_invariants(data: dict[str, Any]) -> None:
    """Validate that all monetary fields use integer paise.

    INVARIANT 1: All money values are integers in paise (₹1 = 100 paise).
    Negative values are valid (representing debits/expenses).

    Args:
        data: Dictionary potentially containing paise fields

    Raises:
        AssertionError: If any paise field is not an integer or is None
    """
    for key, value in data.items():
        if key.endswith("_paise") or "_paise" in key:
            if value is None:
                raise AssertionError(f"{key} is None (paise must be integer)")
            if not isinstance(value, int):
                raise AssertionError(
                    f"{key}={value} is not integer paise, got {type(value).__name__}"
                )


def assert_all_paise_integers(data: dict[str, Any]) -> None:
    """Fail if any float/None in paise fields.

    Args:
        data: Dictionary to validate

    Raises:
        AssertionError: If any paise field violates integer constraint
    """
    for key, value in data.items():
        if key.endswith("_paise") or "paise" in key:
            if not isinstance(value, int) or value is None:
                raise AssertionError(f"{key}={value} is not integer paise")
