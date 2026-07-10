"""
Payoff Strategies
=================
Implements Avalanche and Snowball debt payoff prioritization.

INVARIANT 1-6 enforced throughout.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class LoanForPriority:
    """Minimal loan data structure for priority sorting."""
    loan_id: int
    outstanding_paise: int
    interest_rate_bps: int
    remaining_months: int


def avalanche_priority(loans: list[LoanForPriority]) -> list[int]:
    """
    Sort loans for avalanche payoff strategy.

    Priority order:
    1. Highest interest rate first
    2. Within same rate: longest tenure first (more interest to save)
    3. Minimum payment to others

    Mathematical: Minimizes total interest paid.

    Returns list of loan IDs in priority order.
    """
    sorted_loans = sorted(
        loans,
        key=lambda ln: (-ln.interest_rate_bps, -ln.remaining_months),
    )
    return [ln.loan_id for ln in sorted_loans]


def snowball_priority(loans: list[LoanForPriority]) -> list[int]:
    """
    Sort loans for snowball payoff strategy.

    Priority order:
    1. Smallest principal first
    2. Within same principal: highest rate first

    Psychological: Quick wins motivate continued payoff.

    Returns list of loan IDs in priority order.
    """
    sorted_loans = sorted(
        loans,
        key=lambda ln: (ln.outstanding_paise, -ln.interest_rate_bps),
    )
    return [ln.loan_id for ln in sorted_loans]


def compute_snowball_timeline(
    loans: list[LoanForPriority],
    monthly_surplus_paise: int,
    start_date: str = "2025-01-01",
) -> dict[str, Any]:
    """
    Compute payoff timeline using snowball method.

    Args:
        loans: List of loans with balances and rates
        monthly_surplus_paise: Extra amount available for prepayment
        start_date: ISO date for timeline start

    Returns:
        Dict with payoff_order, total_months, interest_saved_paise
    """
    from src.engines.loan_engine.amortization_builder import generate_schedule
    from src.engines.loan_engine.emi_calculator import compute_emi_fixed

    priority_order = snowball_priority(loans)

    timeline = []
    total_interest_paise = 0

    for loan_id in priority_order:
        loan = next(ln for ln in loans if ln.loan_id == loan_id)

        # Assume EMI is computed at original terms
        compute_emi_fixed(
            loan.outstanding_paise,
            loan.interest_rate_bps,
            loan.remaining_months,
        )

        # With surplus, compute new timeline
        schedule = generate_schedule(
            principal_paise=loan.outstanding_paise,
            annual_rate_bps=loan.interest_rate_bps,
            tenure_months=loan.remaining_months,
            start_date=start_date,
        )

        # Find when loan pays off with extra payment
        months_to_close = 0
        running_balance = loan.outstanding_paise
        total_interest = 0

        for row in schedule:
            months_to_close += 1
            total_interest += row.interest_paise
            # Add surplus to principal
            running_balance = row.balance_paise - monthly_surplus_paise
            if running_balance <= 0:
                break

        total_interest_paise += total_interest
        timeline.append({
            "loan_id": loan_id,
            "months_to_close": months_to_close,
            "interest_paise": total_interest,
        })

    return {
        "payoff_order": priority_order,
        "timeline": timeline,
        "total_months": sum(t["months_to_close"] for t in timeline),
        "total_interest_paise": total_interest_paise,
    }


def compute_avalanche_timeline(
    loans: list[LoanForPriority],
    monthly_surplus_paise: int,
    start_date: str = "2025-01-01",
) -> dict[str, Any]:
    """
    Compute payoff timeline using avalanche method.

    Same as snowball but with avalanche priority order.
    """
    from src.engines.loan_engine.amortization_builder import generate_schedule

    priority_order = avalanche_priority(loans)

    timeline = []
    total_interest_paise = 0

    for loan_id in priority_order:
        loan = next(ln for ln in loans if ln.loan_id == loan_id)

        schedule = generate_schedule(
            principal_paise=loan.outstanding_paise,
            annual_rate_bps=loan.interest_rate_bps,
            tenure_months=loan.remaining_months,
            start_date=start_date,
        )

        months_to_close = 0
        running_balance = loan.outstanding_paise
        total_interest = 0

        for row in schedule:
            months_to_close += 1
            total_interest += row.interest_paise
            running_balance = row.balance_paise - monthly_surplus_paise
            if running_balance <= 0:
                break

        total_interest_paise += total_interest
        timeline.append({
            "loan_id": loan_id,
            "months_to_close": months_to_close,
            "interest_paise": total_interest,
        })

    return {
        "payoff_order": priority_order,
        "timeline": timeline,
        "total_months": sum(t["months_to_close"] for t in timeline),
        "total_interest_paise": total_interest_paise,
    }
