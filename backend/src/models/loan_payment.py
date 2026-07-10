"""Loan payment domain model."""

from typing import Any

from pydantic import field_validator

from src.models.base import DomainModel


class LoanPayment(DomainModel):
    """Loan payment record."""

    id: int | None = None
    loan_id: int
    payment_date: str  # ISO 8601 date string
    amount_paise: int
    principal_paise: int
    interest_paise: int
    late_fee_paise: int = 0
    source_account_id: int | None = None
    created_at: str | None = None

    @field_validator("amount_paise", "principal_paise", "interest_paise", "late_fee_paise")
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Ensure monetary fields are non-negative."""
        if v < 0:
            raise ValueError("Monetary fields must be non-negative")
        return v

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "LoanPayment":
        return cls(
            id=row.get("id"),
            loan_id=row["loan_id"],
            payment_date=row["payment_date"],
            amount_paise=row["amount_paise"],
            principal_paise=row["principal_paise"],
            interest_paise=row["interest_paise"],
            late_fee_paise=row.get("late_fee_paise", 0),
            source_account_id=row.get("source_account_id"),
            created_at=row.get("created_at"),
        )


class LoanPaymentCreate(DomainModel):
    """DTO for creating a loan payment."""

    loan_id: int
    payment_date: str  # ISO 8601 date string
    amount_paise: int
    principal_paise: int | None = None
    interest_paise: int | None = None
    late_fee_paise: int = 0
    source_account_id: int | None = None
