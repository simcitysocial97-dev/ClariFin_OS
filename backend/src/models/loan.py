"""Loan domain models with extended fields for loan engine."""

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from src.models.base import DomainModel, Money


class Loan(DomainModel):
    """Loan domain entity."""

    id: int
    name: str
    principal: Money
    interest_rate: float  # Annual percentage (for backward compatibility)
    interest_rate_bps: int | None = None  # Basis points (INVARIANT 2)
    start_date: str  # ISO 8601 date string
    tenure_months: int
    emi: Money
    outstanding_paise: int = 0
    interest_type: str = "fixed"  # fixed | floating | hybrid
    floating_baselined_rate_bps: int | None = None
    last_rate_reset_date: str | None = None
    prepayment_mode: str = "reduce_tenure"
    original_tenure_months: int | None = None

    @field_validator("outstanding_paise")
    @classmethod
    def validate_outstanding_paise(cls, v: int) -> int:
        """Ensure outstanding amount is non-negative."""
        if v < 0:
            raise ValueError("outstanding_paise must be non-negative")
        return v

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "Loan":
        return cls(
            id=row["id"],
            name=row["name"],
            principal=Money(paise=row["principal_paise"]),
            interest_rate=row["interest_rate"],
            interest_rate_bps=row.get("interest_rate_bps"),
            start_date=row["start_date"],
            tenure_months=row["tenure_months"],
            emi=Money(paise=row["emi_paise"]),
            outstanding_paise=row.get("outstanding_paise", 0),
            interest_type=row.get("interest_type", "fixed"),
            floating_baselined_rate_bps=row.get("floating_baselined_rate_bps"),
            last_rate_reset_date=row.get("last_rate_reset_date"),
            prepayment_mode=row.get("prepayment_mode", "reduce_tenure"),
            original_tenure_months=row.get("original_tenure_months"),
        )


class AmortizationRow(BaseModel):
    """Immutable amortization schedule row for display.

    Frozen to prevent mutation of historical payment data.
    All monetary values in paise (₹1.00 = 100 paise).
    """

    model_config = ConfigDict(frozen=True)

    month_number: int
    payment_date: str  # ISO 8601 date string
    emi_paise: int
    principal_paise: int
    interest_paise: int
    balance_paise: int
    cumulative_interest_paise: int

    @field_validator("emi_paise", "principal_paise", "interest_paise", "balance_paise", "cumulative_interest_paise")
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Ensure monetary fields are non-negative."""
        if v < 0:
            raise ValueError("Monetary fields must be non-negative")
        return v

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "AmortizationRow":
        """Create AmortizationRow from database row."""
        return cls(
            month_number=row["month_number"],
            payment_date=row["payment_date"],
            emi_paise=row["emi_paise"],
            principal_paise=row["principal_paise"],
            interest_paise=row["interest_paise"],
            balance_paise=row["balance_paise"],
            cumulative_interest_paise=row["cumulative_interest_paise"],
        )
