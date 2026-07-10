"""
Payoff Strategies Engine
========================
Simulates debt payoff strategies (Avalanche, Snowball) with accurate interest savings.

INVARIANT 1-6 enforced throughout.
"""

from decimal import Decimal
from typing import Literal

from src.engines.loan_engine.amortization_builder import (
    generate_schedule,
    total_interest_paise,
)
from src.engines.loan_engine.dynamic_prepayment_engine import (
    apply_multiple_prepayments,
    apply_prepayment_at_month,
)
from src.engines.loan_engine.types import (
    AmortizationRow,
    LoanInfo,
    PayoffResult,
    PayoffStrategy,
    PrepaymentResult,
)

def compute_snowball_timeline(
    loans: list[LoanInfo],
    monthly_surplus_paise: int,
    strategy: Literal["snowball", "avalanche"] = "snowball",
) -> PayoffResult:
    """
    Compute payoff timeline for snowball or avalanche strategy.

    Uses dynamic prepayment engine to accurately simulate month-by-month payoff.

    INVARIANT 1: All money values in paise
    INVARIANT 3: Returns new data, never mutates input
    """
    if not loans:
        return PayoffResult(
            strategy=PayoffStrategy(strategy),
            total_months=0,
            total_interest_paise=0,
            monthly_cash_flow=[],
            loan_results=[],
        )

    # Create initial schedules for all loans
    loan_schedules = []
    for loan in loans:
        schedule = generate_schedule(
            principal_paise=loan.outstanding_paise,
            annual_rate_bps=loan.annual_rate_bps,
            tenure_months=loan.remaining_months,
            start_date=loan.start_date,
        )
        loan_schedules.append((loan, schedule))

    # Track active loans and their current state
    active_loans = loan_schedules.copy()
    monthly_cash_flow = []
    total_interest = 0
    current_month = 0
    loan_results = []

    # Sort loans based on strategy
    if strategy == "avalanche":
        # Highest interest rate first
        active_loans.sort(key=lambda x: x[0].annual_rate_bps, reverse=True)
    else:
        # Smallest balance first (snowball)
        active_loans.sort(key=lambda x: x[0].outstanding_paise)

    while active_loans:
        current_month += 1
        total_payment_this_month = 0
        monthly_interest = 0

        # Pay minimum payments on all active loans
        for loan, schedule in active_loans:
            if current_month <= len(schedule):
                monthly_interest += schedule[current_month - 1].interest_paise
                total_payment_this_month += schedule[current_month - 1].emi_paise

        # Apply surplus to the first loan in the strategy
        remaining_surplus = monthly_surplus_paise
        new_active_loans = []

        for i, (loan, schedule) in enumerate(active_loans):
            if current_month > len(schedule):
                # Loan is already paid off
                loan_results.append({
                    "loan_id": loan.loan_id,
                    "months_to_payoff": current_month - 1,
                    "total_interest_paise": total_interest_paise(schedule),
                    "total_payment_paise": sum(row.emi_paise for row in schedule),
                })
                continue

            # Apply minimum payment
            min_payment = schedule[current_month - 1].emi_paise

            if i == 0 and remaining_surplus > 0:
                # This is the target loan for the strategy
                additional_payment = min(remaining_surplus, schedule[current_month - 1].balance_paise)
                total_payment = min_payment + additional_payment

                # Apply prepayment to this loan
                _, prepayment_result = apply_prepayment_at_month(
                    schedule,
                    current_month,
                    additional_payment,
                    loan.annual_rate_bps,
                    loan.prepayment_penalty_bps,
                    "reduce_tenure",
                    loan.start_date,
                )

                # Check if loan is paid off
                if prepayment_result.loan_closed:
                    loan_results.append({
                        "loan_id": loan.loan_id,
                        "months_to_payoff": current_month,
                        "total_interest_paise": total_interest_paise(prepayment_result.new_schedule),
                        "total_payment_paise": sum(row.emi_paise for row in prepayment_result.new_schedule) + additional_payment,
                    })
                    # Add freed up EMI to surplus for next month
                    remaining_surplus += min_payment
                else:
                    # Loan still active, update schedule
                    new_active_loans.append((loan, prepayment_result.new_schedule))
                    # Surplus is used up
                    remaining_surplus = 0
            else:
                # Just pay minimum
                new_active_loans.append((loan, schedule))

        # Update active loans for next month
        active_loans = new_active_loans

        # Track monthly cash flow
        monthly_cash_flow.append({
            "month": current_month,
            "total_payment_paise": total_payment_this_month + (monthly_surplus_paise - remaining_surplus),
            "interest_paise": monthly_interest,
            "principal_paise": (total_payment_this_month + (monthly_surplus_paise - remaining_surplus)) - monthly_interest,
        })

        # Update total interest
        total_interest += monthly_interest

    return PayoffResult(
        strategy=PayoffStrategy(strategy),
        total_months=current_month,
        total_interest_paise=total_interest,
        monthly_cash_flow=monthly_cash_flow,
        loan_results=loan_results,
    )

def compute_minimum_payments_only(
    loans: list[LoanInfo],
) -> PayoffResult:
    """
    Compute timeline for minimum payments only (baseline comparison).
    """
    if not loans:
        return PayoffResult(
            strategy=PayoffStrategy("minimum"),
            total_months=0,
            total_interest_paise=0,
            monthly_cash_flow=[],
            loan_results=[],
        )

    # Find the longest loan duration
    max_months = max(loan.remaining_months for loan in loans)
    total_interest = 0
    monthly_cash_flow = []
    loan_results = []

    for month in range(1, max_months + 1):
        monthly_payment = 0
        monthly_interest = 0

        for loan in loans:
            if month <= loan.remaining_months:
                # Generate schedule for this loan to get exact payment
                schedule = generate_schedule(
                    principal_paise=loan.outstanding_paise,
                    annual_rate_bps=loan.annual_rate_bps,
                    tenure_months=loan.remaining_months,
                    start_date=loan.start_date,
                )
                if month <= len(schedule):
                    monthly_payment += schedule[month - 1].emi_paise
                    monthly_interest += schedule[month - 1].interest_paise

        total_interest += monthly_interest
        monthly_cash_flow.append({
            "month": month,
            "total_payment_paise": monthly_payment,
            "interest_paise": monthly_interest,
            "principal_paise": monthly_payment - monthly_interest,
        })

    # Generate loan results
    for loan in loans:
        schedule = generate_schedule(
            principal_paise=loan.outstanding_paise,
            annual_rate_bps=loan.annual_rate_bps,
            tenure_months=loan.remaining_months,
            start_date=loan.start_date,
        )
        loan_results.append({
            "loan_id": loan.loan_id,
            "months_to_payoff": loan.remaining_months,
            "total_interest_paise": total_interest_paise(schedule),
            "total_payment_paise": sum(row.emi_paise for row in schedule),
        })

    return PayoffResult(
        strategy=PayoffStrategy("minimum"),
        total_months=max_months,
        total_interest_paise=total_interest,
        monthly_cash_flow=monthly_cash_flow,
        loan_results=loan_results,
    )

def compare_payoff_strategies(
    loans: list[LoanInfo],
    monthly_surplus_paise: int,
) -> dict[str, PayoffResult]:
    """
    Compare all payoff strategies side-by-side.

    Returns dict with results for each strategy.
    """
    strategies = {}

    # Minimum payments baseline
    strategies["minimum"] = compute_minimum_payments_only(loans)

    # Snowball strategy
    strategies["snowball"] = compute_snowball_timeline(loans, monthly_surplus_paise, "snowball")

    # Avalanche strategy
    strategies["avalanche"] = compute_snowball_timeline(loans, monthly_surplus_paise, "avalanche")

    return strategies