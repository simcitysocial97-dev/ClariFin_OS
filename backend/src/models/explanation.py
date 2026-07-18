"""
Explanation Models - Explainability contracts for financial metrics.

All monetary values are in paise (₹1.00 = 100 paise).
All confidence values are in basis points (0-10000).
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# Type aliases
EvidenceType = Literal['data', 'calculation', 'source']
CalculationOperation = Literal[
    'ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE',
    'AVERAGE', 'LOOKUP', 'FILTER', 'GROUP', 'MATCH'
]
SourceType = Literal[
    'statement', 'account', 'loan', 'investment',
    'transaction', 'recommendation_engine', 'cashflow_engine',
    'behaviour_engine', 'user_input'
]


class SourceReference(BaseModel):
    """Business source reference for evidence provenance."""
    type: SourceType
    id: str | int
    name: str | None = None
    date: str | None = None


class Evidence(BaseModel):
    """Evidence for a calculation."""
    id: str
    type: EvidenceType
    description: str
    value: int | str | bool | None
    sourceId: str | int | None = None


class CalculationStep(BaseModel):
    """Single step in a calculation chain."""
    stepId: str
    description: str
    operation: CalculationOperation
    inputIds: list[str]
    outputId: str
    order: int


class Confidence(BaseModel):
    """Confidence in basis points (0-10000)."""
    value: int = Field(ge=0, le=10000)
    reason: str | None = None


class Explanation(BaseModel):
    """Complete explanation for a financial metric."""
    metric: str
    value: int
    confidence: Confidence
    evidence: list[Evidence]
    sources: list[SourceReference]
    calculationSteps: list[CalculationStep]


class NetWorthExplanation(BaseModel):
    """Explanation for net worth calculation."""
    netWorth: Explanation
    assets: Explanation
    liabilities: Explanation
    confidenceReason: str | None = None


class NetWorthResponse(BaseModel):
    """Canonical API response for /api/networth endpoint."""
    net_worth_paise: int
    assets: dict[str, int]
    liabilities: dict[str, int]
    is_partial: bool
    partial_reason: str | None = None
    last_updated: str | None = None
    explanation: NetWorthExplanation | None = None


class CashflowMonth(BaseModel):
    """Single month cashflow data."""
    month_key: str
    month_label: str
    income_paise: int
    expense_paise: int
    net_paise: int
    transaction_count: int


class CashflowResponse(BaseModel):
    """Canonical API response for /api/cashflow/monthly endpoint."""
    months: list[CashflowMonth]
    period_months: int
    total_income_paise: int
    total_expense_paise: int
    total_net_paise: int
    is_partial: bool
    partial_reason: str | None = None
    last_updated: str | None = None
    explanation: Explanation | None = None


# ============================================================
# Reconciliation Response Models
# ============================================================

class ReconciliationMatch(BaseModel):
    """Single reconciliation match with transaction details."""
    id: int | None = None
    debit_txn_id: int
    credit_txn_id: int
    debit_account_id: str
    credit_account_id: str
    amount_paise: int
    date_diff_days: int
    match_confidence: float
    match_type: str
    status: str | None = None
    created_at: str | None = None
    confirmed_at: str | None = None
    # Transaction details
    debit_date: str | None = None
    debit_date_iso: str | None = None
    debit_description: str | None = None
    debit_amount_paise: int | None = None
    debit_bank: str | None = None
    credit_date: str | None = None
    credit_date_iso: str | None = None
    credit_description: str | None = None
    credit_amount_paise: int | None = None
    credit_bank: str | None = None


class ReconciliationResponse(BaseModel):
    """Canonical API response for /api/reconciliations/scan endpoint."""
    matches: list[ReconciliationMatch]
    count: int
    is_partial: bool = False
    partial_reason: str | None = None
    last_updated: str | None = None
    explanation: Explanation | None = None


# ============================================================
# Loans Response Models
# ============================================================

class LoansResponse(BaseModel):
    """Canonical API response for /api/loans endpoint."""
    loans: list[dict[str, Any]]
    total_outstanding_paise: int
    total_principal_paise: int
    total_monthly_emi_paise: int
    is_partial: bool = False
    partial_reason: str | None = None
    last_updated: str | None = None
    explanation: Explanation | None = None


# ============================================================
# Credit Cards Response Models
# ============================================================

class CreditCardSummary(BaseModel):
    """Single credit card summary for API response."""
    card_id: str
    bank: str
    card_last4: str | None = None
    credit_limit_paise: int
    current_outstanding_paise: int
    minimum_due_paise: int
    utilization_bps: int
    is_active: bool = True


class CreditCardsResponse(BaseModel):
    """Canonical API response for /api/v1/credit-cards endpoint."""
    cards: list[CreditCardSummary]
    total_outstanding_paise: int
    total_credit_limit_paise: int
    total_utilization_bps: int
    is_partial: bool = False
    partial_reason: str | None = None
    last_updated: str | None = None
    explanation: Explanation | None = None


# ============================================================
# Investments Response Models
# ============================================================

class InvestmentSummary(BaseModel):
    """Single investment summary for API response."""
    id: int
    name: str
    type: str
    invested_paise: int
    current_value_paise: int
    gain_paise: int
    gain_percent: float
    is_active: bool = True


class InvestmentsResponse(BaseModel):
    """Canonical API response for /api/investments endpoint."""
    investments: list[InvestmentSummary]
    total_invested_paise: int
    total_current_value_paise: int
    total_gain_paise: int
    is_partial: bool = False
    partial_reason: str | None = None
    last_updated: str | None = None
    explanation: Explanation | None = None