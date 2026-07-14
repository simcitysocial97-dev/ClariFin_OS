# Loan invariant: principal decreases, final balance zero
import pytest


def assert_schedule_valid(schedule):
    """Principal decreases monotonically, final balance == 0."""
    balances = [row.get("balance_paise", 0) for row in schedule]
    for i in range(1, len(balances)):
        if balances[i] > balances[i - 1]:
            raise AssertionError(f"Balance increased at row {i}")
    if balances and balances[-1] != 0:
        raise AssertionError(f"Final balance {balances[-1]} != 0")


def test_loan_invariants():
    schedule = [
        {"balance_paise": 100000},
        {"balance_paise": 90000},
        {"balance_paise": 0},
    ]
    assert_schedule_valid(schedule)  # Should pass