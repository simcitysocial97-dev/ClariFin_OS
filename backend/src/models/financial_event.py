"""Financial Event domain models for Behaviour Engine.

Events represent enriched financial transactions with reconciliation metadata.
These will be used by the Behaviour Engine in future phases for accurate
classification of income, expenses, transfers, and liability changes.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from src.models.base import DomainModel

# EventType using Literal for type safety (works on Python 3.8+)
EventType = Literal[
    "income",
    "expense",
    "transfer",
    "liability_increase",
    "liability_decrease",
    "cash_advance",
]


class FinancialEvent(DomainModel):
    """Financial event DTO combining transaction data with reconciliation metadata.

    Events represent the true nature of financial flows for behavioural analysis.
    All monetary values are in paise (₹1.00 = 100 paise).
    """

    event_id: str
    event_type: EventType
    transaction_ids: list[int] = Field(default_factory=list)
    amount_paise: int
    date_iso: str
    account_id: str
    counterparty_account_id: str | None = None
    category: str
    subcategory: str | None = None
    confidence: float = 0.0
    notes: str | None = None
    household_id: str | None = None  # Future multi-user support
    owner_id: str | None = None  # Future multi-user support


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
    household_id: str | None = None
