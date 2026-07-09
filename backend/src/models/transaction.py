from typing import Any
from datetime import date

from src.models.base import DomainModel, Money


class Transaction(DomainModel):
    """Transaction domain entity"""

    id: int
    statement_id: int
    date: date
    description: str
    amount: Money
    category: str
    member: str
    bank: str | None = None

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "Transaction":
        """
        Convert database row to Transaction model.

        Expects row with:
        - amount_paise (int) — canonical storage
        - amount (float) — legacy, ignored
        """
        return cls(
            id=row["id"],
            statement_id=row["statement_id"],
            date=row["date"],
            description=row["description"],
            amount=Money(paise=row["amount_paise"]),
            category=row["category"],
            member=row["member"],
            bank=row.get("bank"),
        )
