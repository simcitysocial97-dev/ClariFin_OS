from typing import Any
from datetime import date

from src.models.base import DomainModel, Money


class Loan(DomainModel):
    """Loan domain entity"""

    id: int
    name: str
    principal: Money
    interest_rate: float  # Annual percentage
    start_date: date
    tenure_months: int
    emi: Money

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "Loan":
        return cls(
            id=row["id"],
            name=row["name"],
            principal=Money(paise=row["principal_paise"]),
            interest_rate=row["interest_rate"],
            start_date=row["start_date"],
            tenure_months=row["tenure_months"],
            emi=Money(paise=row["emi_paise"]),
        )
