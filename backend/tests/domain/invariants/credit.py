"""Credit Card Invariants - Utilization, EMI, and statement validation."""
from __future__ import annotations

from typing import Any


def assert_credit_invariants(card_data: dict[str, Any]) -> None:
    """Validate credit card data invariants.

    INVARIANT: Utilization percentage must be 0-100.
    INVARIANT: Credit limits and balances must be non-negative.
    INVARIANT: Available credit = limit - outstanding.

    Args:
        card_data: Credit card dictionary

    Raises:
        AssertionError: If credit card violates invariants
    """
    from .money import assert_money_invariants

    assert_money_invariants(card_data)

    # Limit must be positive
    if "credit_limit_paise" in card_data:
        if card_data["credit_limit_paise"] < 0:
            raise AssertionError("credit_limit_paise cannot be negative")

    # Outstanding cannot exceed limit
    if "credit_limit_paise" in card_data and "outstanding_paise" in card_data:
        if card_data["outstanding_paise"] > card_data["credit_limit_paise"]:
            raise AssertionError(
                f"outstanding_paise ({card_data['outstanding_paise']}) "
                f"> credit_limit_paise ({card_data['credit_limit_paise']})"
            )


def assert_utilization_valid(available_credit: int, limit: int, outstanding: int) -> None:
    """Validate credit card utilization calculations.

    INVARIANT: Utilization = outstanding / limit.
    INVARIANT: Available = limit - outstanding.

    Args:
        available_credit: Calculated available credit
        limit: Credit limit
        outstanding: Outstanding balance

    Raises:
        AssertionError: If utilization invalid
    """
    if limit < 0:
        raise AssertionError("Credit limit cannot be negative")
    if outstanding < 0:
        raise AssertionError("Outstanding cannot be negative")
    if available_credit != limit - outstanding:
        raise AssertionError(
            f"Available credit mismatch: {available_credit} != {limit} - {outstanding}"
        )
    if limit > 0:
        util = outstanding / limit
        if util < 0 or util > 1:
            raise AssertionError(f"Utilization {util} out of range (0-1)")


def assert_emi_conversion_valid(emi_result: dict[str, Any], amount_paise: int, tenure_months: int) -> None:
    """Validate EMI conversion result invariants.

    INVARIANT: EMI must be positive.
    INVARIANT: Total repayment >= principal.
    INVARIANT: Total interest >= 0.

    Args:
        emi_result: Result from EMI calculation
        amount_paise: Original principal amount
        tenure_months: Tenure in months

    Raises:
        AssertionError: If EMI calculation violates invariants
    """
    from .money import assert_money_invariants

    assert_money_invariants(emi_result)

    if emi_result.get("emi_paise", 0) <= 0:
        raise AssertionError("EMI must be positive")

    if emi_result.get("total_repayment_paise", 0) < amount_paise:
        raise AssertionError("Total repayment must be >= principal")

    total_interest = emi_result.get("total_interest_paise", 0)
    if total_interest < 0:
        raise AssertionError("Total interest must be non-negative")


def assert_minimum_due_valid(min_due: int, total_outstanding: int) -> None:
    """Validate minimum due calculation.

    INVARIANT: Minimum due must be positive when balance > 0.

    Args:
        min_due: Calculated minimum due
        total_outstanding: Total outstanding balance

    Raises:
        AssertionError: If minimum due invalid
    """
    if total_outstanding > 0 and min_due <= 0:
        raise AssertionError(f"Minimum due {min_due} must be positive when balance > 0")
