"""
Credit Cards DTOs
==================

Data Transfer Objects for credit cards API responses.
All monetary fields use _paise suffix for explicit units.
All interest rates use _bps suffix (basis points, 1% = 100 bps).
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ===== Credit Card Types =====

CreditCardStatus = Literal["active", "inactive", "closed"]


# ===== Statement History Types =====

class StatementHistoryDTO(BaseModel):
    """Statement history entry for a credit card."""
    id: int = Field(description="Statement identifier")
    card_id: str = Field(description="Credit card identifier")
    period_from: str = Field(description="Statement period start (ISO format)")
    period_to: str = Field(description="Statement period end (ISO format)")
    total_due_paise: int = Field(description="Total amount due in paise")
    min_due_paise: int = Field(description="Minimum amount due in paise")
    total_payment_paise: int = Field(description="Total payment made in paise")
    payment_date: str | None = Field(default=None, description="Payment date (ISO format)")
    status: str = Field(description="Payment status (paid, pending, overdue)")


# ===== Utilization Types =====

class UtilizationDTO(BaseModel):
    """Credit card utilization data."""
    card_id: str = Field(description="Credit card identifier")
    credit_limit_paise: int = Field(description="Credit limit in paise")
    current_balance_paise: int = Field(description="Current balance in paise")
    utilization_percentage: float = Field(description="Utilization percentage (0-100)")
    available_paise: int = Field(description="Available credit in paise")


# ===== Spending by Category Types =====

class SpendingByCategoryDTO(BaseModel):
    """Spending breakdown by category for a credit card."""
    card_id: str = Field(description="Credit card identifier")
    category: str = Field(description="Category name")
    amount_paise: int = Field(description="Spending amount in paise")
    percentage: float = Field(description="Percentage of total spending (0-100)")
    transaction_count: int = Field(description="Number of transactions in this category")


# ===== Credit Card Summary Types =====

class CreditCardSummaryDTO(BaseModel):
    """Credit card summary information."""
    id: str = Field(description="Credit card identifier")
    name: str = Field(description="Card name")
    bank: str = Field(description="Issuing bank")
    card_number_last4: str = Field(description="Last 4 digits of card")
    credit_limit_paise: int = Field(description="Credit limit in paise")
    current_balance_paise: int = Field(description="Current balance in paise")
    available_paise: int = Field(description="Available credit in paise")
    min_due_paise: int = Field(description="Minimum due in paise")
    total_due_paise: int = Field(description="Total due in paise")
    due_date: str = Field(description="Payment due date (ISO format)")
    status: CreditCardStatus = Field(description="Card status")
    reward_points: int = Field(default=0, description="Reward points balance")


# ===== Credit Card Insight Types =====

CreditCardInsightType = Literal["positive", "warning", "info", "alert"]
CreditCardInsightSeverity = Literal["low", "medium", "high"]


class CreditCardInsightDTO(BaseModel):
    """Insight about credit card changes or patterns."""
    type: CreditCardInsightType = Field(description="Insight type")
    severity: CreditCardInsightSeverity = Field(description="Insight severity")
    message: str = Field(description="Human-readable insight message")
    action_url: str | None = Field(default=None, description="URL for detailed view or action")


# ===== Credit Card Evidence Types =====

class CreditCardEvidenceItemDTO(BaseModel):
    """Evidence item for credit card calculation."""
    type: str = Field(description="Evidence type (statement, transaction, adjustment)")
    summary: str = Field(description="Human-readable summary")
    source: str = Field(description="Source reference")
    confidence: float | None = Field(default=None, description="Confidence score (0-100)")


class CreditCardCalculationStepDTO(BaseModel):
    """Calculation step in the credit card derivation chain."""
    name: str = Field(description="Step name")
    description: str = Field(description="Step description")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input values")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Output values")


class CreditCardEvidenceChainDTO(BaseModel):
    """Evidence chain for credit card calculation."""
    summary: str = Field(description="Overall summary of the calculation")
    evidence: list[CreditCardEvidenceItemDTO] = Field(
        default_factory=list,
        description="List of evidence items"
    )
    calculation_steps: list[CreditCardCalculationStepDTO] = Field(
        default_factory=list,
        description="Calculation chain steps"
    )
    source_references: list[str] = Field(
        default_factory=list,
        description="Source references for traceability"
    )
    confidence_score: float = Field(description="Overall confidence (0-100)")


# ===== Main Credit Cards DTO =====

class CreditCardsDTO(BaseModel):
    """
    Credit Cards data transfer object.

    Monetary fields:
    - total_balance_paise: Total balance in paise (canonical)
    - total_due_paise: Total due in paise
    - total_available_paise: Total available credit in paise
    """
    cards: list[CreditCardSummaryDTO] = Field(
        default_factory=list,
        description="List of credit card summaries"
    )
    total_balance_paise: int = Field(description="Total balance across all cards in paise")
    total_due_paise: int = Field(description="Total due across all cards in paise")
    total_available_paise: int = Field(description="Total available credit in paise")
    card_count: int = Field(description="Total number of active cards")
    insights: list[CreditCardInsightDTO] = Field(
        default_factory=list,
        description="List of insights about credit cards"
    )
    evidence_chain: CreditCardEvidenceChainDTO | None = Field(
        default=None,
        description="Evidence chain for explainability"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "cards": [],
                "total_balance_paise": 15000000,  # ₹1,50,000.00
                "total_due_paise": 5000000,  # ₹50,000.00
                "total_available_paise": 35000000,  # ₹3,50,000.00
                "card_count": 2,
                "insights": [],
                "evidence_chain": None
            }
        }


# ===== Credit Cards Response Types =====

class CreditCardsStatementResponse(BaseModel):
    """Response for statement history endpoint."""
    statements: list[StatementHistoryDTO] = Field(
        default_factory=list,
        description="Statement history entries"
    )
    total_count: int = Field(description="Total number of statements")


class CreditCardsUtilizationResponse(BaseModel):
    """Response for utilization endpoint."""
    utilization: list[UtilizationDTO] = Field(
        default_factory=list,
        description="Utilization data for each card"
    )


class CreditCardsSpendingResponse(BaseModel):
    """Response for spending by category endpoint."""
    spending: list[SpendingByCategoryDTO] = Field(
        default_factory=list,
        description="Spending breakdown by category"
    )
