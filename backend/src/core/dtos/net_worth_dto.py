"""
Net Worth DTOs
==============

Data Transfer Objects for net worth API responses.
All monetary fields use _paise suffix for explicit units.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ===== Net Worth Composition Types =====


class NetWorthBreakdownItemDTO(BaseModel):
    """Single item in net worth composition breakdown."""

    id: str = Field(description="Account or asset identifier")
    name: str = Field(description="Account or asset name")
    type: str = Field(
        description="Account type (savings, current, investment, loan, credit_card)"
    )
    balance_paise: int = Field(
        description="Balance in paise (can be negative for liabilities)"
    )
    percentage: float = Field(description="Percentage of total net worth (0-100)")
    contribution_paise: int = Field(description="Contribution to net worth in paise")


class NetWorthCompositionDTO(BaseModel):
    """Net worth composition with asset and liability breakdowns."""

    total_assets_paise: int = Field(description="Total assets in paise")
    total_liabilities_paise: int = Field(description="Total liabilities in paise")
    asset_breakdown: list[NetWorthBreakdownItemDTO] = Field(
        default_factory=list,
        description="List of asset accounts with their contributions",
    )
    liability_breakdown: list[NetWorthBreakdownItemDTO] = Field(
        default_factory=list,
        description="List of liability accounts with their contributions",
    )


# ===== Net Worth Historical Snapshot Types =====


class NetWorthHistoricalSnapshotDTO(BaseModel):
    """Single historical net worth snapshot."""

    date: str = Field(description="Snapshot date (ISO format YYYY-MM-DD)")
    net_worth_paise: int = Field(description="Net worth in paise on this date")
    assets_paise: int = Field(description="Total assets in paise on this date")
    liabilities_paise: int = Field(
        description="Total liabilities in paise on this date"
    )


# ===== Net Worth Trend Types =====

NetWorthTrendDirection = Literal["up", "down", "flat"]


class NetWorthTrendDTO(BaseModel):
    """Net worth trend information."""

    direction: NetWorthTrendDirection = Field(
        description="Trend direction (up/down/flat)"
    )
    percentage_change: float = Field(
        description="Percentage change from previous period"
    )
    period: str = Field(
        description="Time period for comparison (e.g., '1M', '3M', '1Y')"
    )


# ===== Net Worth Insight Types =====

NetWorthInsightType = Literal["positive", "warning", "info", "alert"]
NetWorthInsightSeverity = Literal["low", "medium", "high"]


class NetWorthInsightDTO(BaseModel):
    """Insight about net worth changes or patterns."""

    type: NetWorthInsightType = Field(description="Insight type")
    severity: NetWorthInsightSeverity = Field(description="Insight severity")
    message: str = Field(description="Human-readable insight message")
    action_url: str | None = Field(
        default=None, description="URL for detailed view or action"
    )


# ===== Net Worth Evidence Types =====


class NetWorthEvidenceItemDTO(BaseModel):
    """Evidence item for net worth calculation."""

    type: str = Field(description="Evidence type (account, calculation, adjustment)")
    summary: str = Field(description="Human-readable summary")
    source: str = Field(description="Source reference")
    confidence: float | None = Field(
        default=None, description="Confidence score (0-100)"
    )


class NetWorthCalculationStepDTO(BaseModel):
    """Calculation step in the net worth derivation chain."""

    name: str = Field(description="Step name")
    description: str = Field(description="Step description")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input values")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Output values")


class NetWorthEvidenceChainDTO(BaseModel):
    """Evidence chain for net worth calculation."""

    summary: str = Field(description="Overall summary of the calculation")
    evidence: list[NetWorthEvidenceItemDTO] = Field(
        default_factory=list, description="List of evidence items"
    )
    calculation_steps: list[NetWorthCalculationStepDTO] = Field(
        default_factory=list, description="Calculation chain steps"
    )
    source_references: list[str] = Field(
        default_factory=list, description="Source references for traceability"
    )
    confidence_score: float = Field(description="Overall confidence (0-100)")


# ===== Main Net Worth DTO =====


class NetWorthDTO(BaseModel):
    """
    Net Worth data transfer object.

    Monetary fields:
    - total_net_worth_paise: Net worth in paise (canonical)
    - total_assets_paise: Total assets in paise
    - total_liabilities_paise: Total liabilities in paise
    """

    total_net_worth_paise: int = Field(
        description="Net worth in paise (assets - liabilities)"
    )
    total_assets_paise: int = Field(description="Total assets in paise")
    total_liabilities_paise: int = Field(description="Total liabilities in paise")
    composition: NetWorthCompositionDTO = Field(
        default_factory=lambda: NetWorthCompositionDTO(
            total_assets_paise=0,
            total_liabilities_paise=0,
            asset_breakdown=[],
            liability_breakdown=[],
        ),
        description="Asset and liability composition breakdown",
    )
    trend: NetWorthTrendDTO | None = Field(
        default=None, description="Net worth trend information"
    )
    insights: list[NetWorthInsightDTO] = Field(
        default_factory=list, description="List of insights about net worth"
    )
    evidence_chain: NetWorthEvidenceChainDTO | None = Field(
        default=None, description="Evidence chain for explainability"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_net_worth_paise": 15000000,  # ₹1,50,000.00
                "total_assets_paise": 20000000,  # ₹2,00,000.00
                "total_liabilities_paise": 5000000,  # ₹50,000.00
                "composition": {
                    "total_assets_paise": 20000000,
                    "total_liabilities_paise": 5000000,
                    "asset_breakdown": [],
                    "liability_breakdown": [],
                },
                "trend": {"direction": "up", "percentage_change": 5.5, "period": "1M"},
                "insights": [],
                "evidence_chain": None,
            }
        }


# ===== Net Worth Response Types =====


class NetWorthHistoryResponse(BaseModel):
    """Response for net worth history endpoint."""

    snapshots: list[NetWorthHistoricalSnapshotDTO] = Field(
        default_factory=list, description="Historical net worth snapshots"
    )
    total_count: int = Field(description="Total number of snapshots available")


class NetWorthInsightsResponse(BaseModel):
    """Response for net worth insights endpoint."""

    insights: list[NetWorthInsightDTO] = Field(
        default_factory=list, description="List of net worth insights"
    )
