"""
Foreclosure Engine - Pure calculation module
==========================================
Calculates foreclosure amount for loans.
"""

from decimal import ROUND_HALF_EVEN, Decimal

from .amortization import generate_schedule, total_interest_paise
from .models import ForeclosureResult


def compute_foreclosure_amount(
    outstanding_paise: int,
    annual_rate_bps: int,
    remaining_months: int,
    months_paid: int = 0,
    prepayment_penalty_bps: int = 0,
) -> ForeclosureResult:
    """
    Calculate foreclosure amount including penalties and accrued interest.

    Args:
        outstanding_paise: Current outstanding principal (paise)
        annual_rate_bps: Annual interest rate (basis points)
        remaining_months: Remaining tenure in months
        months_paid: Months already paid (0 if none)
        prepayment_penalty_bps: Prepayment penalty rate (basis points)

    Returns:
        ForeclosureResult with breakdown of costs
    """
    # Calculate accrued interest for remaining period
    # First, generate the remaining schedule
    # For foreclosure, we need to calculate interest from the beginning of remaining period
    original_schedule = generate_schedule(
        principal_paise=outstanding_paise + (months_paid * 0),  # We need original principal
        annual_rate_bps=annual_rate_bps,
        tenure_months=remaining_months,
        start_date="2025-01-01",  # Default, would need actual start date
    )

    # Interest remaining to be paid
    remaining_interest = total_interest_paise(original_schedule)

    # Penalty calculation
    penalty_decimal = Decimal(prepayment_penalty_bps) * Decimal(outstanding_paise) / Decimal(10000)
    penalty_paise = int(penalty_decimal.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))

    # Total foreclosure amount
    foreclosure_amount = outstanding_paise + remaining_interest + penalty_paise

    return ForeclosureResult(
        outstanding_paise=outstanding_paise,
        accrued_interest_paise=remaining_interest,
        penalty_paise=penalty_paise,
        foreclosure_amount_paise=foreclosure_amount,
        remaining_months_saved=remaining_months,
    )


def compute_prepayment_breakup(
    outstanding_paise: int,
    annual_rate_bps: int,
    months_elapsed: int,
    original_principal_paise: int,
    original_tenure_months: int,
    prepayment_penalty_bps: int = 0,
) -> dict[str, int]:
    """
    Break down prepayment/foreclosure costs.

    Returns:
        Dictionary with principal_remaining, accrued_interest, penalty, total
    """
    remaining_months = original_tenure_months - months_elapsed

    if remaining_months <= 0:
        return {
            "principal_remaining_paise": 0,
            "accrued_interest_paise": 0,
            "penalty_paise": 0,
            "total_foreclosure_paise": 0,
        }

    # Generate schedule for remaining period
    from .amortization import generate_schedule

    # Calculate principal remaining (current outstanding)
    principal_remaining = outstanding_paise

    # Calculate interest that would be paid in remaining period
    remaining_schedule = generate_schedule(
        principal_paise=outstanding_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=remaining_months,
        start_date="2025-01-01",
    )

    accrued_interest = sum(row.interest_paise for row in remaining_schedule)

    # Penalty
    penalty_decimal = Decimal(prepayment_penalty_bps) * Decimal(principal_remaining) / Decimal(10000)
    penalty = int(penalty_decimal.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))

    return {
        "principal_remaining_paise": principal_remaining,
        "accrued_interest_paise": accrued_interest,
        "penalty_paise": penalty,
        "total_foreclosure_paise": principal_remaining + accrued_interest + penalty,
    }
