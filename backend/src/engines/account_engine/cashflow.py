"""
Cashflow Engine - Pure calculation module
=========================================
Deterministic cash flow calculations.

All monetary values in paise (integer).
All rates in basis points (integer).

Provides factual cash flow metrics only — no recommendations.
"""

from decimal import ROUND_HALF_UP, Decimal


def compute_net_cash_flow(credits_paise: int, debits_paise: int) -> int:
    """
    Compute net cash flow for a period.

    Args:
        credits_paise: Total credits in paise.
        debits_paise: Total debits in paise.

    Returns:
        Net flow in paise (credits - debits, can be negative).

    INVARIANT 1: Net flow = credits - debits.
    INVARIANT 2: Can be positive (inflow) or negative (outflow).
    """
    return credits_paise - debits_paise


def compute_cash_flow_rate(net_flow_paise: int, days: int) -> int:
    """
    Compute average daily cash flow rate.

    Args:
        net_flow_paise: Net cash flow in paise.
        days: Number of days in the period.

    Returns:
        Average daily flow in paise/day (rounded using ROUND_HALF_UP).

    Raises:
        ValueError: If days is zero or negative.

    INVARIANT 1: Rate = net_flow / days.
    INVARIANT 2: Days must be positive.
    INVARIANT 3: Uses ROUND_HALF_UP for rounding.
    """
    if days <= 0:
        raise ValueError("days must be positive")

    rate_decimal = Decimal(net_flow_paise) / Decimal(days)
    return int(rate_decimal.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def compute_income_expense_ratio(income_paise: int, expense_paise: int) -> int:
    """
    Compute income to expense ratio as basis points.

    Args:
        income_paise: Total income in paise.
        expense_paise: Total expenses in paise.

    Returns:
        Ratio in basis points (10000 bps = income equals expenses).
        Returns 0 if expense is zero (avoid division by zero).

    INVARIANT 1: Ratio = (income / expense) * 10000.
    INVARIANT 2: Zero expense returns 0 bps.
    INVARIANT 3: Uses ROUND_HALF_UP for rounding.
    """
    if expense_paise == 0:
        # No expenses - ratio undefined, return 0
        return 0

    ratio_decimal = Decimal(income_paise) * Decimal(10000) / Decimal(expense_paise)
    return int(ratio_decimal.quantize(Decimal(1), rounding=ROUND_HALF_UP))
