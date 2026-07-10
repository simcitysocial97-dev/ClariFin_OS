"""
Prepayment Analyzer
===================
Simulates impact of prepayments on loan schedules.

Supports two modes:
- REDUCE_TENURE: Same EMI, shorter loan
- REDUCE_EMI: Same tenure, lower payments

INVARIANT 3: Returns new schedule, never mutates existing
"""

import math
from decimal import Decimal

from src.engines.loan_engine.amortization_builder import (
    generate_schedule,
    total_interest_paise,
)
from src.engines.loan_engine.emi_calculator import compute_emi_fixed
from src.engines.loan_engine.types import AmortizationRow, PrepaymentMode, PrepaymentResult


def compute_remaining_months(
    principal_paise: int,
    annual_rate_bps: int,
    emi_paise: int,
) -> int:
    """
    Compute remaining months given principal, rate (bps), and fixed EMI.

    Uses logarithmic formula for precise calculation.
    Returns integer months.
    """
    if annual_rate_bps == 0:
        return math.ceil(principal_paise / emi_paise) if emi_paise > 0 else 999

    monthly_rate: Decimal = Decimal(annual_rate_bps) / Decimal(120000)
    principal: Decimal = Decimal(principal_paise)
    emi: Decimal = Decimal(emi_paise)

    # EMI must cover interest to work
    if emi <= principal * monthly_rate:
        return 999  # Will never close

    # n = ln(EMI / (EMI - P * r)) / ln(1 + r)
    numerator = emi / (emi - principal * monthly_rate)
    denominator = Decimal(1) + monthly_rate

    months_decimal = numerator.ln() / denominator.ln()
    return math.ceil(months_decimal)


def apply_prepayment(
    outstanding_paise: int,
    annual_rate_bps: int,
    remaining_months: int,
    prepayment_paise: int,
    mode: PrepaymentMode | str = "reduce_tenure",
    start_date: str | None = None,
) -> PrepaymentResult:
    """
    Simulate impact of a prepayment on remaining loan term.

    INVARIANT 1: All money values are integer paise
    INVARIANT 2: Rate is integer basis points
    INVARIANT 3: Returns new result, never mutates input

    Args:
        outstanding_paise: Current loan outstanding (paise)
        annual_rate_bps: Annual interest rate (basis points)
        remaining_months: Months left on loan
        prepayment_paise: Prepayment amount (paise)
        mode: "reduce_tenure" or "reduce_emi"
        start_date: ISO date string for schedule regeneration (optional)

    Returns:
        PrepaymentResult with comparison of before/after scenarios
    """
    # Validate inputs
    if outstanding_paise <= 0:
        raise ValueError("Outstanding must be positive")
    if prepayment_paise <= 0:
        raise ValueError("Prepayment must be positive")

    # Normalize mode to PrepaymentMode enum
    if isinstance(mode, str):
        mode_enum = PrepaymentMode(mode)
    else:
        mode_enum = mode

    original_emi_paise = compute_emi_fixed(outstanding_paise, annual_rate_bps, remaining_months)
    new_principal_paise = outstanding_paise - prepayment_paise

    # Full prepayment closes the loan
    if new_principal_paise <= 0:
        return PrepaymentResult(
            prepayment_paise=prepayment_paise,
            mode=mode_enum,
            original_emi_paise=original_emi_paise,
            new_emi_paise=0,
            original_remaining_months=remaining_months,
            new_remaining_months=0,
            months_saved=remaining_months,
            interest_saved_paise=outstanding_paise,  # All interest saved
            loan_closed=True,
        )

    if mode == "reduce_tenure":
        new_months = compute_remaining_months(new_principal_paise, annual_rate_bps, original_emi_paise)
        new_emi_paise = original_emi_paise
    else:  # reduce_emi
        new_months = remaining_months
        new_emi_paise = compute_emi_fixed(new_principal_paise, annual_rate_bps, remaining_months)

    # Compute interest saved via schedule comparison
    original_schedule = generate_schedule(
        principal_paise=outstanding_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=remaining_months,
        start_date=start_date or "2025-01-01",
    ) if start_date else None

    new_schedule = generate_schedule(
        principal_paise=new_principal_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=new_months,
        start_date=start_date or "2025-01-01",
    ) if start_date else None

    # If we have schedules, compute precise savings
    if original_schedule and new_schedule:
        original_interest = total_interest_paise(original_schedule)
        new_interest = total_interest_paise(new_schedule)
        interest_saved_paise = max(0, original_interest - new_interest - prepayment_paise)
    else:
        # Fallback: simple approximation
        original_total = original_emi_paise * remaining_months
        new_total = new_emi_paise * new_months + prepayment_paise
        interest_saved_paise = max(0, original_total - new_total)

    return PrepaymentResult(
        prepayment_paise=prepayment_paise,
        mode=mode_enum,
        original_emi_paise=original_emi_paise,
        new_emi_paise=new_emi_paise,
        original_remaining_months=remaining_months,
        new_remaining_months=new_months,
        months_saved=remaining_months - new_months,
        interest_saved_paise=interest_saved_paise,
        loan_closed=False,
    )


def compute_savings(
    original_schedule: list[AmortizationRow],
    new_schedule: list[AmortizationRow],
    prepayment_paise: int,
) -> dict[str, int]:
    """
    Compute exact savings between two schedules.

    Returns dict with interest_saved_paise, months_saved, and total_savings_paise.
    """
    original_interest = sum(row.interest_paise for row in original_schedule)
    new_interest = sum(row.interest_paise for row in new_schedule)

    return {
        "original_interest_paise": original_interest,
        "new_interest_paise": new_interest,
        "interest_saved_paise": max(0, original_interest - new_interest - prepayment_paise),
        "months_saved": len(original_schedule) - len(new_schedule),
        "total_savings_paise": max(0, original_interest - new_interest - prepayment_paise),
    }
