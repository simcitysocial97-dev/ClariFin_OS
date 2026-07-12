"""
Foreclosure Engine - Thin wrapper that delegates to loan_engine
================================================================
No foreclosure calculation duplication. Delegates to
loan_engine.foreclosure.compute_foreclosure_amount().

All monetary values in paise (integer).
All rates in basis points (integer).
"""

from src.engines.loan_engine import compute_foreclosure_amount


def compute_card_foreclosure(
    outstanding_paise: int,
    annual_rate_bps: int,
    remaining_months: int,
    penalty_bps: int = 0,
) -> dict[str, int]:
    """
    Compute foreclosure payoff amount for a credit card EMI.

    Delegates to loan_engine.foreclosure.compute_foreclosure_amount().
    No formula duplication.

    Args:
        outstanding_paise: Current outstanding EMI balance in paise.
        annual_rate_bps: Annual interest rate in basis points.
        remaining_months: Remaining EMI months.
        penalty_bps: Prepayment penalty in basis points (default 0).

    Returns:
        dict with:
            - foreclosure_amount_paise: Total amount to close
            - outstanding_paise: Principal outstanding
            - accrued_interest_paise: Interest accrued
            - penalty_paise: Prepayment penalty

    INVARIANT 1: All monetary values in integer paise.
    """
    if outstanding_paise < 0:
        raise ValueError("outstanding_paise must be non-negative")
    if annual_rate_bps < 0:
        raise ValueError("annual_rate_bps must be non-negative")
    if remaining_months < 0:
        raise ValueError("remaining_months must be non-negative")
    if penalty_bps < 0:
        raise ValueError("penalty_bps must be non-negative")

    if outstanding_paise == 0:
        return {
            "foreclosure_amount_paise": 0,
            "outstanding_paise": 0,
            "accrued_interest_paise": 0,
            "penalty_paise": 0,
        }

    # Delegate to loan_engine - pure delegation
    result = compute_foreclosure_amount(
        outstanding_paise=outstanding_paise,
        annual_rate_bps=annual_rate_bps,
        remaining_months=remaining_months,
        months_paid=0,
        prepayment_penalty_bps=penalty_bps,
    )

    return {
        "foreclosure_amount_paise": result.foreclosure_amount_paise,
        "outstanding_paise": result.outstanding_paise,
        "accrued_interest_paise": result.accrued_interest_paise,
        "penalty_paise": result.penalty_paise,
    }
