"""
Interest Engine - Pure calculation module
=========================================
Daily interest accrual and monthly interest charge computation.

All monetary values in paise (integer).
All interest rates in basis points (integer).

Uses Decimal with ROUND_HALF_EVEN for all intermediate calculations.
Reuses bps_to_monthly_rate from loan_engine for rate conversion.

INVARIANT: Indian credit cards charge interest on daily balances
but bill monthly. This module calculates per-day accrual and
aggregates across a billing cycle.
"""

from decimal import ROUND_HALF_EVEN, Decimal


def bps_to_daily_rate(annual_rate_bps: int) -> Decimal:
    """
    Convert annual basis points to decimal daily rate.

    Daily rate = annual_rate_bps / (365 * 10000)
    Uses 365-day year (not 360) for Indian credit card convention.

    Args:
        annual_rate_bps: Annual interest rate in basis points (e.g., 2400 = 24%).

    Returns:
        Decimal daily rate.

    INVARIANT 2: Rates stored as basis points.
    """
    return Decimal(annual_rate_bps) / Decimal(3650000)


def compute_daily_interest(
    outstanding_paise: int,
    annual_rate_bps: int,
) -> int:
    """
    Compute interest accrued for one day on the given outstanding balance.

    Interest = outstanding × daily_rate

    Args:
        outstanding_paise: Outstanding balance for the day in paise.
        annual_rate_bps: Annual interest rate in basis points.

    Returns:
        Daily interest in paise (int), rounded with ROUND_HALF_EVEN.

    INVARIANT 1: Money is always integer paise.
    INVARIANT 6: Interest calculations use banker's rounding.
    """
    if outstanding_paise < 0:
        raise ValueError("outstanding_paise must be non-negative")
    if annual_rate_bps < 0:
        raise ValueError("annual_rate_bps must be non-negative")

    if outstanding_paise == 0 or annual_rate_bps == 0:
        return 0

    daily_rate: Decimal = bps_to_daily_rate(annual_rate_bps)
    outstanding: Decimal = Decimal(outstanding_paise)
    interest_decimal: Decimal = outstanding * daily_rate
    interest_paise = int(interest_decimal.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))

    return interest_paise


def compute_monthly_interest_charge(
    daily_balances: list[tuple[str, int]],
    annual_rate_bps: int,
) -> int:
    """
    Compute total interest charge for a billing cycle.

    Aggregates daily interest across all days in the cycle.
    Each entry is (date_iso, outstanding_balance_paise).

    Args:
        daily_balances: List of (date_string, balance_paise) for each day
                       in the billing cycle.
        annual_rate_bps: Annual interest rate in basis points.

    Returns:
        Total interest charge in paise (int).

    INVARIANT 1: Money is always integer paise.
    INVARIANT 6: Banker's rounding.
    """
    if not daily_balances:
        return 0
    if annual_rate_bps < 0:
        raise ValueError("annual_rate_bps must be non-negative")

    total_interest: int = 0
    for _date_iso, balance in daily_balances:
        if balance < 0:
            raise ValueError(f"Negative balance {balance} on date {_date_iso}")
        total_interest += compute_daily_interest(balance, annual_rate_bps)

    return total_interest


def compute_monthly_interest_simple(
    average_daily_balance_paise: int,
    annual_rate_bps: int,
    days_in_cycle: int,
) -> int:
    """
    Simplified monthly interest using average daily balance method.

    Some credit cards use average daily balance instead of per-day.
    This is an alternative to compute_monthly_interest_charge.

    Interest = avg_daily_balance × daily_rate × days_in_cycle

    Args:
        average_daily_balance_paise: Average daily balance in paise.
        annual_rate_bps: Annual interest rate in basis points.
        days_in_cycle: Number of days in the billing cycle.

    Returns:
        Interest charge in paise (int).
    """
    if average_daily_balance_paise < 0:
        raise ValueError("average_daily_balance_paise must be non-negative")
    if days_in_cycle <= 0:
        raise ValueError("days_in_cycle must be positive")
    if annual_rate_bps < 0:
        raise ValueError("annual_rate_bps must be non-negative")

    if average_daily_balance_paise == 0 or annual_rate_bps == 0:
        return 0

    # Per-day interest * days in cycle
    daily = compute_daily_interest(average_daily_balance_paise, annual_rate_bps)
    return daily * days_in_cycle
