"""
Loan Intelligence Engine Package
=================================
Modular loan calculation and optimization engine.

All monetary values in paise (integer).
All interest rates in basis points (integer).
"""

from src.engines.loan_engine.amortization_builder import (
    generate_schedule,
    regenerate_schedule,
)
from src.engines.loan_engine.emi_calculator import (
    compute_emi_fixed,
    compute_emi_floating,
    compute_monthly_interest,
    compute_principal_component,
)
from src.engines.loan_engine.health_scorer import compute_health_score
from src.engines.loan_engine.payoff_strategies import avalanche_priority, snowball_priority
from src.engines.loan_engine.prepayment_analyzer import apply_prepayment, compute_savings
from src.engines.loan_engine.refinance_evaluator import evaluate_refinance
from src.engines.loan_engine.tax_calculator import (
    compute_section_24_benefit,
    compute_section_80c_benefit,
)
from src.engines.loan_engine.types import (
    AmortizationRow,
    HealthScoreResult,
    InterestType,
    LoanSummary,
    PrepaymentMode,
    PrepaymentResult,
    RefinanceInput,
    RefinanceResult,
)

__all__ = [
    # Types
    "AmortizationRow",
    "HealthScoreResult",
    "InterestType",
    "LoanSummary",
    "PrepaymentMode",
    "PrepaymentResult",
    "RefinanceInput",
    "RefinanceResult",
    # EMI Calculator
    "compute_emi_fixed",
    "compute_emi_floating",
    "compute_monthly_interest",
    "compute_principal_component",
    # Amortization
    "generate_schedule",
    "regenerate_schedule",
    # Prepayment
    "apply_prepayment",
    "compute_savings",
    # Refinance
    "evaluate_refinance",
    # Health
    "compute_health_score",
    # Tax
    "compute_section_24_benefit",
    "compute_section_80c_benefit",
    # Payoff
    "avalanche_priority",
    "snowball_priority",
]
