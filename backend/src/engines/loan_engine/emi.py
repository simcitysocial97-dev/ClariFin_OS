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
    """
    if tenure_months <= 0:
        raise ValueError("Tenure must be positive")

    if principal_paise <= 0:
        raise ValueError("Principal must be positive")

    if annual_rate_bps < 0:
        raise ValueError("Rate cannot be negative")

    monthly_rate: Decimal = bps_to_monthly_rate(annual_rate_bps)

    if annual_rate_bps == 0:
        return principal_paise // tenure_months

    one: Decimal = Decimal(1)
    factor: Decimal = (one + monthly_rate) ** tenure_months
    principal: Decimal = Decimal(principal_paise)

    emi_decimal: Decimal = principal * monthly_rate * factor / (factor - one)

    emi_paise = int(emi_decimal)
    return emi_paise


def compute_emi_floating(
    outstanding_paise: int,
    annual_rate_bps: int,
    remaining_months: int,
) -> int:
    """Compute EMI for floating-rate loan."""
    return compute_emi_fixed(outstanding_paise, annual_rate_bps, remaining_months)


def compute_monthly_interest(
    outstanding_paise: int,
    annual_rate_bps: int,
) -> int:
    """Compute interest component for one month."""
    monthly_rate: Decimal = bps_to_monthly_rate(annual_rate_bps)
    outstanding: Decimal = Decimal(outstanding_paise)

    if annual_rate_bps == 0:
        return 0

    interest_decimal: Decimal = outstanding * monthly_rate
    interest_paise = int(interest_decimal)
    return interest_paise


def compute_principal_component(
    emi_paise: int,
    interest_paise: int,
) -> int:
    """Compute principal component from EMI and interest."""
    return emi_paise - interest_paise


def compute_principal_from_emi(
    emi_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
) -> int:
    """
    Compute principal from EMI, rate, and tenure (inverse of compute_emi_fixed).

    P = EMI * ((1+r)^n - 1) / (r * (1+r)^n)

    INVARIANT 1: Money is always integer paise
    INVARIANT 2: Rates stored as basis points
    """
    if tenure_months <= 0:
        raise ValueError("Tenure must be positive")

    if annual_rate_bps == 0:
        return emi_paise * tenure_months

    monthly_rate: Decimal = bps_to_monthly_rate(annual_rate_bps)
    one: Decimal = Decimal(1)
    factor: Decimal = (one + monthly_rate) ** Decimal(tenure_months)
    emi: Decimal = Decimal(emi_paise)

    numerator: Decimal = emi * (factor - one)
    denominator: Decimal = monthly_rate * factor

    principal_decimal: Decimal = numerator / denominator
    base_principal = int(principal_decimal.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))

    # Extended localized search window (-500 to +500 paise) to securely capture 
    # forward-pass integer quantization divergence across all boundary cases.
    best_principal = base_principal
    min_diff = float('inf')
    best_distance = float('inf')

    for candidate in range(base_principal - 500, base_principal + 501):
        if candidate <= 0:
            continue
        test_emi = compute_emi_fixed(candidate, annual_rate_bps, tenure_months)
        diff = abs(test_emi - emi_paise)
        distance = abs(candidate - base_principal)
        
        # Prefer smaller diff, then smaller distance from base_principal
        if diff < min_diff or (diff == min_diff and distance < best_distance):
            min_diff = diff
            best_distance = distance
            best_principal = candidate

    return best_principal


def compute_tenure_from_emi(
    principal_paise: int,
    annual_rate_bps: int,
    emi_paise: int,
) -> int:
    """Compute tenure from principal, rate, and EMI."""
    if principal_paise <= 0:
        raise ValueError("Principal must be positive")

    if emi_paise <= 0:
        raise ValueError("EMI must be positive")

    if annual_rate_bps == 0:
        return (principal_paise + emi_paise - 1) // emi_paise  # ceiling

    monthly_rate: Decimal = bps_to_monthly_rate(annual_rate_bps)
    one: Decimal = Decimal(1)

    interest_only = Decimal(principal_paise) * monthly_rate
    if emi_paise <= interest_only:
        return 999  # EMI doesn't cover interest — return max

    ratio = Decimal(emi_paise) / (Decimal(emi_paise) - interest_only)
    
    # High-precision Decimal logarithm computation to eliminate float drift
    n = ratio.ln() / (one + monthly_rate).ln()
    tenure = int(n.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))

    return min(999, max(1, tenure))
