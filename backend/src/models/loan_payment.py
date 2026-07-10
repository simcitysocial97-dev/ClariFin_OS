"""Loan payment domain model."""

from typing import Any

from src.models.base import DomainModel


class LoanPayment(DomainModel):
    """Loan payment record."""

    id: int | None = None
    loan_id: int
    payment_date: str
    amount_paise: int
    principal_paise: int
    interest_paise: int
    late_fee_paise: int = 0
    source_account_id: int | None = None
    created_at: str | None = None

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
    payment_date: str
    amount_paise: int
    principal_paise: int | None = None
    interest_paise: int | None = None
    late_fee_paise: int = 0
    source_account_id: int | None = None
