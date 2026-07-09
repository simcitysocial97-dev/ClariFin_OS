from typing import Any
from src.models.base import DomainModel


class Statement(DomainModel):
    """Statement domain entity (metadata record for an imported statement)"""

    id: int
    bank: str
    card_last4: str | None = None
    period_from: str | None = None
    period_to: str | None = None
    file_name: str
    imported_at: str | None = None

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "Statement":
        return cls(
            id=row["id"],
            bank=row["bank"],
            card_last4=row.get("card_last4"),
            period_from=row.get("statement_period_from"),
            period_to=row.get("statement_period_to"),
            file_name=row["file_name"],
            imported_at=row.get("imported_at"),
        )
