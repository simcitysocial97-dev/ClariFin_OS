"""
Loan Intelligence Engine Package
=================================
Modular loan calculation and optimization engine.

All monetary values in paise (integer).
All interest rates in basis points (integer).
"""

from src.engines.loan_engine.amortization_builder import (
    find_schedule_row,
    generate_schedule,
    regenerate_schedule,
    total_interest_paise,
    total_payment_paise,
    validate_schedule_invariants,
)
from src.engines.loan_engine.comparison_engine import (
    compare_loans,
    compare_prepayment_scenarios,
    generate_loan_summary,
)
from src.engines.loan_engine.dynamic_prepayment_engine import (
    apply_floating_rate_change,
    apply_multiple_prepayments,
    apply_prepayment_at_month,
    simulate_floating_rate_schedule,
)
from src.engines.loan_engine.emi_calculator import (
    compute_emi_fixed,
    compute_emi_floating,
    compute_monthly_interest,
    compute_principal_component,
)
from src.engines.loan_engine.health_scorer import (
    compute_health_score,
    get_health_insights,
    get_health_recommendations,
)
from src.engines.loan_engine.payoff_strategies import (
    compare_payoff_strategies,
    compute_minimum_payments_only,
    compute_snowball_timeline,
)
from src.engines.loan_engine.prepayment_analyzer import (
    apply_prepayment,
    compute_multiple_prepayment_savings,
    compute_savings,
)
from src.engines.loan_engine.refinance_evaluator import (
    compare_refinance_options,
    evaluate_refinance,
)
from src.engines.loan_engine.tax_calculator import (
    compare_tax_regimes,
    compute_annual_benefits,
    compute_section_24_benefit,
    compute_section_80c_benefit,
    compute_section_80ee_benefit,
    compute_section_80eea_benefit,
    compute_total_lifetime_tax_savings,
)
from src.engines.loan_engine.types import (
    AmortizationRow,
    FloatingRateChange,
    HealthScoreResult,
    InterestType,
    LoanComparisonResult,
    LoanInfo,
    LoanSummary,
    MonthlyCashFlow,
    PayoffLoanResult,
    PayoffResult,
    PayoffStrategy,
    PrepaymentMode,
    PrepaymentResult,
    RefinanceInput,
    RefinanceResult,
    TaxBenefitResult,
)

__all__ = [
    # Types
    "AmortizationRow",
    "FloatingRateChange",
    "HealthScoreResult",
    "InterestType",
    "LoanComparisonResult",
    "LoanInfo",
    "LoanSummary",
    "MonthlyCashFlow",
    "PayoffLoanResult",
    "PayoffResult",
    "PayoffStrategy",
    "PrepaymentMode",
    "PrepaymentResult",
    "RefinanceInput",
    "RefinanceResult",
    "TaxBenefitResult",
    # EMI Calculator
    "compute_emi_fixed",
    "compute_emi_floating",
    "compute_monthly_interest",
    "compute_principal_component",
    # Amortization
    "find_schedule_row",
    "generate_schedule",
    "regenerate_schedule",
    "total_interest_paise",
    "total_payment_paise",
    "validate_schedule_invariants",
    # Prepayment Analyzer
    "apply_prepayment",
    "compute_multiple_prepayment_savings",
    "compute_savings",
    # Dynamic Prepayment Engine
    "apply_floating_rate_change",
    "apply_multiple_prepayments",
    "apply_prepayment_at_month",
    "simulate_floating_rate_schedule",
    # Payoff Strategies
    "avalanche_priority",
    "compare_payoff_strategies",
    "compute_minimum_payments_only",
    "compute_snowball_timeline",
    "snowball_priority",
    # Refinance Evaluator
    "compare_refinance_options",
    "evaluate_refinance",
    # Health Scorer
    "compute_health_score",
    "get_health_insights",
    "get_health_recommendations",
    # Tax Calculator
    "compare_tax_regimes",
    "compute_annual_benefits",
    "compute_section_24_benefit",
    "compute_section_80c_benefit",
    "compute_section_80ee_benefit",
    "compute_section_80eea_benefit",
    "compute_total_lifetime_tax_savings",
    # Comparison Engine
    "compare_loans",
    "compare_prepayment_scenarios",
    "generate_loan_summary",
]