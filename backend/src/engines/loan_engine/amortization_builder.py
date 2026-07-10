"""
Amortization Schedule Builder
=============================
Generates immutable amortization schedules for loans.

INVARIANT 3: Once generated, schedule is never modified in-place.
INVARIANT 4: All dates are ISO 8601 strings.
"""

from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal

from src.engines.loan_engine.emi_calculator import (
    compute_emi_fixed,
    compute_principal_component,
)
from src.engines.loan_engine.types import AmortizationRow


def generate_schedule(
    principal_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
    start_date: str,
    emi_paise: int | None = None,
) -> list[AmortizationRow]:
    """
    Generate full amortization schedule for a reducing balance loan.

    Returns list of AmortizationRow models.
    Schedule is immutable — returns a new list each time.

    INVARIANT 1: Money is integer paise
    INVARIANT 2: Rates stored as basis points
    INVARIANT 3: Amortization schedules are immutable
    INVARIANT 4: All dates are ISO 8601 strings
    INVARIANT 6: Banker's rounding
    """
    if emi_paise is None:
        emi_paise = compute_emi_fixed(principal_paise, annual_rate_bps, tenure_months)

    monthly_rate: Decimal = Decimal(annual_rate_bps) / Decimal(120000)
    balance: Decimal = Decimal(principal_paise)

    schedule: list[AmortizationRow] = []
    cumulative_interest: int = 0

    # Parse start date (INVARIANT 4: ISO 8601)
    start: date = date.fromisoformat(start_date)

    for month in range(1, tenure_months + 1):
        # Compute interest with Decimal precision
        interest_decimal: Decimal = balance * monthly_rate
        interest_paise = int(interest_decimal.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))

        # Compute principal component
        principal_component_paise = compute_principal_component(emi_paise, interest_paise)

        # Last payment adjustment (handles rounding)
        if month == tenure_months:
            principal_component_paise = int(balance)
            actual_emi_paise = principal_component_paise + interest_paise
        else:
            actual_emi_paise = emi_paise

        balance -= Decimal(principal_component_paise)
        cumulative_interest += interest_paise

        # Compute payment date
        year = start.year + (start.month + month - 1) // 12
        month_idx = (start.month + month - 1) % 12 or 12
        payment_date: date = date(year, month_idx, start.day)

        # Safety: ensure payment date doesn't overflow month
        try:
            payment_date = date(year, month_idx, start.day)
        except ValueError:
            # Handle Feb 30, 31 edge cases
            payment_date = date(year, month_idx, 28)

        schedule.append(AmortizationRow(
            month_number=month,
            payment_date=payment_date.isoformat(),
            emi_paise=actual_emi_paise,
            principal_paise=principal_component_paise,
            interest_paise=interest_paise,
            balance_paise=max(0, int(balance)),
            cumulative_interest_paise=cumulative_interest,
        ))

    return schedule


def regenerate_schedule(
    outstanding_paise: int,
    annual_rate_bps: int,
    remaining_months: int,
    start_date: str,
    prepayment_paise: int = 0,
) -> list[AmortizationRow]:
    """
    Regenerate schedule after prepayment or rate change.

    Returns NEW schedule — does not modify existing one (INVARIANT 3).
    """
    new_principal_paise = outstanding_paise - prepayment_paise
    if new_principal_paise <= 0:
        return []

    return generate_schedule(
        principal_paise=new_principal_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=remaining_months,
        start_date=start_date,
    )


def find_schedule_row(
    schedule: list[AmortizationRow],
    month_number: int,
) -> AmortizationRow | None:
    """Find a specific row in the schedule."""
    for row in schedule:
        if row.month_number == month_number:
            return row
    return None


def total_interest_paise(schedule: list[AmortizationRow]) -> int:
    """Compute total interest over the schedule."""
    if not schedule:
        return 0
    return schedule[-1].cumulative_interest_paise


def total_payment_paise(schedule: list[AmortizationRow]) -> int:
    """Compute total payment (principal + interest)."""
    if not schedule:
        return 0
    return sum(row.emi_paise for row in schedule)
