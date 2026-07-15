"""Balance repository — isolates sqlite3 from engines."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class BalanceRepository:
    """Repository for account balance history queries."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)

    def get_running_balance_rows(
        self, account_id: str | None = None, starting_balance_paise: int = 0
    ) -> list[dict[str, Any]]:
        """Return running balance rows.

        Invokes BalanceEngine-required query shape:
        [{date_iso, amount_paise, running_balance_paise}, ...]
        """
        results: list[dict[str, Any]] = []
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT date, amount FROM transactions "
                "WHERE account_id = ? OR ? IS NULL ORDER BY date ASC",
                (account_id, account_id),
            )
            balance = starting_balance_paise
            for date_iso, amount in cursor.fetchall():
                balance += int(amount or 0)
                results.append(
                    {"date_iso": date_iso, "amount_paise": int(amount or 0), "running_balance_paise": balance}
                )
        finally:
            conn.close()
        return results
