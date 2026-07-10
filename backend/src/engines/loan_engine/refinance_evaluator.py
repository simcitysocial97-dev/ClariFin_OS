"""
Refinance Evaluator
===================
Evaluates refinance opportunities with break-even analysis and tax benefits.

INVARIANT 1-6 enforced throughout.
"""

from src.engines.loan_engine.amortization_builder import (
    generate_schedule,
    total_interest_paise,
)
from src.engines.loan_engine.emi_calculator import compute_emi_fixed
from src.engines.loan_engine.types import RefinanceInput, RefinanceResult

def evaluate_refinance(input: RefinanceInput) -> RefinanceResult:
    """
    Evaluate refinance opportunity.

    Break-even analysis:
    - One_time_cost = processing_fees + prepayment_penalty
    - EMI_savings = Old_EMI - New_EMI
    - Break_even_months = One_time_cost / EMI_savings

    INVARIANT 1: Money in paise
    INVARIANT 2: Rate in basis points
    """
    # Compute new EMI
    new_emi_paise = compute_emi_fixed(
        input.current_outstanding_paise,
        input.new_rate_bps,
        input.new_tenure_months,
    )

    emi_savings_paise = input.current_emi_paise - new_emi_paise

    # One-time cost: processing fees + prepayment penalty
    one_time_cost_paise = input.processing_fees_paise + input.prepayment_penalty_paise

    # Break-even months
    if emi_savings_paise > 0:
        break_even_months = one_time_cost_paise / emi_savings_paise
        # Round up to nearest month
        break_even_months = int(break_even_months) + (1 if break_even_months % 1 > 0 else 0)
    else:
        break_even_months = 999  # Never beneficial

    # Compute interest over remaining term for tax benefits
    current_schedule = generate_schedule(
        principal_paise=input.current_outstanding_paise,
        annual_rate_bps=input.current_rate_bps,
        tenure_months=input.remaining_months,
        start_date=input.start_date or "2025-01-01",
    )

    new_schedule = generate_schedule(
        principal_paise=input.current_outstanding_paise,
        annual_rate_bps=input.new_rate_bps,
        tenure_months=input.new_tenure_months,
        start_date=input.start_date or "2025-01-01",
    )

    current_interest = total_interest_paise(current_schedule)
    new_interest = total_interest_paise(new_schedule)

    # Tax benefit difference (configurable tax rate and limits)
    tax_benefit_diff = compute_tax_adjusted_savings(
        current_interest,
        new_interest,
        input.tax_rate_bps,
        input.section_24_limit_paise,
    )

    # Total gross savings
    gross_savings_paise = current_interest - new_interest

    # Net savings including tax benefits
    net_savings_paise = gross_savings_paise - tax_benefit_diff

    return RefinanceResult(
        current_rate_bps=input.current_rate_bps,
        new_rate_bps=input.new_rate_bps,
        current_emi_paise=input.current_emi_paise,
        new_emi_paise=new_emi_paise,
        emi_savings_paise=emi_savings_paise,
        one_time_cost_paise=one_time_cost_paise,
        break_even_months=break_even_months,
        remaining_months=input.remaining_months,
        is_beneficial=(break_even_months < input.remaining_months and emi_savings_paise > 0),
        gross_savings_paise=gross_savings_paise,
        tax_benefit_difference_paise=tax_benefit_diff,
        net_savings_paise=net_savings_paise,
    )

def compute_tax_adjusted_savings(
    old_interest_paise: int,
    new_interest_paise: int,
    tax_rate_bps: int = 2000,  # 20% = 2000 bps
    section_24_limit_paise: int = 20000000,  # ₹2,00,000 = 20,000,000 paise
    section_80c_limit_paise: int = 15000000,  # ₹1,50,000 = 15,000,000 paise
) -> int:
    """
    Compute tax-adjusted savings for refinance.

    Handles multiple tax sections:
    - Section 24: Home loan interest (up to limit)
    - Section 80C: Principal repayment (up to limit)

    Returns additional tax cost from refinance (positive = higher tax burden).
    """
    # Section 24: Home loan interest
    old_section_24 = min(old_interest_paise, section_24_limit_paise)
    new_section_24 = min(new_interest_paise, section_24_limit_paise)
    section_24_diff = (old_section_24 - new_section_24) * tax_rate_bps / 10000

    # Section 80C: Principal repayment (simplified - assumes same principal repayment)
    # For refinance, principal repayment is typically similar, so we ignore this
    # unless there's a significant difference in tenure

    # Total tax difference (convert to paise)
    tax_difference_paise = int(section_24_diff * 100)

    return tax_difference_paise

def should_refinance(
    break_even_months: int,
    remaining_months: int,
) -> bool:
    """Determine if refinance is beneficial."""
    return break_even_months < remaining_months and break_even_months > 0

def compare_refinance_options(
    current_loan: RefinanceInput,
    options: list[RefinanceInput],
) -> list[RefinanceResult]:
    """
    Compare multiple refinance options side-by-side.

    Returns list of RefinanceResult for each option.
    """
    results = []
    for option in options:
        result = evaluate_refinance(option)
        results.append(result)
    return results