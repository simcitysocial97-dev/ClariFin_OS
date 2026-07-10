"""Loan domain entity with extended fields for loan engine."""

from datetime import date
from typing import Any

from src.models.base import DomainModel, Money


class Loan(DomainModel):
    """Loan domain entity."""

    id: int
    name: str
    principal: Money
    interest_rate: float  # Annual percentage (for backward compatibility)
    interest_rate_bps: int | None = None  # Basis points (INVARIANT 2)
    start_date: date
    tenure_months: int
    emi: Money
    outstanding_paise: int = 0
    interest_type: str = "fixed"  # fixed | floating | hybrid
    floating_baselined_rate_bps: int | None = None
    last_rate_reset_date: str | None = None
    prepayment_mode: str = "reduce_tenure"
    original_tenure_months: int | None = None

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
