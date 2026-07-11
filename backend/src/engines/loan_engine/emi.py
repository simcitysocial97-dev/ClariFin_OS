"""
EMI Calculator - Deterministic and precise
=========================================
All monetary values in paise (integer).
All interest rates in basis points (integer).

Uses Decimal with banker's rounding (ROUND_HALF_EVEN) for all intermediate calculations.
"""

from decimal import ROUND_HALF_EVEN, Decimal
from functools import lru_cache

from .utils import bps_to_monthly_rate


@lru_cache(maxsize=1024)
def compute_emi_fixed(
    principal_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
) -> int:
    """
    Compute EMI for fixed-rate loan using reducing balance formula.

    EMI = P × r × (1+r)^n / ((1+r)^n - 1)

    Where:
    - P = principal in paise (int)
    - r = monthly rate (basis points → decimal: bps/120000)
    - n = tenure in months (int)

    Returns EMI in paise (int), rounded with ROUND_HALF_EVEN.

    INVARIANT 1: Money is always integer paise
    INVARIANT 2: Rates stored as basis points (1% = 100)
    INVARIANT 6: Interest calculations use banker's rounding
    """
    if tenure_months <= 0:
        raise ValueError("Tenure must be positive")

    if principal_paise <= 0:
        raise ValueError("Principal must be positive")

    if annual_rate_bps < 0:
        raise ValueError("Rate cannot be negative")

    # INVARIANT 2: basis points → monthly rate
    # 850 bps = 8.5% annual → 8.5/1200 = 0.007083 monthly
    monthly_rate: Decimal = bps_to_monthly_rate(annual_rate_bps)

    # Edge case: zero interest rate
    if annual_rate_bps == 0:
        return principal_paise // tenure_months

    # EMI formula using Decimal
    one: Decimal = Decimal(1)
    factor: Decimal = (one + monthly_rate) ** tenure_months
    principal: Decimal = Decimal(principal_paise)

    emi_decimal: Decimal = principal * monthly_rate * factor / (factor - one)

    # INVARIANT 6: Banker's rounding
    emi_paise = int(emi_decimal.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))

    return emi_paise


def compute_emi_floating(
    outstanding_paise: int,
    annual_rate_bps: int,
    remaining_months: int,
) -> int:
    """
    Compute EMI for floating-rate loan.

    Same formula as fixed, but rate may change on reset dates.
    This function computes EMI for current rate.

    INVARIANT 1: All money values in integer paise
    INVARIANT 2: Rates stored as basis points
    """
    return compute_emi_fixed(outstanding_paise, annual_rate_bps, remaining_months)


def compute_monthly_interest(
    outstanding_paise: int,
    annual_rate_bps: int,
) -> int:
    """
    Compute interest component for one month.

    Interest = Outstanding × Monthly_Rate
    where Monthly_Rate = annual_rate_bps / 120000

    Returns interest in paise (int), rounded with ROUND_HALF_EVEN.

    INVARIANT 1: Money is always integer paise
    INVARIANT 2: Rates stored as basis points
    INVARIANT 6: Banker's rounding
    """
    monthly_rate: Decimal = bps_to_monthly_rate(annual_rate_bps)
    outstanding: Decimal = Decimal(outstanding_paise)

    if annual_rate_bps == 0:
        return 0

    interest_decimal: Decimal = outstanding * monthly_rate
    interest_paise = int(interest_decimal.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))

    return interest_paise


def compute_principal_component(
    emi_paise: int,
    interest_paise: int,
) -> int:
    """
    Compute principal component from EMI and interest.

    Principal_Component = EMI - Interest

    INVARIANT 1: Both inputs/return are integer paise
    """
    return emi_paise - interest_paise
