"""
Balance Engine - Pure calculation module
========================================
Balance calculations for accounts.

All monetary values in paise (integer).
All rates in basis points (integer).

Provides factual balance metrics only — no recommendations.
"""

from decimal import ROUND_HALF_UP, Decimal


def compute_average_balance(daily_balances: list[int]) -> int:
    """
    Compute average balance from daily snapshots.

    Args:
        daily_balances: List of daily balance values in paise.

    Returns:
        Average balance in paise (integer, rounded using ROUND_HALF_UP).

    INVARIANT 1: Empty list returns 0.
    INVARIANT 2: All values treated as paise.
    INVARIANT 3: Uses ROUND_HALF_UP for rounding.
    """
    if not daily_balances:
        return 0

    total = sum(daily_balances)
    count = len(daily_balances)

    if count == 0:
        return 0

    avg_decimal = Decimal(total) / Decimal(count)
    return int(avg_decimal.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def compute_balance_change(
    opening_balance_paise: int, closing_balance_paise: int
) -> int:
    """
    Compute absolute balance change.

    Args:
        opening_balance_paise: Opening balance in paise.
        closing_balance_paise: Closing balance in paise.

    Returns:
        Change in paise (can be negative, zero, or positive).

    INVARIANT 1: Change = closing - opening.
    INVARIANT 2: Can be negative (decline).
    """
    return closing_balance_paise - opening_balance_paise


def compute_balance_growth_percentage(
    previous_balance_paise: int, current_balance_paise: int
) -> int:
    """
    Compute balance growth rate as basis points.

    Args:
        previous_balance_paise: Previous balance in paise.
        current_balance_paise: Current balance in paise.

    Returns:
        Growth rate in basis points (100 bps = 1%).
        Returns 0 if previous_balance is 0.

    INVARIANT 1: Basis points = (change / previous) * 10000.
    INVARIANT 2: Zero previous balance returns 0 bps (avoid division by zero).
    INVARIANT 3: Uses ROUND_HALF_UP for rounding.
    """
    if previous_balance_paise == 0:
        # No previous balance - growth undefined, return 0
        return 0

    change = current_balance_paise - previous_balance_paise
    growth_decimal = Decimal(change) * Decimal(10000) / Decimal(previous_balance_paise)

    return int(growth_decimal.quantize(Decimal(1), rounding=ROUND_HALF_UP))
