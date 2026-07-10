"""
Domain models for Loan Engine
==============================
All monetary values in paise (integer).
All interest rates in basis points (integer).
"""

from enum import StrEnum

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


class RefinanceInput(BaseModel):
    """Input for refinance evaluation."""
    current_outstanding_paise: int
    current_rate_bps: int
    remaining_months: int
    current_emi_paise: int
    new_rate_bps: int
    new_tenure_months: int
    processing_fees_paise: int = 0


class RefinanceResult(BaseModel):
    """Result of refinance evaluation."""
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


class HealthScoreComponent(BaseModel):
    """Individual component of health score."""
    score: float
    weight: float = 0.25
    max_possible: float


class HealthScoreResult(BaseModel):
    """Full health score breakdown."""
    dti_score: float
    utilization_score: float
    stress_score: float
    payment_score: float
    overall_score: float


class LoanSummary(BaseModel):
    """Loan summary for listing/display."""
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
