"""
Reconciliation DTOs
===================

Data Transfer Objects for reconciliation API responses.
All monetary fields use _paise suffix for explicit units.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ===== Reconciliation Types =====

ReconciliationStatus = Literal["pending", "confirmed", "rejected", "disputed"]


# ===== Discrepancy Types =====


class DiscrepancyDTO(BaseModel):
    """Discrepancy between transaction and statement."""

    id: int = Field(description="Discrepancy identifier")
    transaction_id: int = Field(description="Transaction identifier")
    statement_id: int = Field(description="Statement identifier")
    type: str = Field(description="Discrepancy type (amount, date, description)")
    expected_paise: int = Field(description="Expected amount in paise")
    actual_paise: int = Field(description="Actual amount in paise")
    difference_paise: int = Field(description="Difference in paise")
    status: ReconciliationStatus = Field(description="Discrepancy status")
    notes: str | None = Field(default=None, description="Additional notes")


# ===== Status Overview Types =====


class StatusOverviewDTO(BaseModel):
    """Reconciliation status overview."""

    total_transactions: int = Field(description="Total transactions")
    reconciled: int = Field(description="Number of reconciled transactions")
    pending: int = Field(description="Number of pending reconciliations")
    discrepancies: int = Field(description="Number of discrepancies")
    match_rate: float = Field(description="Match rate percentage (0-100)")


# ===== Audit Trail Types =====


class AuditTrailEntryDTO(BaseModel):
    """Single entry in audit trail."""

    id: int = Field(description="Audit entry identifier")
    transaction_id: int = Field(description="Transaction identifier")
    action: str = Field(description="Action taken (reconcile, reject, dispute)")
    user: str = Field(description="User who performed the action")
    timestamp: str = Field(description="Action timestamp (ISO format)")
    notes: str | None = Field(default=None, description="Action notes")


# ===== Reconciliation Summary Types =====


class ReconciliationSummaryDTO(BaseModel):
    """Reconciliation summary for a statement."""

    statement_id: int = Field(description="Statement identifier")
    bank: str = Field(description="Bank name")
    period_from: str = Field(description="Statement period start")
    period_to: str = Field(description="Statement period end")
    total_debit_paise: int = Field(description="Total debit in paise")
    total_credit_paise: int = Field(description="Total credit in paise")
    transaction_count: int = Field(description="Number of transactions")
    reconciled_count: int = Field(description="Number of reconciled transactions")
    status: ReconciliationStatus = Field(description="Overall status")


# ===== Reconciliation Insight Types =====

ReconciliationInsightType = Literal["positive", "warning", "info", "alert"]
ReconciliationInsightSeverity = Literal["low", "medium", "high"]


class ReconciliationInsightDTO(BaseModel):
    """Insight about reconciliation changes or patterns."""

    type: ReconciliationInsightType = Field(description="Insight type")
    severity: ReconciliationInsightSeverity = Field(description="Insight severity")
    message: str = Field(description="Human-readable insight message")
    action_url: str | None = Field(
        default=None, description="URL for detailed view or action"
    )


# ===== Reconciliation Evidence Types =====


class ReconciliationEvidenceItemDTO(BaseModel):
    """Evidence item for reconciliation calculation."""

    type: str = Field(description="Evidence type (transaction, statement, match)")
    summary: str = Field(description="Human-readable summary")
    source: str = Field(description="Source reference")
    confidence: float | None = Field(
        default=None, description="Confidence score (0-100)"
    )


class ReconciliationCalculationStepDTO(BaseModel):
    """Calculation step in the reconciliation derivation chain."""

    name: str = Field(description="Step name")
    description: str = Field(description="Step description")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input values")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Output values")


class ReconciliationEvidenceChainDTO(BaseModel):
    """Evidence chain for reconciliation calculation."""

    summary: str = Field(description="Overall summary of the calculation")
    evidence: list[ReconciliationEvidenceItemDTO] = Field(
        default_factory=list, description="List of evidence items"
    )
    calculation_steps: list[ReconciliationCalculationStepDTO] = Field(
        default_factory=list, description="Calculation chain steps"
    )
    source_references: list[str] = Field(
        default_factory=list, description="Source references for traceability"
    )
    confidence_score: float = Field(description="Overall confidence (0-100)")


# ===== Main Reconciliation DTO =====


class ReconciliationDTO(BaseModel):
    """
    Reconciliation data transfer object.

    Monetary fields:
    - total_discrepancy_paise: Total discrepancy in paise (canonical)
    - total_reconciled_paise: Total reconciled in paise
    """

    statements: list[ReconciliationSummaryDTO] = Field(
        default_factory=list, description="List of statement summaries"
    )
    discrepancies: list[DiscrepancyDTO] = Field(
        default_factory=list, description="List of discrepancies"
    )
    status_overview: StatusOverviewDTO = Field(
        default_factory=lambda: StatusOverviewDTO(
            total_transactions=0,
            reconciled=0,
            pending=0,
            discrepancies=0,
            match_rate=0.0,
        ),
        description="Reconciliation status overview",
    )
    audit_trail: list[AuditTrailEntryDTO] = Field(
        default_factory=list, description="Audit trail entries"
    )
    insights: list[ReconciliationInsightDTO] = Field(
        default_factory=list, description="List of insights about reconciliation"
    )
    evidence_chain: ReconciliationEvidenceChainDTO | None = Field(
        default=None, description="Evidence chain for explainability"
    )

    class Config:
        json_schema_extra: dict[str, Any] = {
            "example": {
                "statements": [],
                "discrepancies": [],
                "status_overview": {
                    "total_transactions": 100,
                    "reconciled": 95,
                    "pending": 3,
                    "discrepancies": 2,
                    "match_rate": 95.0,
                },
                "audit_trail": [],
                "insights": [],
                "evidence_chain": None,
            }
        }


# ===== Reconciliation Response Types =====


class ReconciliationMatchDTO(BaseModel):
    """Reconciliation match record from transfer matching."""

    id: int = Field(description="Reconciliation identifier")
    debit_txn_id: int = Field(description="Debit transaction ID")
    credit_txn_id: int = Field(description="Credit transaction ID")
    debit_account_id: str = Field(description="Debit account ID")
    credit_account_id: str = Field(description="Credit account ID")
    amount_paise: int = Field(description="Matched amount in paise")
    date_diff_days: int = Field(description="Days between transactions")
    match_confidence_bps: int = Field(
        description="Match confidence in basis points (0-10000)"
    )
    match_type: str = Field(description="Match type (exact, window, fuzzy, manual)")
    status: Literal["pending", "confirmed", "rejected"] = Field(
        description="Reconciliation status"
    )
    created_at: str = Field(description="Record creation timestamp")
    confirmed_at: str | None = Field(
        default=None, description="Confirmation timestamp if confirmed"
    )
    # Joined debit transaction details
    debit_date: str = Field(description="Debit transaction date")
    debit_date_iso: str = Field(description="Debit transaction ISO date")
    debit_description: str = Field(description="Debit transaction description")
    debit_amount_paise: int = Field(description="Debit transaction amount in paise")
    debit_bank: str = Field(description="Debit transaction bank")
    # Joined credit transaction details
    credit_date: str = Field(description="Credit transaction date")
    credit_date_iso: str = Field(description="Credit transaction ISO date")
    credit_description: str = Field(description="Credit transaction description")
    credit_amount_paise: int = Field(description="Credit transaction amount in paise")
    credit_bank: str = Field(description="Credit transaction bank")


class ReconciliationsListResponse(BaseModel):
    """Response for reconciliation list endpoint."""

    reconciliations: list[ReconciliationMatchDTO] = Field(
        description="List of reconciliation matches"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reconciliations": [
                    {
                        "id": 1,
                        "debit_txn_id": 101,
                        "credit_txn_id": 201,
                        "debit_account_id": "HDFC Bank",
                        "credit_account_id": "ICICI Bank",
                        "amount_paise": 4500000,
                        "date_diff_days": 1,
                        "match_confidence_bps": 7000,
                        "match_type": "window",
                        "status": "pending",
                        "created_at": "2025-01-15T10:00:00",
                        "confirmed_at": None,
                        "debit_date": "15/01/2025",
                        "debit_date_iso": "2025-01-15",
                        "debit_description": "CC PAYMENT",
                        "debit_amount_paise": 4500000,
                        "debit_bank": "HDFC Bank",
                        "credit_date": "16/01/2025",
                        "credit_date_iso": "2025-01-16",
                        "credit_description": "SALARY CREDIT",
                        "credit_amount_paise": 4500000,
                        "credit_bank": "ICICI Bank",
                    }
                ]
            }
        }


class ReconciliationScanResponse(BaseModel):
    """Response for reconciliation scan endpoint."""

    matches: list[dict[str, Any]] = Field(
        description="List of potential match candidates"
    )
    count: int = Field(description="Total number of potential matches")

    class Config:
        json_schema_extra = {
            "example": {
                "matches": [],
                "count": 0,
            }
        }


class ReconciliationDiscrepancyResponse(BaseModel):
    """Response for discrepancy list endpoint."""

    discrepancies: list[DiscrepancyDTO] = Field(
        default_factory=list, description="List of discrepancies"
    )
    total: int = Field(description="Total number of discrepancies")
    limit: int = Field(description="Number of discrepancies per page")
    offset: int = Field(description="Offset for pagination")


class ReconciliationAuditResponse(BaseModel):
    """Response for audit trail endpoint."""

    audit_trail: list[AuditTrailEntryDTO] = Field(
        default_factory=list, description="Audit trail entries"
    )
    total_count: int = Field(description="Total number of entries")
