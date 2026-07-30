"""
EMI Engine - Standalone credit card conversion calculation
==========================================================
Independent EMI calculations using high-precision Decimal arithmetic
to ensure exact rounding consistency without loan_engine delegation.

All monetary values in paise (integer).
All rates in basis points (integer).
"""

from decimal import ROUND_HALF_UP, Decimal


def compute_monthly_interest(
    outstanding_paise: int,
    annual_rate_bps: int,
) -> int:
    """Compute standard monthly interest component in paise."""
    if outstanding_paise <= 0 or annual_rate_bps <= 0:
        return 0

    monthly_rate = Decimal(annual_rate_bps) / Decimal(10000) / Decimal(12)
    interest = Decimal(outstanding_paise) * monthly_rate
    return int(interest.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def compute_emi_fixed(
    principal_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
) -> int:
    """Compute fixed EMI using high-precision decimal arithmetic with ROUND_HALF_UP."""
    if annual_rate_bps == 0:
        # Standard integer division with ceiling adjustment for exact amortization
        return (principal_paise + tenure_months - 1) // tenure_months

    P = Decimal(principal_paise)
    r = Decimal(annual_rate_bps) / Decimal(10000) / Decimal(12)
    n = Decimal(tenure_months)

    one_plus_r_n = (Decimal(1) + r) ** n
    emi_decimal = P * r * one_plus_r_n / (one_plus_r_n - Decimal(1))
    return int(emi_decimal.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def compute_emi_conversion(
    amount_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
) -> dict[str, int]:
    """Compute EMI for a credit card conversion independently."""
    if amount_paise < 0:
        raise ValueError("amount_paise must be non-negative")
    if annual_rate_bps < 0:
        raise ValueError("annual_rate_bps must be non-negative")
    if tenure_months <= 0:
        raise ValueError("tenure_months must be positive")

    if amount_paise == 0:
        return {
            "emi_paise": 0,
            "total_interest_paise": 0,
            "total_repayment_paise": 0,
            "monthly_interest_paise": 0,
        }

    emi_paise = compute_emi_fixed(
        principal_paise=amount_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=tenure_months,
    )

    if annual_rate_bps == 0:
        total_repayment_paise = amount_paise
    else:
        total_repayment_paise = emi_paise * tenure_months
    total_interest_paise = total_repayment_paise - amount_paise

    first_month_interest = compute_monthly_interest(
        outstanding_paise=amount_paise,
        annual_rate_bps=annual_rate_bps,
    )

    return {
        "emi_paise": emi_paise,
        "total_interest_paise": max(0, total_interest_paise),
        "total_repayment_paise": total_repayment_paise,
        "monthly_interest_paise": first_month_interest,
    }
