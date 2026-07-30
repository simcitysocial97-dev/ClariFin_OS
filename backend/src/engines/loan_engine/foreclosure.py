"""
Foreclosure Engine - Pure calculation module
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
    if outstanding_paise <= 0 or remaining_months <= 0:
        return ForeclosureResult(
            outstanding_paise=max(0, outstanding_paise),
            accrued_interest_paise=0,
            penalty_paise=0,
            foreclosure_amount_paise=max(0, outstanding_paise),
            remaining_months_saved=max(0, remaining_months),
        )

    # Generate schedule for remaining period
    schedule = generate_schedule(
        principal_paise=outstanding_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=remaining_months,
        start_date="2025-01-01",
    )

    remaining_interest = total_interest_paise(schedule)

    # Penalty with ROUND_HALF_EVEN
    penalty = int(
        (
            Decimal(prepayment_penalty_bps)
            * Decimal(outstanding_paise)
            / Decimal(10000)
        ).quantize(Decimal(1), rounding=ROUND_HALF_EVEN)
    )

    total = outstanding_paise + remaining_interest + penalty

    return ForeclosureResult(
        outstanding_paise=outstanding_paise,
        accrued_interest_paise=remaining_interest,
        penalty_paise=penalty,
        foreclosure_amount_paise=total,
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
    remaining_months = original_tenure_months - months_elapsed
    if remaining_months <= 0 or outstanding_paise <= 0:
        return {
            "principal_remaining_paise": max(0, outstanding_paise),
            "accrued_interest_paise": 0,
            "penalty_paise": 0,
            "total_foreclosure_paise": max(0, outstanding_paise),
        }

    schedule = generate_schedule(
        principal_paise=outstanding_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=remaining_months,
        start_date="2025-01-01",
    )
    accrued_interest = total_interest_paise(schedule)
    penalty = int(
        (
            Decimal(prepayment_penalty_bps)
            * Decimal(outstanding_paise)
            / Decimal(10000)
        ).quantize(Decimal(1), rounding=ROUND_HALF_EVEN)
    )

    return {
        "principal_remaining_paise": outstanding_paise,
        "accrued_interest_paise": accrued_interest,
        "penalty_paise": penalty,
        "total_foreclosure_paise": outstanding_paise + accrued_interest + penalty,
    }
