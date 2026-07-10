"""
Refinance Evaluator
===================
Evaluates refinance opportunities with break-even analysis.

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
    - Savings_per_month = Old_EMI - New_EMI
    - One_time_cost = New_Principal - Old_Outstanding + processing_fees
    - Break_even_months = One_time_cost / Savings_per_month

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

    # One-time cost: difference in principal + processing fees
    one_time_cost_paise = input.current_outstanding_paise - new_emi_paise * input.new_tenure_months
    one_time_cost_paise = max(0, one_time_cost_paise) + input.processing_fees_paise

    # Break-even months
    if emi_savings_paise > 0:
        break_even_months = int((one_time_cost_paise + input.processing_fees_paise) / emi_savings_paise)
    else:
        break_even_months = 999  # Never beneficial

    # Compute interest over remaining term for tax benefits
    current_schedule = generate_schedule(
        principal_paise=input.current_outstanding_paise,
        annual_rate_bps=input.current_rate_bps,
        tenure_months=input.remaining_months,
        start_date="2025-01-01",
    )

    new_schedule = generate_schedule(
        principal_paise=input.current_outstanding_paise,
        annual_rate_bps=input.new_rate_bps,
        tenure_months=input.new_tenure_months,
        start_date="2025-01-01",
    )

    current_interest = total_interest_paise(current_schedule)
    new_interest = total_interest_paise(new_schedule)

    # Tax benefit difference (assuming 20% tax bracket, Section 24 limit)
    # Section 24: max ₹2,00,000 old regime, ₹3,00,000 new regime
    tax_rate_bps = 2000  # 20% = 2000 bps

    old_tax_benefit = min(current_interest, 20000000) * tax_rate_bps / 10000  # 2L limit
    new_tax_benefit = min(new_interest, 30000000) * tax_rate_bps / 10000  # 3L limit
    tax_benefit_diff = int((old_tax_benefit - new_tax_benefit) * 100)  # Convert to paise

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
        gross_savings_paise=int(gross_savings_paise),
        tax_benefit_difference_paise=tax_benefit_diff,
        net_savings_paise=int(net_savings_paise),
    )


def compute_tax_adjusted_savings(
    old_interest_paise: int,
    new_interest_paise: int,
    tax_rate_bps: int = 2000,
    section_24_limit_paise: int = 20000000,
) -> int:
    """
    Compute tax-adjusted savings for refinance.

    Returns additional savings from tax benefits.
    """
    old_tax = min(old_interest_paise, section_24_limit_paise) * tax_rate_bps / 10000
    new_tax = min(new_interest_paise, section_24_limit_paise) * tax_rate_bps / 10000
    return int((old_tax - new_tax) * 100)  # Paise


def should_refinance(
    break_even_months: int,
    remaining_months: int,
) -> bool:
    """Determine if refinance is beneficial."""
    return break_even_months < remaining_months and break_even_months > 0
