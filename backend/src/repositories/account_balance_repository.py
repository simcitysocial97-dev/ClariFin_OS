"""Account Balance History Repository - Persistence only.

All methods are focused solely on data persistence.
No financial calculations or business logic.
"""

import sqlite3
from typing import Any, Literal

from src.repositories.base import BaseRepository

BalanceSource = Literal["actual", "projected", "adjusted"]


class AccountBalanceRepository(BaseRepository):
    """Repository for account balance history persistence operations.

    Only handles CRUD for balance snapshots.
    All calculations belong to account_engine.
    """

    # ============================================================
    # Balance Snapshot Operations
    # ============================================================

    def insert_balance_snapshot(
        self,
        account_id: str,
        balance_paise: int,
        date_iso: str,
        source: BalanceSource = "actual",
    ) -> int:
        """Insert a balance snapshot for an account.

        Uses UNIQUE(account_id, date_iso) constraint - will silently
        ignore duplicate entries to preserve historical data.

        Returns the snapshot ID, or 0 if duplicate was ignored.
        """
        with self._get_conn() as conn:
            try:
                cur = conn.execute(
                    """
                    INSERT INTO account_balance_history (
                        account_id, balance_paise, date_iso, source
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (account_id, balance_paise, date_iso, source),
                )
                conn.commit()
                return cur.lastrowid or 0
            except sqlite3.IntegrityError:
                # Duplicate (account_id, date_iso) - silently ignore
                return 0

    def get_balance_history(
        self, account_id: str, limit: int = 90
    ) -> list[dict[str, Any]]:
        """Get balance history for an account, most recent first."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, account_id, balance_paise, date_iso, source, created_at
                FROM account_balance_history
                WHERE account_id = ?
                ORDER BY date_iso DESC
                LIMIT ?
                """,
                (account_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_latest_balance(self, account_id: str) -> dict[str, Any] | None:
        """Get the most recent balance snapshot for an account."""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT id, account_id, balance_paise, date_iso, source, created_at
                FROM account_balance_history
                WHERE account_id = ?
                ORDER BY date_iso DESC
                LIMIT 1
                """,
                (account_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_balance_on_date(
        self, account_id: str, date_iso: str
    ) -> dict[str, Any] | None:
        """Get balance snapshot for a specific date."""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT id, account_id, balance_paise, date_iso, source, created_at
                FROM account_balance_history
                WHERE account_id = ? AND date_iso = ?
                """,
                (account_id, date_iso),
            ).fetchone()
        return dict(row) if row else None

    def delete_snapshot(self, snapshot_id: int) -> bool:
        """Delete a balance snapshot by ID."""
        with self._get_conn() as conn:
            conn.execute(
                "DELETE FROM account_balance_history WHERE id = ?",
                (snapshot_id,),
            )
            conn.commit()
            changes = conn.execute("SELECT changes()").fetchone()
        return bool(changes[0]) if changes else False
