"""
EMI Engine - Thin wrapper that delegates to loan_engine
========================================================
No EMI formula duplication. All calculations delegated to
loan_engine.emi for consistency and precision.

All monetary values in paise (integer).
All rates in basis points (integer).
"""
from src.engines.loan_engine.emi import compute_emi_fixed, compute_monthly_interest


def compute_emi_conversion(
    amount_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
) -> dict[str, int]:
    """
    Compute EMI for a credit card conversion.

    Delegates to loan_engine.emi.compute_emi_fixed().
    No formula duplication.

    Args:
        amount_paise: Amount being converted to EMI in paise.
        annual_rate_bps: Annual interest rate in basis points.
        tenure_months: EMI tenure in months (3, 6, 9, 12, 18, 24).

    Returns:
        dict with:
            - emi_paise: Monthly EMI amount
            - total_interest_paise: Total interest over tenure
            - total_repayment_paise: Total amount to repay
            - monthly_interest_paise: Interest component of first EMI

    INVARIANT 1: All monetary values in integer paise.
    INVARIANT 2: Rates stored as basis points.
    """
    if amount_paise <= 0:
        raise ValueError("amount_paise must be positive")
    if annual_rate_bps < 0:
        raise ValueError("annual_rate_bps must be non-negative")
    if tenure_months <= 0:
        raise ValueError("tenure_months must be positive")

    # Delegate to loan_engine - pure delegation, no recomputation
    emi_paise = compute_emi_fixed(
        principal_paise=amount_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=tenure_months,
    )

    # Calculate total repayment and interest
    total_repayment_paise = emi_paise * tenure_months
    total_interest_paise = total_repayment_paise - amount_paise

    # Interest component of first EMI (for informational purposes)
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

