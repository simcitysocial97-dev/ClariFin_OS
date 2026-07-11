"""
Prepayment Engine - Core calculation module
=========================================
Pure calculations for prepayment on loan schedules.

Supports:
- Single and multiple prepayments
- Both reduce-tenure and reduce-EMI modes
- Prepayment penalties
- Dynamic schedule regeneration

INVARIANT 1-6 enforced throughout.
"""

import math
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Literal

from .amortization import (
    generate_schedule,
    total_interest_paise,
)
from .emi import compute_emi_fixed
from .models import AmortizationRow, PrepaymentMode, PrepaymentResult


def _compute_tenure_from_emi(
    principal_paise: int,
    annual_rate_bps: int,
    emi_paise: int,
) -> int:
    """
    Compute remaining months given principal, rate (bps), and fixed EMI.

    Uses logarithmic formula for precise calculation.
    Shared helper used by compute_remaining_months and regenerate_schedule.
    Returns integer months (ceiling).
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
    return _compute_tenure_from_emi(principal_paise, annual_rate_bps, emi_paise)


def apply_prepayment(
    outstanding_paise: int,
    annual_rate_bps: int,
    remaining_months: int,
    prepayment_paise: int,
    mode: PrepaymentMode = PrepaymentMode.REDUCE_TENURE,
    start_date: str | None = None,
    prepayment_penalty_bps: int = 0,
    existing_schedule: list[AmortizationRow] | None = None,
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
        existing_schedule: Pre-generated schedule to avoid duplicate generation (optional)

    Returns:
        PrepaymentResult with comparison of before/after scenarios
    """
    # Use existing schedule if provided, otherwise generate one
    original_schedule = existing_schedule
    if original_schedule is None:
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


def apply_prepayment_at_month(
    schedule: list[AmortizationRow],
    prepayment_month: int,
    prepayment_paise: int,
    annual_rate_bps: int,
    prepayment_penalty_bps: int = 0,
    mode: PrepaymentMode | Literal["reduce_tenure", "reduce_emi"] = "reduce_tenure",
    start_date: str | None = None,
) -> tuple[list[AmortizationRow], PrepaymentResult]:
    """
    Apply a prepayment at a specific month and regenerate the schedule.

    INVARIANT 1: All money values in paise (integer)
    INVARIANT 2: Rate in basis points (integer)
    INVARIANT 3: Returns new schedule, never mutates input
    """
    if prepayment_month < 1 or prepayment_month > len(schedule):
        raise ValueError(f"Prepayment month {prepayment_month} out of range [1, {len(schedule)}]")

    if prepayment_paise <= 0:
        raise ValueError("Prepayment amount must be positive")

    # Extract the state at the prepayment month
    prepayment_row = schedule[prepayment_month - 1]
    remaining_balance = prepayment_row.balance_paise
    remaining_months = len(schedule) - prepayment_month + 1

    # Apply prepayment penalty if any
    penalty_decimal = Decimal(prepayment_paise) * Decimal(prepayment_penalty_bps) / Decimal(10000)
    penalty_paise = int(penalty_decimal.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
    effective_prepayment = prepayment_paise - penalty_paise

    # Compute new balance after prepayment
    new_balance = max(0, remaining_balance - effective_prepayment)

    # Check if loan is fully paid off
    if new_balance <= 0:
        # Loan is closed - return truncated schedule
        new_schedule = schedule[:prepayment_month]
        original_interest = total_interest_paise(schedule)
        new_interest = total_interest_paise(new_schedule)
        interest_saved = original_interest - new_interest

        return new_schedule, PrepaymentResult(
            prepayment_paise=prepayment_paise,
            mode=PrepaymentMode(mode),
            original_emi_paise=prepayment_row.emi_paise,
            new_emi_paise=0,
            original_remaining_months=remaining_months,
            new_remaining_months=0,
            months_saved=remaining_months,
            interest_saved_paise=interest_saved - penalty_paise,
            loan_closed=True,
            new_schedule=new_schedule,
        )

    # Compute start date for regenerated schedule (first payment of remaining period)
    schedule_start_date = start_date
    if schedule_start_date is None:
        schedule_start_date = schedule[prepayment_month - 1].payment_date

    # Generate new schedule from prepayment point
    # Pass schedule from prepayment month onwards for proper tenure calculation
    # Convert mode to Literal for type compatibility
    mode_literal: Literal["reduce_tenure", "reduce_emi"] = "reduce_tenure" if mode == "reduce_tenure" or mode == PrepaymentMode.REDUCE_TENURE else "reduce_emi"
    new_regenerated = regenerate_schedule(
        schedule[prepayment_month - 1:],
        new_balance,
        annual_rate_bps,
        mode_literal,
        schedule_start_date,
    )

    # Combine completed schedule with regenerated portion
    completed_portion = schedule[:prepayment_month - 1] if prepayment_month > 1 else []
    new_schedule = completed_portion + new_regenerated

    # Compute savings
    original_interest = total_interest_paise(schedule)
    new_interest = total_interest_paise(new_schedule)
    interest_saved = original_interest - new_interest

    # Determine new EMI (could be same or different)
    new_emi = 0
    if new_regenerated:
        if mode == "reduce_tenure":
            # First row of regenerated schedule is at prepayment_month
            new_emi = new_regenerated[0].emi_paise
        else:
            new_emi = new_regenerated[0].emi_paise

    return new_schedule, PrepaymentResult(
        prepayment_paise=prepayment_paise,
        mode=PrepaymentMode(mode),
        original_emi_paise=prepayment_row.emi_paise,
        new_emi_paise=new_emi,
        original_remaining_months=remaining_months,
        new_remaining_months=len(new_regenerated),
        months_saved=remaining_months - len(new_regenerated),
        interest_saved_paise=interest_saved - penalty_paise,
        loan_closed=False,
        new_schedule=new_schedule,
    )


def apply_multiple_prepayments(
    schedule: list[AmortizationRow],
    prepayments: list[tuple[int, int]],  # (month, amount_paise)
    annual_rate_bps: int,
    prepayment_penalty_bps: int = 0,
    mode: PrepaymentMode | Literal["reduce_tenure", "reduce_emi"] = "reduce_tenure",
    start_date: str | None = None,
) -> tuple[list[AmortizationRow], list[PrepaymentResult]]:
    """
    Apply multiple prepayments sequentially to a schedule.

    Returns updated schedule and list of prepayment results.
    """
    if not prepayments:
        return schedule, []

    # Sort prepayments by month (earliest first)
    sorted_prepayments = sorted(prepayments, key=lambda x: x[0])
    current_schedule = schedule.copy()
    results = []

    for month, amount in sorted_prepayments:
        if month < 1 or month > len(current_schedule):
            continue  # Skip invalid months

        new_schedule, result = apply_prepayment_at_month(
            current_schedule,
            month,
            amount,
            annual_rate_bps,
            prepayment_penalty_bps,
            mode,
            start_date,
        )
        current_schedule = new_schedule
        results.append(result)

    return current_schedule, results


def regenerate_schedule(
    previous_schedule: list[AmortizationRow],
    new_principal_paise: int,
    annual_rate_bps: int,
    mode: Literal["reduce_tenure", "reduce_emi"],
    start_date: str,
) -> list[AmortizationRow]:
    """
    Regenerate schedule after prepayment or rate change.

    Args:
        previous_schedule: Schedule from the prepayment/change month onwards
        new_principal_paise: Remaining principal after prepayment (paise)
        annual_rate_bps: Annual interest rate in basis points
        mode: "reduce_tenure" (keep EMI) or "reduce_emi" (calculate new EMI)
        start_date: Start date of the new schedule (first payment date)

    Returns NEW schedule starting from previous_schedule[0].month_number.
    INVARIANT 3: Does not modify existing schedule.
    """
    if new_principal_paise <= 0:
        return []

    # Derive remaining_months from previous_schedule length
    remaining_months = len(previous_schedule)

    # Get the current EMI from the first row of previous schedule (for reduce_tenure mode)
    current_emi = previous_schedule[0].emi_paise if previous_schedule else 0

    # Calculate tenure based on mode
    if mode == "reduce_tenure":
        # Keep EMI same, calculate new tenure
        calc_remaining_months = _compute_tenure_from_emi(
            new_principal_paise, annual_rate_bps, current_emi
        )
    else:
        # Reduce EMI mode: keep original remaining tenure
        calc_remaining_months = remaining_months

    # Compute the month offset to continue numbering
    month_offset = 0
    if previous_schedule:
        month_offset = previous_schedule[0].month_number - 1

    # Generate new schedule
    new_schedule = generate_schedule(
        principal_paise=new_principal_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=calc_remaining_months,
        start_date=start_date,
        emi_paise=current_emi if mode == "reduce_tenure" else None,
    )

    if mode == "reduce_emi":
        # Recalculate EMI for reduce_emi mode
        new_emi_val = compute_emi_fixed(new_principal_paise, annual_rate_bps, calc_remaining_months)
        # Rebuild schedule with correct EMI
        new_schedule = generate_schedule(
            principal_paise=new_principal_paise,
            annual_rate_bps=annual_rate_bps,
            tenure_months=calc_remaining_months,
            start_date=start_date,
            emi_paise=new_emi_val,
        )

    # Adjust month numbers to continue from previous schedule
    if previous_schedule and month_offset > 0:
        adjusted_schedule = []
        for row in new_schedule:
            adjusted_schedule.append(AmortizationRow(
                month_number=row.month_number + month_offset,
                payment_date=row.payment_date,
                emi_paise=row.emi_paise,
                principal_paise=row.principal_paise,
                interest_paise=row.interest_paise,
                balance_paise=row.balance_paise,
                cumulative_interest_paise=row.cumulative_interest_paise,
            ))
        return adjusted_schedule

    return new_schedule