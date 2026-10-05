"""Investment domain repository."""

from datetime import date
from typing import Any

from src.models.investment import Investment
from src.repositories.base import BaseRepository


class InvestmentRepository(BaseRepository):
    """Repository for investment-related operations."""

    def get_all(self) -> list[dict[str, Any]]:
        """Get all active investments (raw dicts, for net worth)."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, name, investment_type, units, buy_price_paise,
                       current_price_paise, invested_paise, current_value_paise,
                       as_of_date, is_active, notes, created_at, updated_at
                FROM investments
                WHERE is_active = 1
                ORDER BY current_value_paise DESC
            """).fetchall()
        return [dict(r) for r in rows]

    def get_all_models(self) -> list[Investment]:
        """
        Return all active investments as Investment domain models.

        Maps canonical paise columns (buy_price_paise, current_price_paise,
        invested_paise, current_value_paise) into Money value objects.
        COALESCE guards nullable columns so required model fields stay valid.
        """
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, name, investment_type,
                       COALESCE(units, 0) AS units,
                       COALESCE(buy_price_paise, 0) AS buy_price_paise,
                       COALESCE(current_price_paise, 0) AS current_price_paise,
                       COALESCE(invested_paise, 0) AS invested_paise,
                       COALESCE(current_value_paise, 0) AS current_value_paise,
                       COALESCE(as_of_date, '') AS as_of_date
                FROM investments
                WHERE is_active = 1
                ORDER BY current_value_paise DESC
            """).fetchall()
        return [Investment.from_db_row(dict(r)) for r in rows]

    def create(
        self,
        name: str,
        investment_type: str,
        invested_paise: int,
        current_value_paise: int,
        as_of_date: str | None = None,
        units: float | None = None,
        buy_price_paise: int | None = None,
        current_price_paise: int | None = None,
        notes: str | None = None,
    ) -> int:
        """Create a new investment record.

        The parameters and the INSERT column list are derived from the same
        ``investments`` DDL (``backend/src/core/db/schema.py``). Columns absent
        from that DDL (``platform``, ``purchase_date``, ``maturity_date``,
        ``linked_account_id``) were previously named here; they do not exist on
        the table, so every create failed. ``as_of_date`` is NOT NULL in the
        DDL and therefore always supplied.
        """
        columns = (
            "name",
            "investment_type",
            "invested_paise",
            "current_value_paise",
            "as_of_date",
            "units",
            "buy_price_paise",
            "current_price_paise",
            "notes",
        )
        values: tuple[Any, ...] = (
            name,
            investment_type,
            invested_paise,
            current_value_paise,
            as_of_date if as_of_date else date.today().isoformat(),
            units,
            buy_price_paise,
            current_price_paise,
            notes,
        )
        assert len(columns) == len(values), (
            f"investment INSERT column/value count mismatch: "
            f"{len(columns)} columns vs {len(values)} values"
        )
        placeholders = ", ".join("?" for _ in columns)
        with self._get_conn() as conn:
            cur = conn.execute(
                f"INSERT INTO investments ({', '.join(columns)}) "
                f"VALUES ({placeholders})",
                values,
            )
            conn.commit()
        return cur.lastrowid or 0

    def get_by_id(self, investment_id: int | str) -> dict[str, Any] | None:
        """Get a single investment by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM investments WHERE id = ?", (investment_id,)
            ).fetchone()
        return dict(row) if row else None

    def update(
        self, investment_id: int | str, **kwargs: str | int | float | None
    ) -> dict[str, Any] | None:
        """Update investment fields. Only updates provided fields."""
        allowed = {
            "name",
            "units",
            "current_price_paise",
            "current_value_paise",
            "as_of_date",
            "notes",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return self.get_by_id(investment_id)

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = datetime('now')"
        values = list(updates.values()) + [investment_id]

        with self._get_conn() as conn:
            conn.execute(f"UPDATE investments SET {set_clause} WHERE id = ?", values)
            conn.commit()
        return self.get_by_id(investment_id)

    def delete(self, investment_id: int | str) -> bool:
        """Soft delete an investment."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE investments SET is_active = 0, updated_at = datetime('now') WHERE id = ?",
                (investment_id,),
            )
            conn.commit()
            changes_row = conn.execute("SELECT changes()").fetchone()
        return bool(changes_row[0]) if changes_row else False

    def list_investments(self) -> list[dict[str, Any]]:
        """Get all investments for workspace services. Alias for get_all()."""
        return self.get_all()
