"""Cashflow stability metrics for behaviour engine.

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.
"""

from decimal import Decimal

from .utils import _coefficient_of_variation


def compute_income_stability(monthly_incomes_paise: list[int]) -> Decimal:
    """
    Compute income stability score using median and variance.

    A stable income has low variance relative to its median.
    Score approaches 1 for very stable income, lower for volatile income.

    Parameters:
        monthly_incomes_paise: List of monthly income values in paise.
                              Only complete months should be passed.
                              This function does not impute missing months.

    Returns:
        Decimal stability score between 0 and 1.
        Returns Decimal('1') for empty/single month (assumed stable).
    """
    if len(monthly_incomes_paise) < 2:
        return Decimal('1')

    cv = _coefficient_of_variation(monthly_incomes_paise)
    # Stability = 1 - normalized CV (max CV considered is 1.0)
    stability = Decimal('1') - min(Decimal('1'), cv)
    return max(Decimal('0'), stability)


def compute_expense_stability(monthly_expenses_paise: list[int]) -> Decimal:
    """
    Compute expense stability score using median and variance.

    A stable expense pattern has low variance relative to its median.
    Regular expenses (rent, utilities) create stability.
    Score approaches 1 for very stable expenses, lower for volatile.

    Parameters:
        monthly_expenses_paise: List of monthly expense values in paise.
                               Only complete months should be passed.
                               This function does not impute missing months.

    Returns:
        Decimal stability score between 0 and 1.
        Returns Decimal('1') for empty/single month (assumed stable).
    """
    if len(monthly_expenses_paise) < 2:
        return Decimal('1')

    cv = _coefficient_of_variation(monthly_expenses_paise)
    # Stability = 1 - normalized CV (max CV considered is 1.0)
    stability = Decimal('1') - min(Decimal('1'), cv)
    return max(Decimal('0'), stability)


def compute_cashflow_stability_index(
    monthly_incomes_paise: list[int],
    monthly_expenses_paise: list[int],
) -> Decimal:
    """
    Compute overall cashflow stability index.

    Formula: (income_stability + expense_stability) / 2

    Parameters:
        monthly_incomes_paise: List of monthly income values in paise.
        monthly_expenses_paise: List of monthly expense values in paise.

    Returns:
        Decimal stability index between 0 and 1.
        Higher values indicate more predictable cashflow patterns.

    Note:
        Future versions may introduce weighting between income and expense stability.
        Current implementation uses simple average for transparency.
    """
    income_stability = compute_income_stability(monthly_incomes_paise)
    expense_stability = compute_expense_stability(monthly_expenses_paise)

    return (income_stability + expense_stability) / 2
