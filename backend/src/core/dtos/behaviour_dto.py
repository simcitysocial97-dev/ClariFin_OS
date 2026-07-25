"""
Behaviour DTOs
==============

Data Transfer Objects for behaviour API responses.
All monetary fields use _paise suffix for explicit units.
All scores use _bps suffix (basis points, 0-10000 for 0-100%).
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ===== Behaviour Score Types =====


class BehaviourScoreDTO(BaseModel):
    """Behaviour score for a specific dimension."""

    score: int = Field(description="Score in basis points (0-10000)")
    label: str = Field(description="Score label (e.g., 'Healthy', 'Warning')")
    factors: list[str] = Field(
        default_factory=list, description="Factors contributing to score"
    )


# ===== Spending Pattern Types =====


class SpendingPatternDTO(BaseModel):
    """Spending pattern analysis."""

    category: str = Field(description="Category name")
    amount_paise: int = Field(description="Total spending in paise")
    percentage: float = Field(description="Percentage of total spending (0-100)")
    trend: str = Field(description="Trend direction (increasing, decreasing, stable)")
    month_over_month_change: float = Field(
        description="Month-over-month change percentage"
    )


# ===== Savings Rate Types =====


class SavingsRateDTO(BaseModel):
    """Savings rate analysis."""

    savings_rate_bps: int = Field(description="Savings rate in basis points (0-10000)")
    income_paise: int = Field(description="Total income in paise")
    savings_paise: int = Field(description="Total savings in paise")
    period: str = Field(description="Analysis period (e.g., '1M', '3M', '1Y')")


# ===== Debt Health Types =====


class DebtHealthDTO(BaseModel):
    """Debt health analysis."""

    debt_to_income_bps: int = Field(description="Debt-to-income ratio in basis points")
    total_debt_paise: int = Field(description="Total debt in paise")
    total_income_paise: int = Field(description="Total income in paise")
    health_score: int = Field(description="Health score in basis points (0-10000)")


# ===== Wellness Radar Types =====


class WellnessRadarDTO(BaseModel):
    """Wellness radar data point."""

    dimension: str = Field(
        description="Dimension name (e.g., 'Savings', 'Debt', 'Income')"
    )
    score: int = Field(description="Score in basis points (0-10000)")
    max_score: int = Field(default=10000, description="Maximum possible score")


# ===== Behaviour Insight Types =====

BehaviourInsightType = Literal["positive", "warning", "info", "alert"]
BehaviourInsightSeverity = Literal["low", "medium", "high"]


class BehaviourInsightDTO(BaseModel):
    """Insight about behaviour patterns."""

    type: BehaviourInsightType = Field(description="Insight type")
    severity: BehaviourInsightSeverity = Field(description="Insight severity")
    message: str = Field(description="Human-readable insight message")
    action_url: str | None = Field(
        default=None, description="URL for detailed view or action"
    )


# ===== Behaviour Evidence Types =====


class BehaviourEvidenceItemDTO(BaseModel):
    """Evidence item for behaviour calculation."""

    type: str = Field(description="Evidence type (transaction, pattern, score)")
    summary: str = Field(description="Human-readable summary")
    source: str = Field(description="Source reference")
    confidence: float | None = Field(
        default=None, description="Confidence score (0-100)"
    )


class BehaviourCalculationStepDTO(BaseModel):
    """Calculation step in the behaviour derivation chain."""

    name: str = Field(description="Step name")
    description: str = Field(description="Step description")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input values")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Output values")


class BehaviourEvidenceChainDTO(BaseModel):
    """Evidence chain for behaviour calculation."""

    summary: str = Field(description="Overall summary of the calculation")
    evidence: list[BehaviourEvidenceItemDTO] = Field(
        default_factory=list, description="List of evidence items"
    )
    calculation_steps: list[BehaviourCalculationStepDTO] = Field(
        default_factory=list, description="Calculation chain steps"
    )
    source_references: list[str] = Field(
        default_factory=list, description="Source references for traceability"
    )
    confidence_score: float = Field(description="Overall confidence (0-100)")


# ===== Main Behaviour DTO =====


class BehaviourDTO(BaseModel):
    """
    Behaviour data transfer object.

    Monetary fields:
    - total_income_paise: Total income in paise (canonical)
    - total_savings_paise: Total savings in paise
    - total_debt_paise: Total debt in paise
    """

    wellness_score: BehaviourScoreDTO = Field(
        default_factory=lambda: BehaviourScoreDTO(score=0, label="Unknown", factors=[]),
        description="Overall wellness score",
    )
    spending_patterns: list[SpendingPatternDTO] = Field(
        default_factory=list, description="Spending pattern analysis"
    )
    savings_rate: SavingsRateDTO | None = Field(
        default=None, description="Savings rate analysis"
    )
    debt_health: DebtHealthDTO | None = Field(
        default=None, description="Debt health analysis"
    )
    wellness_radar: list[WellnessRadarDTO] = Field(
        default_factory=list, description="Wellness radar data"
    )
    insights: list[BehaviourInsightDTO] = Field(
        default_factory=list, description="List of insights about behaviour"
    )
    evidence_chain: BehaviourEvidenceChainDTO | None = Field(
        default=None, description="Evidence chain for explainability"
    )

    class Config:
        json_schema_extra: dict[str, Any] = {
            "example": {
                "wellness_score": {
                    "score": 7500,
                    "label": "Healthy",
                    "factors": ["Regular savings", "Low debt"],
                },
                "spending_patterns": [],
                "savings_rate": None,
                "debt_health": None,
                "wellness_radar": [],
                "insights": [],
                "evidence_chain": None,
            }
        }


# ===== Behaviour Response Types =====


class BehaviourPatternsResponse(BaseModel):
    """Response for spending patterns endpoint."""

    patterns: list[SpendingPatternDTO] = Field(
        default_factory=list, description="Spending patterns"
    )
    total_count: int = Field(description="Total number of patterns")


class BehaviourSavingsResponse(BaseModel):
    """Response for savings rate endpoint."""

    savings_rate: SavingsRateDTO = Field(
        default_factory=lambda: SavingsRateDTO(
            savings_rate_bps=0, income_paise=0, savings_paise=0, period="1M"
        ),
        description="Savings rate data",
    )


class BehaviourDebtResponse(BaseModel):
    """Response for debt health endpoint."""

    debt_health: DebtHealthDTO = Field(
        default_factory=lambda: DebtHealthDTO(
            debt_to_income_bps=0,
            total_debt_paise=0,
            total_income_paise=0,
            health_score=0,
        ),
        description="Debt health data",
    )
