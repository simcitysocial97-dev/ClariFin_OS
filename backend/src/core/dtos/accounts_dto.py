"""
Accounts DTOs
=============

Data Transfer Objects for accounts API responses.
All monetary fields use _paise suffix for explicit units.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ===== Account Types =====

AccountType = Literal["savings", "current", "credit_card", "investment", "loan", "other"]
AccountStatus = Literal["active", "inactive", "closed"]


# ===== Account Detail Types =====

class AccountDetailDTO(BaseModel):
    """Detailed account information."""
    id: str = Field(description="Account identifier")
    name: str = Field(description="Account name")
    type: AccountType = Field(description="Account type")
    institution: str = Field(description="Bank or institution name")
    balance_paise: int = Field(description="Current balance in paise")
    currency: str = Field(default="INR", description="Currency code")
    status: AccountStatus = Field(description="Account status")
    account_number_last4: str | None = Field(default=None, description="Last 4 digits")
    opened_date: str | None = Field(default=None, description="Account opening date (ISO)")
    closed_date: str | None = Field(default=None, description="Account closing date (ISO)")


# ===== Balance History Types =====

class BalanceHistoryDTO(BaseModel):
    """Balance history entry for an account."""
    date: str = Field(description="Date of balance (ISO format)")
    balance_paise: int = Field(description="Balance in paise on this date")
    account_id: str = Field(description="Account identifier")


# ===== Account Transaction Types =====

class AccountTransactionDTO(BaseModel):
    """Transaction in account view."""
    id: str = Field(description="Transaction identifier")
    date: str = Field(description="Transaction date (ISO format)")
    description: str = Field(description="Transaction description")
    amount_paise: int = Field(description="Transaction amount in paise")
    category: str = Field(description="Category name")
    merchant: str | None = Field(default=None, description="Merchant name if available")


# ===== Account Type Breakdown Types =====

class AccountTypeBreakdownDTO(BaseModel):
    """Account type breakdown for analytics."""
    type: AccountType = Field(description="Account type")
    count: int = Field(description="Number of accounts of this type")
    total_balance_paise: int = Field(description="Total balance for this type in paise")
    percentage: float = Field(description="Percentage of total balance (0-100)")


# ===== Account Insight Types =====

AccountInsightType = Literal["positive", "warning", "info", "alert"]
AccountInsightSeverity = Literal["low", "medium", "high"]


class AccountInsightDTO(BaseModel):
    """Insight about account changes or patterns."""
    type: AccountInsightType = Field(description="Insight type")
    severity: AccountInsightSeverity = Field(description="Insight severity")
    message: str = Field(description="Human-readable insight message")
    action_url: str | None = Field(default=None, description="URL for detailed view or action")


# ===== Account Evidence Types =====

class AccountEvidenceItemDTO(BaseModel):
    """Evidence item for account calculation."""
    type: str = Field(description="Evidence type (transaction, balance, adjustment)")
    summary: str = Field(description="Human-readable summary")
    source: str = Field(description="Source reference")
    confidence: float | None = Field(default=None, description="Confidence score (0-100)")


class AccountCalculationStepDTO(BaseModel):
    """Calculation step in the account derivation chain."""
    name: str = Field(description="Step name")
    description: str = Field(description="Step description")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input values")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Output values")


class AccountEvidenceChainDTO(BaseModel):
    """Evidence chain for account calculation."""
    summary: str = Field(description="Overall summary of the calculation")
    evidence: list[AccountEvidenceItemDTO] = Field(
        default_factory=list,
        description="List of evidence items"
    )
    calculation_steps: list[AccountCalculationStepDTO] = Field(
        default_factory=list,
        description="Calculation chain steps"
    )
    source_references: list[str] = Field(
        default_factory=list,
        description="Source references for traceability"
    )
    confidence_score: float = Field(description="Overall confidence (0-100)")


# ===== Main Accounts DTO =====

class AccountsDTO(BaseModel):
    """
    Accounts data transfer object.

    Monetary fields:
    - total_balance_paise: Total balance in paise (canonical)
    - account_count: Number of accounts
    """
    accounts: list[AccountDetailDTO] = Field(
        default_factory=list,
        description="List of account details"
    )
    total_balance_paise: int = Field(description="Total balance across all accounts in paise")
    account_count: int = Field(description="Total number of accounts")
    type_breakdown: list[AccountTypeBreakdownDTO] = Field(
        default_factory=list,
        description="Account type breakdown"
    )
    insights: list[AccountInsightDTO] = Field(
        default_factory=list,
        description="List of insights about accounts"
    )
    evidence_chain: AccountEvidenceChainDTO | None = Field(
        default=None,
        description="Evidence chain for explainability"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "accounts": [],
                "total_balance_paise": 15000000,  # ₹1,50,000.00
                "account_count": 5,
                "type_breakdown": [],
                "insights": [],
                "evidence_chain": None
            }
        }


# ===== Accounts Response Types =====

class AccountsHistoryResponse(BaseModel):
    """Response for account balance history endpoint."""
    history: list[BalanceHistoryDTO] = Field(
        default_factory=list,
        description="Balance history entries"
    )
    total_count: int = Field(description="Total number of history entries")


class AccountsTransactionsResponse(BaseModel):
    """Response for account transactions endpoint."""
    transactions: list[AccountTransactionDTO] = Field(
        default_factory=list,
        description="List of transactions"
    )
    total: int = Field(description="Total number of transactions")
    limit: int = Field(description="Number of transactions per page")
    offset: int = Field(description="Offset for pagination")
