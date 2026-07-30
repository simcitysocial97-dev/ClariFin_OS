"""
Utilization Engine - Pure calculation module
=============================================
Computes credit utilization and available credit.

All monetary values in paise (integer).
All rates in basis points (integer).

Utilization = outstanding / credit_limit × 10000 (returns basis points)
"""

from decimal import ROUND_HALF_EVEN, Decimal


def compute_utilization(
    outstanding_paise: int,
    credit_limit_paise: int,
) -> int:
    """
    Compute credit utilization as basis points.

    utilization_bps = (outstanding / credit_limit) × 10000

    Args:
        outstanding_paise: Current outstanding balance in paise.
        credit_limit_paise: Total credit limit in paise.

    Returns:
        Utilization in basis points (e.g., 2500 = 25%).
        Returns 0 if credit_limit is 0.

    INVARIANT 1: Money is always integer paise.
    INVARIANT 2: Rates stored as basis points.
    """
    if outstanding_paise < 0:
        raise ValueError("outstanding_paise must be non-negative")
    if credit_limit_paise < 0:
        raise ValueError("credit_limit_paise must be non-negative")

    if credit_limit_paise == 0 or outstanding_paise == 0:
        return 0

    utilization_decimal = (
        Decimal(outstanding_paise) * Decimal(10000) / Decimal(credit_limit_paise)
    )
    utilization_bps = int(
        utilization_decimal.quantize(Decimal(1), rounding=ROUND_HALF_EVEN)
    )

    return min(utilization_bps, 10000)  # Cap at 100%


def compute_available_credit(
    credit_limit_paise: int,
    outstanding_paise: int,
) -> int:
    """
    Compute available credit.

    available = max(0, credit_limit - outstanding)

    Args:
        credit_limit_paise: Total credit limit in paise.
        outstanding_paise: Current outstanding balance in paise.

    Returns:
        Available credit in paise (non-negative).

    INVARIANT 1: Money is always integer paise.
    INVARIANT 5: Balances are never negative.
    """
    if credit_limit_paise < 0:
        raise ValueError("credit_limit_paise must be non-negative")
    if outstanding_paise < 0:
        raise ValueError("outstanding_paise must be non-negative")

    return max(0, credit_limit_paise - outstanding_paise)
