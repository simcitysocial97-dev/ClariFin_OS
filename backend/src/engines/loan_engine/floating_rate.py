"""
Floating Rate Engine - Pure calculation module
===========================================
Handles manual rate changes for floating rate loans.
"""

from typing import Literal

from .models import AmortizationRow, FloatingRateChange
from .prepayment import regenerate_schedule


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

    # Compute start date for regenerated schedule
    schedule_start_date = start_date
    if schedule_start_date is None:
        schedule_start_date = schedule[change_month - 1].payment_date

    # Generate new schedule from change month onwards
    new_regenerated = regenerate_schedule(
        schedule[change_month - 1:],
        remaining_balance,
        new_rate_bps,
        "reduce_emi" if mode == "adjust_emi" else "reduce_tenure",
        schedule_start_date,
    )

    # Combine completed schedule with regenerated portion
    completed_portion = schedule[:change_month - 1] if change_month > 1 else []
    return completed_portion + new_regenerated


def simulate_floating_rate_schedule(
    principal_paise: int,
    initial_rate_bps: int,
    tenure_months: int,
    rate_changes: list[tuple[int, int]] | list[FloatingRateChange],  # (month, new_rate_bps) or FloatingRateChange objects
    mode: Literal["adjust_emi", "adjust_tenure"] = "adjust_emi",
    start_date: str | None = None,
) -> list[AmortizationRow]:
    """
    Simulate schedule with multiple floating rate changes.
    """
    from .amortization import generate_schedule

    # Generate initial schedule
    schedule = generate_schedule(
        principal_paise=principal_paise,
        annual_rate_bps=initial_rate_bps,
        tenure_months=tenure_months,
        start_date=start_date or "2025-01-01",
    )

    # Apply rate changes in order
    def get_change_month(change: tuple[int, int] | FloatingRateChange) -> int:
        return change[0] if isinstance(change, tuple) else change.change_month

    def get_new_rate(change: tuple[int, int] | FloatingRateChange) -> int:
        return change[1] if isinstance(change, tuple) else change.new_rate_bps

    def get_change_mode(change: tuple[int, int] | FloatingRateChange) -> Literal["adjust_emi", "adjust_tenure"]:
        if isinstance(change, tuple):
            # tuple can have 2 or 3 elements
            return change[2] if len(change) > 2 else "adjust_emi"
        return change.mode if change.mode in ("adjust_emi", "adjust_tenure") else "adjust_emi"

    sorted_changes = sorted(rate_changes, key=get_change_month)
    for change in sorted_changes:
        month = get_change_month(change)
        new_rate = get_new_rate(change)
        change_mode = get_change_mode(change)
        if month < 1 or month > len(schedule):
            continue
        schedule = apply_floating_rate_change(
            schedule,
            month,
            new_rate,
            change_mode,
            start_date,
        )

    return schedule
