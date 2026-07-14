# Cashflow invariant: income - expense == surplus
import pytest


def assert_surplus_balances(cashflow_rows):
    """Income - expense == surplus ±1 paise (rounding tolerance)."""
    for row in cashflow_rows:
        income = row.get("income_paise", 0)
        expense = row.get("expense_paise", 0)
        surplus = row.get("surplus_paise", 0)
        expected = income - expense
        if abs(surplus - expected) > 1:
            raise AssertionError(f"surplus_paise={surplus}, expected {expected}")


def test_cashflow_invariants():
    rows = [{"income_paise": 500, "expense_paise": 300, "surplus_paise": 200}]
    assert_surplus_balances(rows)  # Should pass