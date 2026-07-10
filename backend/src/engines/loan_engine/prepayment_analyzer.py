"""
Prepayment Analyzer
===================
Simulates impact of prepayments on loan schedules.

Supports:
- Single and multiple prepayments
- Both reduce-tenure and reduce-EMI modes
- Prepayment penalties
- Dynamic schedule regeneration

INVARIANT 3: Returns new schedule, never mutates existing
"""

import math
from decimal import Decimal

from src.engines.loan_engine.amortization_builder import (
    generate_schedule,
    total_interest_paise,
)
from src.engines.loan_engine.dynamic_prepayment_engine import (
    apply_prepayment_at_month,
    apply_multiple_prepayments,
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
    prepayment_penalty_bps: int = 0,
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
        prepayment_penalty_bps: Prepayment penalty in basis points (optional)

    Returns:
        PrepaymentResult with comparison of before/after scenarios
    """
    # Generate a temporary schedule for the original loan
    original_schedule = generate_schedule(
        principal_paise=outstanding_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=remaining_months,
        start_date=start_date or "2025-01-01",
    )

    # Apply prepayment at month 1 (beginning of the schedule)
    _, result = apply_prepayment_at_month(
        original_schedule,
        1,
        prepayment_paise,
        annual_rate_bps,
        prepayment_penalty_bps,
        mode,
        start_date,
    )

    return result

def compute_savings(
    outstanding_paise: int,
    annual_rate_bps: int,
    remaining_months: int,
    prepayment_paise: int,
    mode: PrepaymentMode | str = "reduce_tenure",
    prepayment_penalty_bps: int = 0,
) -> int:
    """
    Compute interest savings from a prepayment.

    Convenience wrapper around apply_prepayment.
    """
    result = apply_prepayment(
        outstanding_paise,
        annual_rate_bps,
        remaining_months,
        prepayment_paise,
        mode,
        prepayment_penalty_bps=prepayment_penalty_bps,
    )
    return result.interest_saved_paise

def compute_multiple_prepayment_savings(
    outstanding_paise: int,
    annual_rate_bps: int,
    remaining_months: int,
    prepayments: list[tuple[int, int]],  # (month, amount_paise)
    mode: PrepaymentMode | str = "reduce_tenure",
    prepayment_penalty_bps: int = 0,
    start_date: str | None = None,
) -> tuple[int, list[PrepaymentResult]]:
    """
    Compute interest savings from multiple prepayments.

    Args:
        outstanding_paise: Current loan outstanding (paise)
        annual_rate_bps: Annual interest rate (basis points)
        remaining_months: Months left on loan
        prepayments: List of (month, amount_paise) tuples
        mode: "reduce_tenure" or "reduce_emi"
        prepayment_penalty_bps: Prepayment penalty in basis points
        start_date: ISO date string for schedule start

    Returns:
        tuple of (total_interest_saved_paise, list_of_prepayment_results)
    """
    # Generate original schedule
    original_schedule = generate_schedule(
        principal_paise=outstanding_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=remaining_months,
        start_date=start_date or "2025-01-01",
    )

    # Apply multiple prepayments
    new_schedule, results = apply_multiple_prepayments(
        original_schedule,
        prepayments,
        annual_rate_bps,
        prepayment_penalty_bps,
        mode,
        start_date,
    )

    # Calculate total interest saved
    original_interest = total_interest_paise(original_schedule)
    new_interest = total_interest_paise(new_schedule)
    total_savings = original_interest - new_interest

    return total_savings, results

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