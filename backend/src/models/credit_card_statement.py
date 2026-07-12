"""Credit Card Statement domain models."""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.models.base import DomainModel


class CreditCardStatement(DomainModel):
    """Credit Card Statement domain entity."""

    id: int
    card_id: str
    statement_date: str  # ISO 8601
    due_date: str  # ISO 8601
    total_outstanding_paise: int
    minimum_due_paise: int
    payment_date: str | None = None
    payment_amount_paise: int | None = None
    interest_charged_paise: int = 0

    @field_validator("total_outstanding_paise", "minimum_due_paise", "interest_charged_paise")
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Ensure monetary fields are non-negative."""
        if v < 0:
            raise ValueError("Monetary fields must be non-negative")
        return v

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "CreditCardStatement":
        """Create CreditCardStatement from database row."""
        return cls(
            id=row["id"],
            card_id=row["card_id"],
            statement_date=row["statement_date"],
            due_date=row["due_date"],
            total_outstanding_paise=row["total_outstanding_paise"],
            minimum_due_paise=row["minimum_due_paise"],
            payment_date=row.get("payment_date"),
            payment_amount_paise=row.get("payment_amount_paise"),
            interest_charged_paise=row.get("interest_charged_paise", 0),
        )


# ============================================================
# Request/Response DTOs
# ============================================================


class StatementGenerateRequest(BaseModel):
    """Request to generate a new statement."""

    statement_date: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="ISO 8601 date string for the statement"
    )


class StatementResponse(BaseModel):
    """Statement response model."""

    id: int
    card_id: str
    statement_date: str
    due_date: str
    total_outstanding_paise: int
    minimum_due_paise: int
    payment_date: str | None = None
    payment_amount_paise: int | None = None
    interest_charged_paise: int = 0

    @classmethod
    def from_statement_dict(cls, stmt: dict[str, Any]) -> "StatementResponse":
        """Create StatementResponse from statement dict."""
        return cls(
            id=stmt["id"],
            card_id=stmt["card_id"],
            statement_date=stmt["statement_date"],
            due_date=stmt["due_date"],
            total_outstanding_paise=stmt["total_outstanding_paise"],
            minimum_due_paise=stmt["minimum_due_paise"],
            payment_date=stmt.get("payment_date"),
            payment_amount_paise=stmt.get("payment_amount_paise"),
            interest_charged_paise=stmt.get("interest_charged_paise", 0),
        )


class PaymentRecordRequest(BaseModel):
    """Request to record a payment on a statement."""

    payment_date: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="ISO 8601 date string"
    )
    amount_paise: int = Field(gt=0, description="Payment amount in paise")
