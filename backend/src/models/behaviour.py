"""Behaviour Service DTOs and Response Models.

All monetary values are in paise (₹1.00 = 100 paise).
All ratios are Decimal for precision.
"""

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.models.base import DomainModel

# Type aliases for common types
WellnessBand = Literal["Excellent", "Healthy", "Developing", "Risk", "Critical"]
DebtHealthBand = Literal["HEALTHY", "MODERATE", "WARNING", "DANGER"]
ProfileType = Literal[
    "SAVER", "BALANCED", "SPENDER", "DEBT_OPTIMIZER", "DEBT_DEPENDENT", "INSUFFICIENT_DATA"
]

class WellnessScoreResponse(BaseModel):
    """Response model for wellness score."""

    score: Decimal = Field(..., description="Wellness score between 0 and 100")
    band: WellnessBand = Field(..., description="Wellness classification band")
    components: dict[str, Decimal] = Field(
        ..., description="Breakdown of wellness score components"
    )
    snapshot_date: str = Field(..., description="Date of the snapshot in ISO format")
    version: int = Field(..., description="Version of the scoring algorithm")

class DebtHealthResponse(BaseModel):
    """Response model for debt health metrics."""

    foir: Decimal = Field(..., description="Fixed Obligation to Income Ratio (0-1)")
    credit_dependency_ratio: Decimal = Field(
        ..., description="Ratio of credit-funded expenses to total expenses (0-1+)"
    )
    debt_cycle_score: int = Field(
        ..., description="Debt cycle score (0-100, higher = worse)"
    )
    credit_revolver_ratio: Decimal = Field(
        ..., description="Ratio of revolving credit usage (0-1)"
    )
    band: DebtHealthBand = Field(..., description="Debt health classification band")
    snapshot_date: str = Field(..., description="Date of the snapshot in ISO format")

class CashflowHealthResponse(BaseModel):
    """Response model for cashflow health metrics."""

    cashflow_stability_index: Decimal = Field(
        ..., description="Cashflow stability index (0-1)"
    )
    income_stability: Decimal = Field(..., description="Income stability score (0-1)")
    expense_stability: Decimal = Field(..., description="Expense stability score (0-1)")
    monthly_surplus_paise: int = Field(
        ..., description="Monthly surplus in paise (can be negative)"
    )
    snapshot_date: str = Field(..., description="Date of the snapshot in ISO format")

class FinancialPattern(BaseModel):
    """Model for detected financial patterns."""

    pattern_type: str = Field(..., description="Type of pattern (e.g., IMPULSE, SUBSCRIPTION)")
    pattern_key: str = Field(..., description="Key identifying the pattern (merchant, category)")
    strength: Decimal = Field(..., description="Strength of the pattern (0-1)")
    transaction_count: int = Field(..., description="Number of transactions in pattern")
    total_amount_paise: int = Field(..., description="Total amount in paise")
    first_observed: str = Field(..., description="First observed date in ISO format")
    last_observed: str = Field(..., description="Last observed date in ISO format")

class FinancialProfileResponse(BaseModel):
    """Response model for financial personality profile."""

    profile_type: ProfileType = Field(..., description="Financial personality profile")
    confidence: Decimal = Field(..., description="Confidence score (0-1)")
    explanation: str = Field(..., description="Explanation of the profile classification")
    snapshot_date: str = Field(..., description="Date of the snapshot in ISO format")

class MonthlySummaryResponse(BaseModel):
    """Response model for monthly financial summary."""

    period: str = Field(..., description="Summary period (YYYY-MM)")
    wellness_score: WellnessScoreResponse = Field(..., description="Wellness score for the period")
    debt_health: DebtHealthResponse = Field(..., description="Debt health metrics")
    cashflow_health: CashflowHealthResponse = Field(..., description="Cashflow health metrics")
    top_patterns: list[FinancialPattern] = Field(
        ..., description="Top detected financial patterns"
    )
    savings_rate: Decimal = Field(..., description="Savings rate for the period")
    total_income_paise: int = Field(..., description="Total income in paise")
    total_expenses_paise: int = Field(..., description="Total expenses in paise")
    alerts: list[str] = Field(..., description="Financial alerts for the period")

class BehaviourSnapshotCreate(DomainModel):
    """Input model for creating a behaviour snapshot."""

    snapshot_date: str
    household_id: str = "default"
    savings_discipline_score_bps: int
    cashflow_stability_score_bps: int
    salary_dependence_ratio_bps: int
    lifestyle_inflation_rate_bps: int
    subscription_burn_rate_bps: int
    resilience_index_bps: int
    wellness_score_bps: int
    version: int = 1