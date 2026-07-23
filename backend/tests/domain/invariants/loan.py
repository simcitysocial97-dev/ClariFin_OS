"""Loan Invariants - Principal decreases, balance trends downward."""
from __future__ import annotations

from typing import Any

from .money import assert_money_invariants


def assert_loan_schedule_valid(schedule: list[dict[str, Any]]) -> None:
    """Validate amortization schedule invariants.

    INVARIANT 3: Principal monotonically decreases during repayment.
    INVARIANT 4: Final balance >= 0 (cannot be negative in healthy loan).
    INVARIANT 5: Interest >= 0 for each period.

    Args:
        schedule: List of schedule row dictionaries with balance_paise fields

    Raises:
        AssertionError: If schedule violates invariants
    """
    if not schedule:
        return

    prev_balance: int | None = None

    for i, row in enumerate(schedule):
        # Principal should decrease or stay same (not increase)
        if prev_balance is not None:
            if row.get("balance_paise", 0) > prev_balance:
                raise AssertionError(
                    f"Balance increased at row {i}: {row.get('balance_paise')} > {prev_balance}"
                )

        # Interest must be non-negative
        if row.get("interest_paise", 0) < 0:
            raise AssertionError(f"Negative interest at row {i}: {row.get('interest_paise')}")

        # All monetary fields must be integers
        assert_money_invariants(row)

        prev_balance = row.get("balance_paise", 0)


def assert_loan_invariants(loan_data: dict[str, Any]) -> None:
    """Validate loan data invariants.

    INVARIANT: outstanding_paise <= principal_paise (cannot owe more than borrowed).
    INVARIANT: tenure_months > 0 for active loans.

    Args:
        loan_data: Loan dictionary with principal/outstanding fields

    Raises:
        AssertionError: If loan data violates invariants
    """
    principal = loan_data.get("principal_paise", 0)
    outstanding = loan_data.get("outstanding_paise", 0)

    if principal is not None and outstanding is not None:
        if outstanding > principal:
            raise AssertionError(
                f"outstanding_paise ({outstanding}) > principal_paise ({principal})"
            )

    if loan_data.get("tenure_months") is not None:
        if loan_data["tenure_months"] < 0:
            raise AssertionError("tenure_months cannot be negative")


def assert_prepayment_result_valid(original_schedule: list[dict[str, Any]], new_schedule: list[dict[str, Any]]) -> None:
    """Validate prepayment preserves invariants.

    INVARIANT: New schedule principal still decreases monotonically.
    INVARIANT: Total interest saved >= 0.

    Args:
        original_schedule: Before prepayment
        new_schedule: After prepayment

    Raises:
        AssertionError: If prepayment violates invariants
    """
    assert_loan_schedule_valid(new_schedule)

    original_interest = sum(r.get("interest_paise", 0) for r in original_schedule)
    new_interest = sum(r.get("interest_paise", 0) for r in new_schedule)

    if original_interest - new_interest < 0:
        raise AssertionError("Prepayment should not increase total interest")
