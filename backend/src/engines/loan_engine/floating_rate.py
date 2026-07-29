"""
Floating Rate Engine - Pure calculation module
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
    if change_month < 1 or change_month > len(schedule):
        raise ValueError(f"Change month {change_month} out of range")
    if new_rate_bps < 0:
        raise ValueError("Rate cannot be negative")

    change_row = schedule[change_month - 1]
    # Balance before change month's payment
    opening_balance = change_row.balance_paise + change_row.principal_paise
    remaining_tenure = len(schedule) - change_month + 1
    current_emi = change_row.emi_paise

    # Determine mode for regeneration
    regen_mode: Literal["reduce_tenure", "reduce_emi"] = (
        "reduce_emi" if mode == "adjust_emi" else "reduce_tenure"
    )

    # For adjust_emi: keep tenure, change EMI -> reduce_emi mode
    # For adjust_tenure: keep EMI, change tenure -> reduce_tenure mode
    if mode == "adjust_emi":
        tail = regenerate_schedule(
            schedule[change_month - 1:],
            opening_balance,
            new_rate_bps,
            "reduce_emi",
            change_row.payment_date,
            original_emi=None,
            original_tenure=remaining_tenure,
        )
    else:  # adjust_tenure
        tail = regenerate_schedule(
            schedule[change_month - 1:],
            opening_balance,
            new_rate_bps,
            "reduce_tenure",
            change_row.payment_date,
            original_emi=current_emi,
            original_tenure=None,
        )

    prefix = schedule[:change_month - 1] if change_month > 1 else []
    return prefix + tail


def simulate_floating_rate_schedule(
    principal_paise: int,
    initial_rate_bps: int,
    tenure_months: int,
    rate_changes: list[tuple[int, int]] | list[FloatingRateChange],
    mode: Literal["adjust_emi", "adjust_tenure"] = "adjust_emi",
    start_date: str | None = None,
) -> list[AmortizationRow]:
    from .amortization import generate_schedule

    schedule = generate_schedule(
        principal_paise=principal_paise,
        annual_rate_bps=initial_rate_bps,
        tenure_months=tenure_months,
        start_date=start_date or "2025-01-01",
    )

    def get_change_month(change):
        return change[0] if isinstance(change, tuple) else change.change_month

    def get_new_rate(change):
        return change[1] if isinstance(change, tuple) else change.new_rate_bps

    def get_mode(change):
        if isinstance(change, tuple):
            return change[2] if len(change) > 2 else "adjust_emi"
        return change.mode

    sorted_changes = sorted(rate_changes, key=get_change_month)
    for change in sorted_changes:
        month = get_change_month(change)
        new_rate = get_new_rate(change)
        change_mode = get_mode(change)
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
