"""
Balance History Engine - Pure calculation module
===============================================
Balance history analysis.

All monetary values in paise (integer).

Provides factual trend analysis only — no forecasting.
"""

from decimal import ROUND_HALF_UP, Decimal


def compute_balance_trend(balances: list[int]) -> str:
    """
    Determine balance trend direction.

    Args:
        balances: List of balance values in chronological order (paise).

    Returns:
        Trend string: "IMPROVING", "STABLE", or "DECLINING".

    INVARIANT 1: IMPROVING = closing > opening.
    INVARIANT 2: DECLINING = closing < opening.
    INVARIANT 3: STABLE = closing == opening.
    INVARIANT 4: Empty or single value returns "STABLE".
    """
    if len(balances) < 2:
        return "STABLE"

    opening = balances[0]
    closing = balances[-1]

    # Use Decimal for precise comparison
    opening_decimal = Decimal(opening)
    closing_decimal = Decimal(closing)

    if closing_decimal > opening_decimal:
        return "IMPROVING"
    elif closing_decimal < opening_decimal:
        return "DECLINING"
    else:
        return "STABLE"


def compute_balance_velocity(
    opening_balance: int, closing_balance: int, days: int
) -> int:
    """
    Compute rate of balance change per day.

    Args:
        opening_balance: Opening balance in paise.
        closing_balance: Closing balance in paise.
        days: Number of days in the period.

    Returns:
        Velocity in paise/day (rounded using ROUND_HALF_UP).

    Raises:
        ValueError: If days is zero or negative.

    INVARIANT 1: Velocity = (closing - opening) / days.
    INVARIANT 2: Can be positive (growth) or negative (decline).
    INVARIANT 3: Uses ROUND_HALF_UP for rounding.
    """
    if days <= 0:
        raise ValueError("days must be positive")

    change = closing_balance - opening_balance
    velocity_decimal = Decimal(change) / Decimal(days)
    return int(velocity_decimal.quantize(Decimal(1), rounding=ROUND_HALF_UP))
