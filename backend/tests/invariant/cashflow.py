"""Cashflow Invariants - Mathematical correctness: income - expense = surplus."""

from __future__ import annotations

from typing import Any


def assert_cashflow_invariants(cashflow_rows: list[dict[str, Any]]) -> None:
    """Validate cashflow mathematical identity.

    INVARIANT 2: income_paise - expense_paise == surplus_paise (±1 paise tolerance for rounding).

    Args:
        cashflow_rows: List of cashflow dictionaries with income/expense/surplus fields

    Raises:
        AssertionError: If surplus calculation is incorrect
    """
    for row in cashflow_rows:
        income = row.get("income_paise", 0) or 0
        expense = row.get("expense_paise", 0) or 0
        surplus = row.get("surplus_paise", 0) or 0
        expected = income - expense
        if abs(surplus - expected) > 1:
            raise AssertionError(
                f"surplus_paise={surplus}, expected {expected} (income={income}, expense={expense})"
            )


def assert_cashflow_result_invariants(result: dict[str, Any]) -> None:
    """Validate cashflow engine result structure and invariants.

    Args:
        result: Result dictionary from cashflow engine

    Raises:
        AssertionError: If result violates cashflow invariants
    """
    # All monetary outputs must use integer paise

    for key in ["cash_surplus", "true_savings", "liability_adjusted_savings", "net_worth_impact"]:
        if key in result and result[key] is not None:
            if not isinstance(result[key], int):
                raise AssertionError(f"{key}={result[key]} must be integer paise, got {type(result[key]).__name__}")

    # Month classification must be valid
    valid_classifications = {"surplus", "deficit_covered_by_credit", "deficit"}
    if "month_classification" in result:
        if result["month_classification"] not in valid_classifications:
            raise AssertionError(
                f"Invalid month_classification: {result['month_classification']}"
            )

    # Credit dependency ratio must be non-negative
    if "credit_dependency_ratio" in result and result["credit_dependency_ratio"] is not None:
        if result["credit_dependency_ratio"] < 0:
            raise AssertionError("credit_dependency_ratio must be non-negative")
