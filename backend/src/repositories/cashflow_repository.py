"""Cashflow domain repository."""
from typing import Any
from src.repositories.base import BaseRepository


class CashflowRepository(BaseRepository):
    """Repository for cashflow operations."""

    def get_monthly_cashflow(
        self,
        months: int = 6,
        member: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Returns month-by-month income and expense aggregation.
        All monetary values in paise (INTEGER).
        Uses date_iso for proper month grouping.
        """
        with self._get_conn() as conn:
            conditions = ["t.date_iso IS NOT NULL"]
            params = []

            if member and member != "All":
                conditions.append("t.member = ?")
                params.append(member)

            where = "WHERE " + " AND ".join(conditions)

            sql = f"""
                SELECT
                    substr(t.date_iso, 1, 7) as month_key,
                    SUM(CASE WHEN t.type = 'credit' THEN t.amount_paise ELSE 0 END) as income_paise,
                    SUM(CASE WHEN t.type = 'debit' THEN t.amount_paise ELSE 0 END) as expense_paise,
                    COUNT(*) as transaction_count
                FROM transactions t
                {where}
                GROUP BY substr(t.date_iso, 1, 7)
                ORDER BY month_key ASC
            """

            cur = conn.execute(sql, params)
            rows = [dict(row) for row in cur.fetchall()]
        return rows
