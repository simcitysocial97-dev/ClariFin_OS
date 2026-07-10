from typing import Any, Literal

from src.models.base import DomainModel, Money

AccountType = Literal[
    "savings",
    "current",
    "credit_card",
    "investment",
    "loan",
    "other",
]


class Account(DomainModel):
    """Account domain entity"""

    id: int
    name: str
    type: AccountType
    initial_balance: Money

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "Account":
        """Convert a database row into an Account model.

        Expects a row exposing `initial_balance_paise` (int) — the canonical
        paise storage for the account's opening balance.
        """
        return cls(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            initial_balance=Money(paise=row["initial_balance_paise"]),
        )
