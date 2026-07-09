"""Statement domain repository.

LOC WATCH: No repository file > 200 LOC.
If it grows beyond 200, split by sub-domain.
"""
from typing import Any

from src.models.statement import Statement
from src.repositories.base import BaseRepository


class StatementRepository(BaseRepository):
    """Repository for statement operations."""

    def get_all_statements(self) -> list[dict[str, Any]]:
        """Get all statements with computed transaction counts and totals."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT
                    s.id, s.bank, s.card_last4,
                    s.statement_period_from, s.statement_period_to,
                    s.file_name, s.imported_at,
                    COUNT(t.id) AS transaction_count,
                    COALESCE(SUM(CASE WHEN t.type='debit'  THEN t.amount_paise ELSE 0 END), 0) AS total_debit_paise,
                    COALESCE(SUM(CASE WHEN t.type='credit' THEN t.amount_paise ELSE 0 END), 0) AS total_credit_paise
                FROM statements s
                LEFT JOIN transactions t ON t.statement_id = s.id
                GROUP BY s.id
                ORDER BY s.imported_at DESC
            """).fetchall()
        return [dict(r) for r in rows]

    def get_all_models(self) -> list[Statement]:
        """
        Return all statements as Statement domain models (core metadata columns).
        """
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, bank, card_last4,
                       statement_period_from, statement_period_to,
                       file_name, imported_at
                FROM statements
                ORDER BY imported_at DESC
            """).fetchall()
        return [Statement.from_db_row(dict(r)) for r in rows]

    def get_all_statements_with_metadata(self) -> list[dict[str, Any]]:
        """
        Returns all statements with metadata + computed transaction counts and totals.
        Includes: total_amount_due, minimum_amount_due, payment_due_date,
                  validation_status, validation_difference, card_last4.
        """
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT
                    s.id, s.bank, s.card_last4,
                    s.statement_period_from, s.statement_period_to,
                    s.file_name, s.imported_at,
                    s.total_amount_due, s.minimum_amount_due,
                    s.payment_due_date, s.statement_date,
                    s.validation_status, s.validation_difference,
                    COUNT(t.id) AS transaction_count,
                    COALESCE(SUM(CASE WHEN t.type='debit'  THEN t.amount_paise ELSE 0 END), 0) AS total_debit_paise,
                    COALESCE(SUM(CASE WHEN t.type='credit' THEN t.amount_paise ELSE 0 END), 0) AS total_credit_paise
                FROM statements s
                LEFT JOIN transactions t ON t.statement_id = s.id
                GROUP BY s.id
                ORDER BY s.imported_at DESC
            """).fetchall()
        return [dict(r) for r in rows]

    def insert_statement(
        self,
        bank: str,
        file_name: str,
        period_from: str = "",
        period_to: str = "",
        card_last4: str = "",
    ) -> int:
        """
        Insert a statement record. If (bank, file_name) already exists,
        return the existing id without inserting.
        Returns statement_id (int).
        """
        with self._get_conn() as conn:
            # Check if already exists
            cur = conn.execute(
                "SELECT id FROM statements WHERE bank = ? AND file_name = ?",
                (bank, file_name),
            )
            row = cur.fetchone()
            if row:
                return int(row[0])

            cur = conn.execute(
                """
                INSERT INTO statements (bank, card_last4, statement_period_from, statement_period_to, file_name)
                VALUES (?, ?, ?, ?, ?)
                """,
                (bank, card_last4 or None, period_from or None, period_to or None, file_name),
            )
            conn.commit()
        return int(cur.lastrowid or 0)

    def get_duplicate_check(self, bank: str, file_name: str) -> bool:
        """Returns True if (bank, file_name) already exists in statements."""
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT 1 FROM statements WHERE bank = ? AND file_name = ?",
                (bank, file_name),
            )
            result = cur.fetchone() is not None
        return result

    def get_statement_count(self) -> int:
        """Get total count of statements."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM statements")
            count = cur.fetchone()[0]
        return int(count)

    def update_statement_metadata(self, statement_id: int, metadata: dict[str, Any]) -> None:
        """Update statement with all extracted metadata."""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE statements SET
                    total_amount_due = ?,
                    minimum_amount_due = ?,
                    payment_due_date = ?,
                    statement_date = ?,
                    card_last4 = COALESCE(?, card_last4),
                    credit_limit = ?,
                    opening_balance = ?,
                    bill_cycle_start = ?,
                    bill_cycle_end = ?
                WHERE id = ?
            """, (
                metadata.get("total_amount_due"),
                metadata.get("minimum_amount_due"),
                metadata.get("due_date"),
                metadata.get("statement_date"),
                metadata.get("card_last4"),
                metadata.get("credit_limit"),
                metadata.get("opening_balance"),
                metadata.get("bill_cycle_start"),
                metadata.get("bill_cycle_end"),
                statement_id,
            ))
            conn.commit()

    def update_validation_status(self, statement_id: int, status: str, difference: float) -> None:
        """Update validation status after comparing extracted sum vs total_due."""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE statements SET
                    validation_status = ?,
                    validation_difference = ?
                WHERE id = ?
            """, (status, difference, statement_id))
            conn.commit()

    def get_statement_validation_summary(self) -> list[dict[str, Any]]:
        """Returns list of dicts for each statement with validation info."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT
                    s.id, s.bank, s.file_name,
                    s.total_amount_due, s.minimum_amount_due,
                    s.payment_due_date, s.statement_date, s.card_last4,
                    s.validation_status, s.validation_difference,
                    s.statement_period_from, s.statement_period_to,
                    COUNT(t.id) as transaction_count,
                    COALESCE(SUM(CASE WHEN t.type='debit' THEN t.amount_paise ELSE 0 END), 0) as total_debit_paise,
                    COALESCE(SUM(CASE WHEN t.type='credit' THEN t.amount_paise ELSE 0 END), 0) as total_credit_paise
                FROM statements s
                LEFT JOIN transactions t ON t.statement_id = s.id
                GROUP BY s.id
                ORDER BY s.imported_at DESC
            """).fetchall()
        return [dict(r) for r in rows]

    def delete_statement(self, statement_id: int) -> None:
        """Delete a statement and all its transactions."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM transactions WHERE statement_id = ?", (statement_id,))
            conn.execute("DELETE FROM statements WHERE id = ?", (statement_id,))
            conn.commit()

    def get_statement_pdf_path(self, statement_id: int) -> str | None:
        """Get the file_name for a statement."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT file_name FROM statements WHERE id = ?", (statement_id,)).fetchone()
        return row[0] if row else None

    def get_duplicate_check_by_filename(self, file_name: str) -> bool:
        """Returns True if file_name already exists in statements (any bank)."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT 1 FROM statements WHERE file_name = ?", (file_name,)).fetchone()
        return row is not None

    def get_banks(self) -> list[str]:
        """Get distinct list of banks from statements."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT DISTINCT bank FROM statements ORDER BY bank")
            banks = [row[0] for row in cur.fetchall()]
        return banks
