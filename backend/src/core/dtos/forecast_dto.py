"""
Forecast DTOs
=============

Data Transfer Objects for forecast API responses.
All monetary fields use _paise suffix for explicit units.
All confidence levels use _bps suffix (basis points, 0-10000 for 0-100%).
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ===== Forecast Projection Types =====

class NetWorthProjectionDTO(BaseModel):
    """Net worth projection for a future date."""
    date: str = Field(description="Projection date (ISO format)")
    projected_paise: int = Field(description="Projected net worth in paise")
    lower_bound_paise: int = Field(description="Lower confidence bound in paise")
    upper_bound_paise: int = Field(description="Upper confidence bound in paise")


class CashflowProjectionDTO(BaseModel):
    """Cashflow projection for a future month."""
    month: str = Field(description="Month label (e.g., '2026-08')")
    income_paise: int = Field(description="Projected income in paise")
    expenses_paise: int = Field(description="Projected expenses in paise")
    net_paise: int = Field(description="Projected net cashflow in paise")


# ===== Forecast Scenario Types =====

class ForecastScenarioDTO(BaseModel):
    """Forecast scenario with alternative projections."""
    name: str = Field(description="Scenario name")
    description: str = Field(description="Scenario description")
    probability_bps: int = Field(description="Probability in basis points (0-10000)")
    net_worth_projections: list[NetWorthProjectionDTO] = Field(
        default_factory=list,
        description="Net worth projections for this scenario"
    )
    cashflow_projections: list[CashflowProjectionDTO] = Field(
        default_factory=list,
        description="Cashflow projections for this scenario"
    )


# ===== Confidence Interval Types =====

ConfidenceLevel = Literal[90, 95, 99]


class ConfidenceIntervalDTO(BaseModel):
    """Confidence interval for a projection."""
    level: int = Field(description="Confidence level (90, 95, or 99)")
    lower_paise: int = Field(description="Lower bound in paise")
    upper_paise: int = Field(description="Upper bound in paise")


# ===== Forecast Summary Types =====

class ForecastSummaryDTO(BaseModel):
    """Forecast summary information."""
    horizon_months: int = Field(description="Forecast horizon in months")
    current_net_worth_paise: int = Field(description="Current net worth in paise")
    projected_net_worth_paise: int = Field(description="Final projected net worth in paise")
    projected_growth_paise: int = Field(description="Projected growth in paise")
    projected_growth_percentage: float = Field(description="Projected growth percentage")


# ===== Forecast Insight Types =====

ForecastInsightType = Literal["positive", "warning", "info", "alert"]
ForecastInsightSeverity = Literal["low", "medium", "high"]


class ForecastInsightDTO(BaseModel):
    """Insight about forecast changes or patterns."""
    type: ForecastInsightType = Field(description="Insight type")
    severity: ForecastInsightSeverity = Field(description="Insight severity")
    message: str = Field(description="Human-readable insight message")
    action_url: str | None = Field(default=None, description="URL for detailed view or action")


# ===== Forecast Evidence Types =====

class ForecastEvidenceItemDTO(BaseModel):
    """Evidence item for forecast calculation."""
    type: str = Field(description="Evidence type (historical, model, assumption)")
    summary: str = Field(description="Human-readable summary")
    source: str = Field(description="Source reference")
    confidence: float | None = Field(default=None, description="Confidence score (0-100)")


class ForecastCalculationStepDTO(BaseModel):
    """Calculation step in the forecast derivation chain."""
    name: str = Field(description="Step name")
    description: str = Field(description="Step description")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input values")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Output values")


class ForecastEvidenceChainDTO(BaseModel):
    """Evidence chain for forecast calculation."""
    summary: str = Field(description="Overall summary of the calculation")
    evidence: list[ForecastEvidenceItemDTO] = Field(
        default_factory=list,
        description="List of evidence items"
    )
    calculation_steps: list[ForecastCalculationStepDTO] = Field(
        default_factory=list,
        description="Calculation chain steps"
    )
    source_references: list[str] = Field(
        default_factory=list,
        description="Source references for traceability"
    )
    confidence_score: float = Field(description="Overall confidence (0-100)")


# ===== Main Forecast DTO =====

class ForecastDTO(BaseModel):
    """
    Forecast data transfer object.

    Monetary fields:
    - current_net_worth_paise: Current net worth in paise (canonical)
    - projected_net_worth_paise: Final projected net worth in paise
    - projected_growth_paise: Projected growth in paise
    """
    summary: ForecastSummaryDTO = Field(
        default_factory=lambda: ForecastSummaryDTO(
            horizon_months=12,
            current_net_worth_paise=0,
            projected_net_worth_paise=0,
            projected_growth_paise=0,
            projected_growth_percentage=0.0,
        ),
        description="Forecast summary"
    )
    net_worth_projections: list[NetWorthProjectionDTO] = Field(
        default_factory=list,
        description="Net worth projections"
    )
    cashflow_projections: list[CashflowProjectionDTO] = Field(
        default_factory=list,
        description="Cashflow projections"
    )
    scenarios: list[ForecastScenarioDTO] = Field(
        default_factory=list,
        description="Forecast scenarios"
    )
    confidence_intervals: list[ConfidenceIntervalDTO] = Field(
        default_factory=list,
        description="Confidence intervals"
    )
    insights: list[ForecastInsightDTO] = Field(
        default_factory=list,
        description="List of insights about forecast"
    )
    evidence_chain: ForecastEvidenceChainDTO | None = Field(
        default=None,
        description="Evidence chain for explainability"
    )

    class Config:
        json_schema_extra: dict[str, Any] = {
            "example": {
                "summary": {
                    "horizon_months": 12,
                    "current_net_worth_paise": 15000000,  # ₹1,50,000.00
                    "projected_net_worth_paise": 18000000,  # ₹1,80,000.00
                    "projected_growth_paise": 3000000,  # ₹30,000.00
                    "projected_growth_percentage": 20.0
                },
                "net_worth_projections": [],
                "cashflow_projections": [],
                "scenarios": [],
                "confidence_intervals": [],
                "insights": [],
                "evidence_chain": None
            }
        }


# ===== Forecast Response Types =====

class ForecastNetWorthResponse(BaseModel):
    """Response for net worth projection endpoint."""
    projections: list[NetWorthProjectionDTO] = Field(
        default_factory=list,
        description="Net worth projections"
    )
    total_count: int = Field(description="Total number of projections")


class ForecastCashflowResponse(BaseModel):
    """Response for cashflow projection endpoint."""
    projections: list[CashflowProjectionDTO] = Field(
        default_factory=list,
        description="Cashflow projections"
    )
    total_count: int = Field(description="Total number of projections")


class ForecastScenariosResponse(BaseModel):
    """Response for scenarios endpoint."""
    scenarios: list[ForecastScenarioDTO] = Field(
        default_factory=list,
        description="Forecast scenarios"
    )
    total_count: int = Field(description="Total number of scenarios")
