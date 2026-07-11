"""
Domain models for Loan Engine - Out-of-scope types kept for backward compatibility.
All monetary values in paise (integer).
All interest rates in basis points (integer).

NOTE: These types are DEPRECATED and will be removed.
Use src.engines.loan_engine.models for core loan types.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class InterestType(StrEnum):
    """Loan interest models supported."""
    FIXED = "fixed"
    FLOATING = "floating"
    HYBRID = "hybrid"


class PrepaymentMode(StrEnum):
    """Prepayment behavior modes."""
    REDUCE_TENURE = "reduce_tenure"
    REDUCE_EMI = "reduce_emi"


class PayoffStrategy(StrEnum):
    """Debt payoff strategies - DEPRECATED."""
    SNOWBALL = "snowball"
    AVALANCHE = "avalanche"
    MINIMUM = "minimum"


class AmortizationRow(BaseModel):
    """Single row in amortization schedule."""
    month_number: int
    payment_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    emi_paise: int
    principal_paise: int
    interest_paise: int
    balance_paise: int
    cumulative_interest_paise: int


class PrepaymentResult(BaseModel):
    """Result of a prepayment simulation."""
    prepayment_paise: int
    mode: PrepaymentMode
    original_emi_paise: int
    new_emi_paise: int
    original_remaining_months: int
    new_remaining_months: int
    months_saved: int
    interest_saved_paise: int
    loan_closed: bool = False
    new_schedule: list[AmortizationRow] | None = None


class RefinanceInput(BaseModel):
    """Input for refinance evaluation - DEPRECATED."""
    current_outstanding_paise: int
    current_rate_bps: int
    remaining_months: int
    current_emi_paise: int
    new_rate_bps: int
    new_tenure_months: int
    processing_fees_paise: int = 0
    prepayment_penalty_paise: int = 0
    tax_rate_bps: int = 2000  # 20% default
    section_24_limit_paise: int = 20000000  # ₹2,00,000 default
    start_date: str | None = None


class RefinanceResult(BaseModel):
    """Result of refinance evaluation - DEPRECATED."""
    current_rate_bps: int
    new_rate_bps: int
    current_emi_paise: int
    new_emi_paise: int
    emi_savings_paise: int
    one_time_cost_paise: int
    break_even_months: int
    remaining_months: int
    is_beneficial: bool
    gross_savings_paise: int
    tax_benefit_difference_paise: int
    net_savings_paise: int


class LoanInfo(BaseModel):
    """Loan information for payoff strategies - DEPRECATED."""
    loan_id: int
    outstanding_paise: int
    annual_rate_bps: int
    remaining_months: int
    emi_paise: int
    start_date: str
    prepayment_penalty_bps: int = 0
    name: str = ""
    lender: str = ""
    interest_type: InterestType = InterestType.FIXED
    rate_changes: list[tuple[int, int]] = Field(default_factory=list)
    processing_fees_paise: int = 0


class PayoffLoanResult(BaseModel):
    """Result for a single loan in payoff strategy - DEPRECATED."""
    loan_id: int
    months_to_payoff: int
    total_interest_paise: int
    total_payment_paise: int


class MonthlyCashFlow(BaseModel):
    """Monthly cash flow details - DEPRECATED."""
    month: int
    total_payment_paise: int
    interest_paise: int
    principal_paise: int


class PayoffResult(BaseModel):
    """Result of payoff strategy simulation - DEPRECATED."""
    strategy: PayoffStrategy
    total_months: int
    total_interest_paise: int
    monthly_cash_flow: list[MonthlyCashFlow]
    loan_results: list[PayoffLoanResult]


class HealthScoreResult(BaseModel):
    """Comprehensive health score breakdown - DEPRECATED."""
    dti_score: float
    utilization_score: float
    stress_score: float
    payment_score: float
    credit_score: float
    overall_score: float
    ltv_ratio: float = 0.0
    dti: float = 0.0
    missed_payment_rate: float = 0.0


class TaxBenefitResult(BaseModel):
    """Tax benefit calculation result - DEPRECATED."""
    interest_paise: int
    principal_paise: int
    section_24_benefit_paise: int
    section_80c_benefit_paise: int
    section_80ee_benefit_paise: int
    section_80eea_benefit_paise: int
    stamp_duty_benefit_paise: int
    total_benefit_paise: int


class LoanSummary(BaseModel):
    """Loan summary for listing/display - DEPRECATED."""
    loan_id: int
    name: str
    lender: str
    loan_type: str
    principal_paise: int
    outstanding_paise: int
    interest_rate_bps: int
    tenure_months: int
    emi_paise: int
    health_score: float | None = None
    annual_rate_bps: int | None = None
    remaining_months: int | None = None
    start_date: str | None = None


class FloatingRateChange(BaseModel):
    """Floating rate change event."""
    change_month: int
    new_rate_bps: int
    mode: Literal["adjust_emi", "adjust_tenure"]


class LoanComparisonResult(BaseModel):
    """Result of loan comparison - DEPRECATED."""
    loan_id: int
    total_cost_paise: int
    total_interest_paise: int
    total_payment_paise: int
    tenure_months: int
    emi_paise: int
    is_best: bool = False
