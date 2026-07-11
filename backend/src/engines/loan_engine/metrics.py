"""
Loan Metrics - Pure calculation module
=====================================
Computes factual metrics for loans without recommendations.
"""

from .amortization import total_interest_paise
from .models import AmortizationRow, LoanMetrics


def compute_loan_metrics(
    schedule: list[AmortizationRow],
    original_principal_paise: int,
) -> LoanMetrics:
    """
    Compute pure metrics for a loan schedule.

    Returns factual values only - no recommendations.
    """
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

    # Current outstanding (last balance is 0, so first balance is the original)
    # For a schedule in progress, we need the current balance
    # This assumes schedule is for remaining period
    current_outstanding = schedule[0].balance_paise if len(schedule) > 1 else 0

    # For a full schedule, we need to know months elapsed
    # This is simplified - assumes schedule passed is remaining schedule
    total_principal_paid = original_principal_paise - current_outstanding
    total_interest_paid = total_interest_paise(schedule)
    total_payments_remaining = len(schedule)

    # Interest ratio
    if original_principal_paise > 0:
        interest_ratio = total_interest_paid / original_principal_paise
    else:
        interest_ratio = 0.0

    return LoanMetrics(
        outstanding_paise=current_outstanding,
        principal_paid_paise=total_principal_paid,
        interest_paid_paise=total_interest_paid,
        remaining_interest_paise=total_interest_paise(schedule),
        remaining_tenure_months=len(schedule),
        tenure_saved_months=0,
        total_payments_remaining=total_payments_remaining,
        effective_interest_ratio=round(interest_ratio, 4),
    )


def calculate_interest_saved(
    original_schedule: list[AmortizationRow],
    new_schedule: list[AmortizationRow],
    prepayment_paise: int = 0,
) -> int:
    """
    Calculate interest saved from prepayment.

    Returns max(0, original_interest - new_interest - prepayment_cost)
    """
    original_interest = sum(row.interest_paise for row in original_schedule)
    new_interest = sum(row.interest_paise for row in new_schedule)

    return max(0, original_interest - new_interest - prepayment_paise)


def calculate_tenure_saved(
    original_schedule: list[AmortizationRow],
    new_schedule: list[AmortizationRow],
) -> int:
    """
    Calculate months saved from prepayment.
    """
    return len(original_schedule) - len(new_schedule)


def get_interest_component(
    principal_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
) -> int:
    """
    Get total interest component for a loan.

    Useful for comparing loan costs.
    """
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
    """
    Get EMI for a loan.
    """
    from .emi import compute_emi_fixed

    return compute_emi_fixed(principal_paise, annual_rate_bps, tenure_months)
