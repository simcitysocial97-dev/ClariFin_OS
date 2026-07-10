"""
EMI Calculator — Deterministic and precise
=========================================
All monetary values in paise (integer).
All interest rates in basis points (integer).

Uses Decimal with banker's rounding (ROUND_HALF_EVEN) for all intermediate calculations.
"""

from decimal import ROUND_HALF_EVEN, Decimal


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

    # INVARIANT 2: basis points → monthly rate
    # 850 bps = 8.5% annual → 8.5/1200 = 0.007083 monthly
    monthly_rate: Decimal = Decimal(annual_rate_bps) / Decimal(120000)

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

    INVARIANT 1: Money is integer paise
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

    INVARIANT 1: Money is integer paise
    INVARIANT 2: Rates stored as basis points
    INVARIANT 6: Banker's rounding
    """
    monthly_rate: Decimal = Decimal(annual_rate_bps) / Decimal(120000)
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


def compute_cumulative_interest(schedule: list[dict[str, int]]) -> int:
    """
    Compute total interest paid over a schedule.

    Useful for comparing prepayment scenarios.
    """
    return sum(row.get("interest_paise", 0) for row in schedule)


def validate_positive_paise(value: int, name: str) -> None:
    """Validate that a monetary value is positive."""
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def validate_positive_bps(value: int, name: str) -> None:
    """Validate that a basis points value is non-negative."""
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value}")


def bps_to_decimal_rate(bps: int) -> Decimal:
    """
    Convert basis points to decimal annual rate.

    850 bps → 0.085
    """
    return Decimal(bps) / Decimal(10000)


def bps_to_monthly_rate(bps: int) -> Decimal:
    """
    Convert basis points to decimal monthly rate.

    850 bps → 0.007083...
    """
    return Decimal(bps) / Decimal(120000)
