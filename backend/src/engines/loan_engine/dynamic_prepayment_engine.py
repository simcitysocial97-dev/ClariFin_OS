"""
Dynamic Prepayment Engine
=========================
Core engine for applying prepayments to loan schedules with accurate interest recalculation.

Supports:
- Single and multiple prepayments
- Both reduce-tenure and reduce-EMI modes
- Prepayment penalties
- Dynamic schedule regeneration
- Floating rate adjustments

INVARIANT 1-6 enforced throughout.
"""

from decimal import Decimal
from typing import Literal

from src.engines.loan_engine.amortization_builder import (
    generate_schedule,
    regenerate_schedule,
    total_interest_paise,
)
from src.engines.loan_engine.emi_calculator import compute_emi_fixed
from src.engines.loan_engine.types import (
    AmortizationRow,
    PrepaymentMode,
    PrepaymentResult,
)

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
    penalty_paise = int(prepayment_paise * prepayment_penalty_bps / 10000)
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

    # Generate new schedule from prepayment point
    if mode == "reduce_tenure":
        # Keep EMI same, reduce tenure
        new_schedule = regenerate_schedule(
            schedule[:prepayment_month],
            new_balance,
            annual_rate_bps,
            "reduce_tenure",
            start_date,
        )
    else:
        # Reduce EMI, keep tenure same
        new_schedule = regenerate_schedule(
            schedule[:prepayment_month],
            new_balance,
            annual_rate_bps,
            "reduce_emi",
            start_date,
        )

    # Compute savings
    original_interest = total_interest_paise(schedule)
    new_interest = total_interest_paise(new_schedule)
    interest_saved = original_interest - new_interest

    # Determine new EMI (could be same or different)
    new_emi = new_schedule[prepayment_month - 1].emi_paise if new_schedule else 0

    return new_schedule, PrepaymentResult(
        prepayment_paise=prepayment_paise,
        mode=PrepaymentMode(mode),
        original_emi_paise=prepayment_row.emi_paise,
        new_emi_paise=new_emi,
        original_remaining_months=remaining_months,
        new_remaining_months=len(new_schedule) - prepayment_month + 1,
        months_saved=remaining_months - (len(new_schedule) - prepayment_month + 1),
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

def apply_floating_rate_change(
    schedule: list[AmortizationRow],
    change_month: int,
    new_rate_bps: int,
    mode: Literal["adjust_emi", "adjust_tenure"] = "adjust_emi",
    start_date: str | None = None,
) -> list[AmortizationRow]:
    """
    Apply floating rate change to a schedule.

    Supports two modes:
    - adjust_emi: Keep tenure same, adjust EMI
    - adjust_tenure: Keep EMI same, adjust tenure
    """
    if change_month < 1 or change_month > len(schedule):
        raise ValueError(f"Change month {change_month} out of range [1, {len(schedule)}]")

    if new_rate_bps < 0:
        raise ValueError("Rate cannot be negative")

    # Extract state at change month
    change_row = schedule[change_month - 1]
    remaining_balance = change_row.balance_paise
    remaining_months = len(schedule) - change_month + 1

    if mode == "adjust_emi":
        # Keep tenure same, compute new EMI
        new_emi = compute_emi_fixed(
            remaining_balance,
            new_rate_bps,
            remaining_months,
        )
        new_schedule = regenerate_schedule(
            schedule[:change_month],
            remaining_balance,
            new_rate_bps,
            "reduce_emi",
            start_date,
        )
    else:
        # Keep EMI same, compute new tenure
        new_schedule = regenerate_schedule(
            schedule[:change_month],
            remaining_balance,
            new_rate_bps,
            "reduce_tenure",
            start_date,
        )

    return new_schedule

def simulate_floating_rate_schedule(
    principal_paise: int,
    initial_rate_bps: int,
    tenure_months: int,
    rate_changes: list[tuple[int, int]],  # (month, new_rate_bps)
    mode: Literal["adjust_emi", "adjust_tenure"] = "adjust_emi",
    start_date: str | None = None,
) -> list[AmortizationRow]:
    """
    Simulate schedule with multiple floating rate changes.
    """
    # Generate initial schedule
    schedule = generate_schedule(
        principal_paise=principal_paise,
        annual_rate_bps=initial_rate_bps,
        tenure_months=tenure_months,
        start_date=start_date or "2025-01-01",
    )

    # Apply rate changes in order
    for month, new_rate in sorted(rate_changes, key=lambda x: x[0]):
        if month < 1 or month > len(schedule):
            continue
        schedule = apply_floating_rate_change(
            schedule,
            month,
            new_rate,
            mode,
            start_date,
        )

    return schedule