"""
Loan Comparison Engine
======================
Compares multiple loan options side-by-side with comprehensive metrics.

INVARIANT 1-6 enforced throughout.
"""

from src.engines.loan_engine.amortization_builder import (
    generate_schedule,
    total_interest_paise,
    total_payment_paise,
)
from src.engines.loan_engine.dynamic_prepayment_engine import (
    apply_multiple_prepayments,
    simulate_floating_rate_schedule,
)
from src.engines.loan_engine.health_scorer import compute_health_score
from src.engines.loan_engine.tax_calculator import compute_total_lifetime_tax_savings
from src.engines.loan_engine.types import (
    FloatingRateChange,
    InterestType,
    LoanComparisonResult,
    LoanInfo,
    LoanSummary,
)

def compare_loans(
    loan_options: list[LoanInfo],
    monthly_income_paise: int,
    sanction_amount_paise: int,
    credit_score: int = 0,
    ltv_ratio: float = 0.0,
    is_self_occupied: bool = True,
    is_first_time_buyer: bool = False,
    is_affordable_housing: bool = False,
    loan_sanction_date: str | None = None,
    property_value_paise: int = 0,
    other_80c_investments_paise: int = 0,
    stamp_duty_paise: int = 0,
    registration_charges_paise: int = 0,
    prepayment_scenarios: list[list[tuple[int, int]]] | None = None,
) -> list[LoanComparisonResult]:
    """
    Compare multiple loan options side-by-side.

    Args:
        loan_options: List of loan options to compare
        monthly_income_paise: Borrower's monthly income for DTI calculation
        sanction_amount_paise: Original sanction amount for utilization score
        credit_score: Borrower's credit score
        ltv_ratio: Loan-to-value ratio
        is_self_occupied: True if property is self-occupied
        is_first_time_buyer: True for first-time homebuyers
        is_affordable_housing: True for affordable housing
        loan_sanction_date: Date when loan was sanctioned
        property_value_paise: Property value in paise
        other_80c_investments_paise: Other 80C investments
        stamp_duty_paise: Stamp duty paid
        registration_charges_paise: Registration charges paid
        prepayment_scenarios: List of prepayment scenarios (one per loan)

    Returns:
        List of LoanComparisonResult with comparison metrics
    """
    if not loan_options:
        return []

    if prepayment_scenarios is None:
        prepayment_scenarios = [[] for _ in loan_options]
    elif len(prepayment_scenarios) != len(loan_options):
        raise ValueError("Prepayment scenarios must match loan options count")

    results = []

    for i, loan in enumerate(loan_options):
        # Generate base schedule
        if loan.interest_type == InterestType.FLOATING:
            # For floating rate, use initial rate and simulate rate changes
            schedule = simulate_floating_rate_schedule(
                principal_paise=loan.outstanding_paise,
                initial_rate_bps=loan.annual_rate_bps,
                tenure_months=loan.remaining_months,
                rate_changes=loan.rate_changes or [],
                start_date=loan.start_date,
            )
        else:
            # For fixed rate, generate standard schedule
            schedule = generate_schedule(
                principal_paise=loan.outstanding_paise,
                annual_rate_bps=loan.annual_rate_bps,
                tenure_months=loan.remaining_months,
                start_date=loan.start_date,
            )

        # Apply prepayment scenario if provided
        if prepayment_scenarios[i]:
            schedule, _ = apply_multiple_prepayments(
                schedule,
                prepayment_scenarios[i],
                loan.annual_rate_bps,
                loan.prepayment_penalty_bps,
                "reduce_tenure",
                loan.start_date,
            )

        # Compute total cost metrics
        total_interest = total_interest_paise(schedule)
        total_payment = total_payment_paise(schedule)
        total_cost = total_payment + loan.processing_fees_paise

        # Compute health score
        health_score = compute_health_score(
            monthly_emi_paise=loan.emi_paise,
            monthly_income_paise=monthly_income_paise,
            sanction_amount_paise=sanction_amount_paise,
            outstanding_paise=loan.outstanding_paise,
            missed_payments=0,  # Assume no missed payments for comparison
            total_payments=loan.remaining_months,
            months_since_start=0,  # Assume new loan for comparison
            other_debt_paise=0,
            credit_score=credit_score,
            ltv_ratio=ltv_ratio,
        ).overall_score

        # Compute tax benefits
        tax_benefits = compute_total_lifetime_tax_savings(
            principal_paise=loan.outstanding_paise,
            annual_rate_bps=loan.annual_rate_bps,
            tenure_months=loan.remaining_months,
            start_date=loan.start_date,
            is_new_regime=False,  # Use old regime for comparison
            is_self_occupied=is_self_occupied,
            is_first_time_buyer=is_first_time_buyer,
            is_affordable_housing=is_affordable_housing,
            loan_sanction_date=loan_sanction_date,
            property_value_paise=property_value_paise,
            other_80c_investments_paise=other_80c_investments_paise,
            stamp_duty_paise=stamp_duty_paise,
            registration_charges_paise=registration_charges_paise,
        )

        results.append(LoanComparisonResult(
            loan_id=loan.loan_id,
            total_cost_paise=total_cost,
            total_interest_paise=total_interest,
            total_payment_paise=total_payment,
            tenure_months=len(schedule),
            emi_paise=loan.emi_paise,
            is_best=False,
        ))

    # Mark the best option (lowest total cost)
    if results:
        min_cost = min(result.total_cost_paise for result in results)
        for result in results:
            if result.total_cost_paise == min_cost:
                result.is_best = True

    return results

def generate_loan_summary(
    loan: LoanInfo,
    monthly_income_paise: int,
    sanction_amount_paise: int,
    credit_score: int = 0,
    ltv_ratio: float = 0.0,
) -> LoanSummary:
    """
    Generate comprehensive summary for a single loan.

    Includes health score, key metrics, and recommendations.
    """
    # Generate schedule for metrics
    schedule = generate_schedule(
        principal_paise=loan.outstanding_paise,
        annual_rate_bps=loan.annual_rate_bps,
        tenure_months=loan.remaining_months,
        start_date=loan.start_date,
    )

    # Compute health score
    health_score = compute_health_score(
        monthly_emi_paise=loan.emi_paise,
        monthly_income_paise=monthly_income_paise,
        sanction_amount_paise=sanction_amount_paise,
        outstanding_paise=loan.outstanding_paise,
        missed_payments=0,  # Assume no missed payments
        total_payments=loan.remaining_months,
        months_since_start=0,  # Assume new loan
        other_debt_paise=0,
        credit_score=credit_score,
        ltv_ratio=ltv_ratio,
    )

    return LoanSummary(
        loan_id=loan.loan_id,
        name=loan.name,
        lender=loan.lender,
        loan_type=loan.interest_type.value if hasattr(loan, 'interest_type') else "fixed",
        principal_paise=loan.outstanding_paise,
        outstanding_paise=loan.outstanding_paise,
        interest_rate_bps=loan.annual_rate_bps,
        tenure_months=loan.remaining_months,
        emi_paise=loan.emi_paise,
        health_score=health_score.overall_score,
        annual_rate_bps=loan.annual_rate_bps,
        remaining_months=loan.remaining_months,
        start_date=loan.start_date,
    )

def compare_prepayment_scenarios(
    loan: LoanInfo,
    scenarios: list[list[tuple[int, int]]],  # List of prepayment scenarios
    monthly_income_paise: int,
    sanction_amount_paise: int,
    credit_score: int = 0,
    ltv_ratio: float = 0.0,
) -> list[LoanComparisonResult]:
    """
    Compare different prepayment scenarios for a single loan.

    Returns comparison of total cost, interest saved, and tenure reduction.
    """
    results = []

    # Base scenario (no prepayments)
    base_schedule = generate_schedule(
        principal_paise=loan.outstanding_paise,
        annual_rate_bps=loan.annual_rate_bps,
        tenure_months=loan.remaining_months,
        start_date=loan.start_date,
    )

    base_interest = total_interest_paise(base_schedule)
    base_payment = total_payment_paise(base_schedule)
    base_cost = base_payment + loan.processing_fees_paise

    results.append(LoanComparisonResult(
        loan_id=loan.loan_id,
        total_cost_paise=base_cost,
        total_interest_paise=base_interest,
        total_payment_paise=base_payment,
        tenure_months=len(base_schedule),
        emi_paise=loan.emi_paise,
        is_best=False,
    ))

    # Compare each scenario
    for i, scenario in enumerate(scenarios):
        schedule, _ = apply_multiple_prepayments(
            base_schedule,
            scenario,
            loan.annual_rate_bps,
            loan.prepayment_penalty_bps,
            "reduce_tenure",
            loan.start_date,
        )

        total_interest = total_interest_paise(schedule)
        total_payment = total_payment_paise(schedule)
        total_cost = total_payment + loan.processing_fees_paise

        # Compute health score improvement
        health_score = compute_health_score(
            monthly_emi_paise=loan.emi_paise,
            monthly_income_paise=monthly_income_paise,
            sanction_amount_paise=sanction_amount_paise,
            outstanding_paise=loan.outstanding_paise - sum(amount for _, amount in scenario),
            missed_payments=0,
            total_payments=loan.remaining_months,
            months_since_start=0,
            other_debt_paise=0,
            credit_score=credit_score,
            ltv_ratio=ltv_ratio,
        )

        results.append(LoanComparisonResult(
            loan_id=loan.loan_id,
            total_cost_paise=total_cost,
            total_interest_paise=total_interest,
            total_payment_paise=total_payment,
            tenure_months=len(schedule),
            emi_paise=loan.emi_paise,
            is_best=False,
        ))

    # Mark the best scenario (lowest total cost)
    if results:
        min_cost = min(result.total_cost_paise for result in results)
        for result in results:
            if result.total_cost_paise == min_cost:
                result.is_best = True

    return results