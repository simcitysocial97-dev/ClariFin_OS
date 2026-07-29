"""
Loan Metrics - Pure calculation module
"""

from .amortization import total_interest_paise
from .models import AmortizationRow, LoanMetrics


def compute_loan_metrics(
    schedule: list[AmortizationRow],
    original_principal_paise: int,
) -> LoanMetrics:
    if not schedule:
        return LoanMetrics(
            outstanding_paise=0,
            principal_paid_paise=0,
            interest_paid_paise=0,
            remaining_interest_paise=0,
            remaining_tenure_months=0,
            tenure_saved_months=0,
            total_payments_remaining=0,
            effective_interest_ratio=0.0,
        )

    # The schedule is the remaining period. The outstanding at the start of this period is:
    # balance after first payment + principal of first payment = opening balance.
    first_row = schedule[0]
    outstanding = first_row.balance_paise + first_row.principal_paise
    # But if the schedule is a full schedule, the first payment's opening balance is original principal.
    # However, we can just use the first row's balance + principal, which equals opening balance.

    total_interest = total_interest_paise(schedule)
    total_principal_paid = original_principal_paise - outstanding
    remaining_tenure = len(schedule)
    total_payments_remaining = sum(row.emi_paise for row in schedule)

    effective_ratio = total_interest / original_principal_paise if original_principal_paise > 0 else 0.0

    return LoanMetrics(
        outstanding_paise=outstanding,
        principal_paid_paise=total_principal_paid,
        interest_paid_paise=0,
        remaining_interest_paise=total_interest,
        remaining_tenure_months=remaining_tenure,
        tenure_saved_months=0,
        total_payments_remaining=total_payments_remaining,
        effective_interest_ratio=round(effective_ratio, 4),
    )


def calculate_interest_saved(
    original_schedule: list[AmortizationRow],
    new_schedule: list[AmortizationRow],
    prepayment_paise: int = 0,
) -> int:
    original_interest = sum(row.interest_paise for row in original_schedule)
    new_interest = sum(row.interest_paise for row in new_schedule)
    saved = original_interest - new_interest - prepayment_paise
    return max(0, saved)


def calculate_tenure_saved(
    original_schedule: list[AmortizationRow],
    new_schedule: list[AmortizationRow],
) -> int:
    return len(original_schedule) - len(new_schedule)


def get_interest_component(
    principal_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
) -> int:
    from .amortization import generate_schedule
    schedule = generate_schedule(
        principal_paise=principal_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=tenure_months,
        start_date="2025-01-01",
    )
    return total_interest_paise(schedule)


def get_emi_component(
    principal_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
) -> int:
    from .emi import compute_emi_fixed
    return compute_emi_fixed(principal_paise, annual_rate_bps, tenure_months)
