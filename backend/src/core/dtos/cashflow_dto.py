"""
Cashflow DTOs
=============

Data Transfer Objects for cashflow API responses.
All monetary fields use _paise suffix for explicit units.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ===== Cashflow Trend Types =====

CashflowTrendDirection = Literal["up", "down", "flat"]


class CashflowTrendDTO(BaseModel):
    """Cashflow trend information."""

    direction: CashflowTrendDirection = Field(
        description="Trend direction (up/down/flat)"
    )
    percentage_change: float = Field(
        description="Percentage change from previous period"
    )
    period: str = Field(
        description="Time period for comparison (e.g., '1M', '3M', '1Y')"
    )
    volatility_score: float = Field(default=0.0, description="Volatility score (0-100)")


# ===== Cashflow Monthly Types =====


class CashflowMonthlyDTO(BaseModel):
    """Monthly cashflow summary."""

    month: str = Field(description="Month label (e.g., '2026-07')")
    income_paise: int = Field(description="Total income in paise")
    expenses_paise: int = Field(description="Total expenses in paise")
    net_paise: int = Field(description="Net cashflow in paise (income - expenses)")
    transaction_count: int = Field(description="Number of transactions in this month")


# ===== Cashflow Category Types =====


class CashflowCategoryDTO(BaseModel):
    """Category breakdown for cashflow."""

    category_id: str = Field(description="Category identifier")
    category_name: str = Field(description="Category name for display")
    amount_paise: int = Field(description="Total amount in paise")
    percentage: float = Field(description="Percentage of total (0-100)")
    transaction_count: int = Field(
        description="Number of transactions in this category"
    )


# ===== Cashflow Transaction Types =====


class CashflowTransactionDTO(BaseModel):
    """Transaction in cashflow view."""

    id: str = Field(description="Transaction identifier")
    date: str = Field(description="Transaction date (ISO format)")
    description: str = Field(description="Transaction description")
    amount_paise: int = Field(description="Transaction amount in paise")
    category: str = Field(description="Category name")
    merchant: str | None = Field(default=None, description="Merchant name if available")


# ===== Cashflow Insight Types =====

CashflowInsightType = Literal["positive", "warning", "info", "alert"]
CashflowInsightSeverity = Literal["low", "medium", "high"]


class CashflowInsightDTO(BaseModel):
    """Insight about cashflow patterns."""

    type: CashflowInsightType = Field(description="Insight type")
    severity: CashflowInsightSeverity = Field(description="Insight severity")
    message: str = Field(description="Human-readable insight message")
    action_url: str | None = Field(
        default=None, description="URL for detailed view or action"
    )


# ===== Cashflow Evidence Types =====


class CashflowEvidenceItemDTO(BaseModel):
    """Evidence item for cashflow calculation."""

    type: str = Field(
        description="Evidence type (transaction, categorization, adjustment)"
    )
    summary: str = Field(description="Human-readable summary")
    source: str = Field(description="Source reference")
    confidence: float | None = Field(
        default=None, description="Confidence score (0-100)"
    )


class CashflowCalculationStepDTO(BaseModel):
    """Calculation step in the cashflow derivation chain."""

    name: str = Field(description="Step name")
    description: str = Field(description="Step description")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input values")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Output values")


class CashflowEvidenceChainDTO(BaseModel):
    """Evidence chain for cashflow calculation."""

    summary: str = Field(description="Overall summary of the calculation")
    evidence: list[CashflowEvidenceItemDTO] = Field(
        default_factory=list, description="List of evidence items"
    )
    calculation_steps: list[CashflowCalculationStepDTO] = Field(
        default_factory=list, description="Calculation chain steps"
    )
    source_references: list[str] = Field(
        default_factory=list, description="Source references for traceability"
    )
    confidence_score: float = Field(description="Overall confidence (0-100)")


# ===== Main Cashflow DTO =====


class CashflowSummaryDTO(BaseModel):
    """
    Cashflow summary data transfer object.

    Monetary fields:
    - total_income_paise: Total income in paise (canonical)
    - total_expenses_paise: Total expenses in paise
    - net_cashflow_paise: Net cashflow in paise
    """

    total_income_paise: int = Field(description="Total income in paise")
    total_expenses_paise: int = Field(description="Total expenses in paise")
    net_cashflow_paise: int = Field(
        description="Net cashflow in paise (income - expenses)"
    )
    transaction_count: int = Field(description="Total number of transactions")
    trend: CashflowTrendDTO | None = Field(
        default=None, description="Cashflow trend information"
    )
    insights: list[CashflowInsightDTO] = Field(
        default_factory=list, description="List of insights about cashflow"
    )
    evidence_chain: CashflowEvidenceChainDTO | None = Field(
        default=None, description="Evidence chain for explainability"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_income_paise": 10000000,  # ₹1,00,000.00
                "total_expenses_paise": 7500000,  # ₹75,000.00
                "net_cashflow_paise": 2500000,  # ₹25,000.00
                "transaction_count": 150,
                "trend": {
                    "direction": "up",
                    "percentage_change": 10.5,
                    "period": "1M",
                    "volatility_score": 25.0,
                },
                "insights": [],
                "evidence_chain": None,
            }
        }


# ===== Cashflow Response Types =====


class CashflowMonthlyResponse(BaseModel):
    """Response for monthly breakdown endpoint."""

    months: list[CashflowMonthlyDTO] = Field(
        default_factory=list, description="Monthly cashflow summaries"
    )
    total_count: int = Field(description="Total number of months available")


class CashflowCategoryResponse(BaseModel):
    """Response for category breakdown endpoint."""

    categories: list[CashflowCategoryDTO] = Field(
        default_factory=list, description="Category breakdowns"
    )
    total_count: int = Field(description="Total number of categories")


class CashflowTransactionResponse(BaseModel):
    """Response for transaction list endpoint."""

    transactions: list[CashflowTransactionDTO] = Field(
        default_factory=list, description="List of transactions"
    )
    total: int = Field(description="Total number of transactions")
    limit: int = Field(description="Number of transactions per page")
    offset: int = Field(description="Offset for pagination")
