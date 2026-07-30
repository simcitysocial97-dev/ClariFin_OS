"""
Investments DTOs
================

Data Transfer Objects for investments API responses.
All monetary fields use _paise suffix for explicit units.
All returns use _bps suffix (basis points, 1% = 100 bps).
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ===== Investment Types =====

InvestmentType = Literal[
    "stocks", "mutual_funds", "bonds", "fd", "ppf", "gold", "other"
]
InvestmentStatus = Literal["active", "closed", "matured"]


# ===== Performance Types =====


class PerformanceDTO(BaseModel):
    """Investment performance data."""

    date: str = Field(description="Date (ISO format)")
    value_paise: int = Field(description="Portfolio value in paise")
    returns_bps: int = Field(description="Returns in basis points since inception")
    day_change_bps: int = Field(description="Day change in basis points")


# ===== Asset Allocation Types =====


class AssetAllocationDTO(BaseModel):
    """Asset allocation breakdown."""

    type: InvestmentType = Field(description="Investment type")
    value_paise: int = Field(description="Total value in paise")
    percentage: float = Field(description="Percentage of total (0-100)")
    count: int = Field(description="Number of holdings")


# ===== Holding Types =====


class HoldingDTO(BaseModel):
    """Single investment holding."""

    id: str = Field(description="Holding identifier")
    name: str = Field(description="Holding name")
    type: InvestmentType = Field(description="Investment type")
    symbol: str | None = Field(default=None, description="Stock/mutual fund symbol")
    quantity: float = Field(description="Number of units held")
    purchase_price_paise: int = Field(description="Purchase price per unit in paise")
    current_price_paise: int = Field(description="Current price per unit in paise")
    current_value_paise: int = Field(description="Current value in paise")
    invested_paise: int = Field(description="Total invested in paise")
    returns_paise: int = Field(description="Absolute returns in paise")
    returns_percentage: float = Field(description="Returns percentage")
    last_updated: str = Field(description="Last updated timestamp (ISO)")


# ===== Investment Summary Types =====


class InvestmentSummaryDTO(BaseModel):
    """Investment summary information."""

    id: str = Field(description="Investment identifier")
    name: str = Field(description="Investment name")
    type: InvestmentType = Field(description="Investment type")
    institution: str = Field(description="Institution name")
    current_value_paise: int = Field(description="Current value in paise")
    invested_paise: int = Field(description="Total invested in paise")
    returns_paise: int = Field(description="Absolute returns in paise")
    returns_percentage: float = Field(description="Returns percentage")
    returns_ytd_bps: int = Field(description="Year-to-date returns in basis points")
    status: InvestmentStatus = Field(description="Investment status")


# ===== Investment Insight Types =====

InvestmentInsightType = Literal["positive", "warning", "info", "alert"]
InvestmentInsightSeverity = Literal["low", "medium", "high"]


class InvestmentInsightDTO(BaseModel):
    """Insight about investment changes or patterns."""

    type: InvestmentInsightType = Field(description="Insight type")
    severity: InvestmentInsightSeverity = Field(description="Insight severity")
    message: str = Field(description="Human-readable insight message")
    action_url: str | None = Field(
        default=None, description="URL for detailed view or action"
    )


# ===== Investment Evidence Types =====


class InvestmentEvidenceItemDTO(BaseModel):
    """Evidence item for investment calculation."""

    type: str = Field(description="Evidence type (holding, price, calculation)")
    summary: str = Field(description="Human-readable summary")
    source: str = Field(description="Source reference")
    confidence: float | None = Field(
        default=None, description="Confidence score (0-100)"
    )


class InvestmentCalculationStepDTO(BaseModel):
    """Calculation step in the investment derivation chain."""

    name: str = Field(description="Step name")
    description: str = Field(description="Step description")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input values")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Output values")


class InvestmentEvidenceChainDTO(BaseModel):
    """Evidence chain for investment calculation."""

    summary: str = Field(description="Overall summary of the calculation")
    evidence: list[InvestmentEvidenceItemDTO] = Field(
        default_factory=list, description="List of evidence items"
    )
    calculation_steps: list[InvestmentCalculationStepDTO] = Field(
        default_factory=list, description="Calculation chain steps"
    )
    source_references: list[str] = Field(
        default_factory=list, description="Source references for traceability"
    )
    confidence_score: float = Field(description="Overall confidence (0-100)")


# ===== Main Investments DTO =====


class InvestmentsDTO(BaseModel):
    """
    Investments data transfer object.

    Monetary fields:
    - total_value_paise: Total value in paise (canonical)
    - total_invested_paise: Total invested in paise
    - total_returns_paise: Total returns in paise
    """

    investments: list[InvestmentSummaryDTO] = Field(
        default_factory=list, description="List of investment summaries"
    )
    total_value_paise: int = Field(
        description="Total value across all investments in paise"
    )
    total_invested_paise: int = Field(description="Total invested in paise")
    total_returns_paise: int = Field(description="Total returns in paise")
    investment_count: int = Field(description="Total number of active investments")
    insights: list[InvestmentInsightDTO] = Field(
        default_factory=list, description="List of insights about investments"
    )
    evidence_chain: InvestmentEvidenceChainDTO | None = Field(
        default=None, description="Evidence chain for explainability"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "investments": [],
                "total_value_paise": 20000000,  # ₹2,00,000.00
                "total_invested_paise": 15000000,  # ₹1,50,000.00
                "total_returns_paise": 5000000,  # ₹50,000.00
                "investment_count": 5,
                "insights": [],
                "evidence_chain": None,
            }
        }


# ===== Investments Response Types =====


class InvestmentsPerformanceResponse(BaseModel):
    """Response for performance endpoint."""

    performance: list[PerformanceDTO] = Field(
        default_factory=list, description="Performance history"
    )
    total_count: int = Field(description="Total number of entries")


class InvestmentsAllocationResponse(BaseModel):
    """Response for asset allocation endpoint."""

    allocation: list[AssetAllocationDTO] = Field(
        default_factory=list, description="Asset allocation breakdown"
    )


class InvestmentsHoldingsResponse(BaseModel):
    """Response for holdings endpoint."""

    holdings: list[HoldingDTO] = Field(
        default_factory=list, description="Investment holdings"
    )
    total: int = Field(description="Total number of holdings")
    limit: int = Field(description="Number of holdings per page")
    offset: int = Field(description="Offset for pagination")
