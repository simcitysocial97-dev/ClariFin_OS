from typing import Any
from src.models.base import DomainModel, Money


class Reconciliation(DomainModel):
    """Reconciliation domain entity linking a debit and a credit transaction"""

    id: int
    debit_txn_id: int
    credit_txn_id: int
    debit_account_id: str
    credit_account_id: str
    amount: Money
    date_diff_days: int
    match_confidence: float
    match_type: str
    status: str

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "Reconciliation":
        # The `amount` column is stored as a float; normalize to paise (₹1.00 = 100).
        return cls(
            id=row["id"],
            debit_txn_id=row["debit_txn_id"],
            credit_txn_id=row["credit_txn_id"],
            debit_account_id=row["debit_account_id"],
            credit_account_id=row["credit_account_id"],
            amount=Money(paise=row["amount_paise"]),
            date_diff_days=row["date_diff_days"],
            match_confidence=row["match_confidence"],
            match_type=row["match_type"],
            status=row["status"],
        )
