"""Financial Event domain models for Behaviour Engine.

Events represent enriched financial transactions with reconciliation metadata.
These will be used by the Behaviour Engine in future phases for accurate
classification of income, expenses, transfers, and liability changes.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from src.models.base import DomainModel

# EventType using Literal for type safety (works on Python 3.8+)
EventType = Literal[
    "income",
    "expense",
    "transfer",
    "liability_increase",
    "liability_decrease",
    "cash_advance",
    # New event types for Phase 6
    "emi_payment",
    "liability_repayment",
    "credit_card_cash_advance",
    "transfer_internal",
]

# Lifecycle states per project convention
LifecycleState = Literal[
    "open",
    "partially_settled",
    "settled",
    "rolls_over",
    "superseded",
]


class FinancialEvent(DomainModel):
    """Financial event DTO combining transaction data with reconciliation metadata.

    Events represent the true nature of financial flows for behavioural analysis.
    All monetary values are in paise (₹1.00 = 100 paise).

    Backward Compatibility:
    - amount_paise is the legacy/general amount field, populated for original event types
    - For original types (income/expense/transfer/cash_advance), only amount_paise is set
    - For new types (emi_payment, liability_repayment, credit_card_cash_advance, transfer_internal),
      the granular change fields are populated while preserving amount_paise for compatibility

    Granular Change Fields:
    - asset_change_paise: Positive = asset increase, Negative = asset decrease
    - liability_change_paise: Positive = liability increase (borrowing), Negative = decrease (repayment)
    - expense_paise: Positive = expense outflow
    - income_paise: Positive = income inflow
    """

    event_type: EventType
    transaction_ids: list[int] = Field(default_factory=list)
    
    # Legacy field - primary amount for original event types
    amount_paise: int = 0
    
    # Granular change fields for new event types
    asset_change_paise: int = 0
    liability_change_paise: int = 0
    expense_paise: int = 0
    income_paise: int = 0
    
    # Temporal fields
    date_iso: str
    month_bucket: str = ""  # Derived from date_iso via validator
    
    # Account fields
    account_id: str = ""
    counterparty_account_id: str | None = None
    
    # Categorization
    category: str = ""
    subcategory: str | None = None
    sub_type: str | None = None  # For sub-classification (e.g., "cash_conversion", "emi")
    provider: str | None = None  # Source of the event (e.g., "CRED", "Cheq", "HDFC")
    
    # Confidence (deprecated float kept for backward compatibility)
    confidence: float = 0.0
    confidence_bps: int | None = None
    
    # Lifecycle tracking
    lifecycle_state: LifecycleState = "open"
    settled_by_event_id: int | None = None
    outstanding_paise: int = 0
    superseded_by: int | None = None
    
    # Audit fields
    reviewed_by_user: bool = False
    notes: str | None = None
    
    # Multi-user support
    household_id: str = "primary"
    owner_id: str = "self"

    @model_validator(mode='after')
    def _derive_month_bucket(self) -> "FinancialEvent":
        """Derive month_bucket from date_iso if not explicitly provided."""
        if not self.month_bucket and self.date_iso:
            # date_iso expected format: YYYY-MM-DD, take first 7 chars = YYYY-MM
            self.month_bucket = self.date_iso[:7]
        return self

    model_config = {
        "from_attributes": True,
        "frozen": False,
        "validate_assignment": True,
        "str_strip_whitespace": True,
    }


class FinancialEventBatch(BaseModel):
    """Container for a batch of financial events with metadata."""

    events: list[FinancialEvent]
    generated_at: str  # ISO 8601 timestamp
    source: str | None = None  # "transactions", "import", "manual"


class BehaviourInput(BaseModel):
    """Input data contract for Behaviour Engine functions.

    This interface allows the engine to operate on data passed from the service
    layer rather than directly accessing the database.
    """

    transactions: list[dict[str, Any]]
    accounts: list[dict[str, Any]]
    loans: list[dict[str, Any]]
    credit_cards: list[dict[str, Any]]
    reconciliations: list[tuple[int, int]]
    financial_events: list[dict[str, Any]] = Field(default_factory=list)
    household_id: str | None = None