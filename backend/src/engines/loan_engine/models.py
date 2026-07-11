"""
Domain models for Loan Engine - Pure calculation types only.
All monetary values in paise (integer).
All interest rates in basis points (integer).
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


class FloatingRateChange(BaseModel):
    """Floating rate change event."""
    change_month: int
    new_rate_bps: int
    mode: Literal["adjust_emi", "adjust_tenure"]


class ForeclosureResult(BaseModel):
    """Result of foreclosure calculation."""
    outstanding_paise: int
    accrued_interest_paise: int
    penalty_paise: int
    foreclosure_amount_paise: int
    remaining_months_saved: int


class LoanMetrics(BaseModel):
    """Pure metrics for a loan."""
    outstanding_paise: int
    principal_paid_paise: int
    interest_paid_paise: int
    remaining_interest_paise: int
    remaining_tenure_months: int
    tenure_saved_months: int
    total_payments_remaining: int
    effective_interest_ratio: float  # interest / principal
