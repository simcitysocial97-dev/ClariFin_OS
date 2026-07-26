"""Statement domain repository.

LOC WATCH: No repository file > 200 LOC.
If it grows beyond 200, split by sub-domain.
"""

from datetime import datetime, timedelta
from typing import Any

from src.models.statement import Statement
from src.repositories.base import BaseRepository


def _normalize_to_iso(date_str: str) -> str:
    """
    Normalize date string to canonical YYYY-MM-DD ISO format.

    Handles common Indian date formats from bank statements:
    - DD/MM/YYYY
    - DD-MM-YYYY
    - Already ISO YYYY-MM-DD (returns unchanged)

    If no format matches, returns original string.
    """
    if not date_str:
        return ""

    for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str


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
                (
                    bank,
                    card_last4 or None,
                    period_from or None,
                    period_to or None,
                    file_name,
                ),
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

    def update_statement_metadata(
        self, statement_id: int, metadata: dict[str, Any]
    ) -> None:
        """Update statement with all extracted metadata. Normalizes date fields to ISO format."""
        # Normalize all date fields to YYYY-MM-DD format on write
        normalized = {
            "payment_due_date": _normalize_to_iso(metadata.get("due_date", "")),
            "statement_date": _normalize_to_iso(metadata.get("statement_date", "")),
            "bill_cycle_start": _normalize_to_iso(metadata.get("bill_cycle_start", "")),
            "bill_cycle_end": _normalize_to_iso(metadata.get("bill_cycle_end", "")),
        }

        with self._get_conn() as conn:
            conn.execute(
                """
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
            """,
                (
                    metadata.get("total_amount_due"),
                    metadata.get("minimum_amount_due"),
                    normalized["payment_due_date"],
                    normalized["statement_date"],
                    metadata.get("card_last4"),
                    metadata.get("credit_limit"),
                    metadata.get("opening_balance"),
                    normalized["bill_cycle_start"],
                    normalized["bill_cycle_end"],
                    statement_id,
                ),
            )
            conn.commit()

    def update_validation_status(
        self, statement_id: int, status: str, difference: float
    ) -> None:
        """Update validation status after comparing extracted sum vs total_due."""
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE statements SET
                    validation_status = ?,
                    validation_difference = ?
                WHERE id = ?
            """,
                (status, difference, statement_id),
            )
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
            conn.execute(
                "DELETE FROM transactions WHERE statement_id = ?", (statement_id,)
            )
            conn.execute("DELETE FROM statements WHERE id = ?", (statement_id,))
            conn.commit()

    def get_statement_pdf_path(self, statement_id: int) -> str | None:
        """Get the file_name for a statement."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT file_name FROM statements WHERE id = ?", (statement_id,)
            ).fetchone()
        return row[0] if row else None

    def get_duplicate_check_by_filename(self, file_name: str) -> bool:
        """Returns True if file_name already exists in statements (any bank)."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM statements WHERE file_name = ?", (file_name,)
            ).fetchone()
        return row is not None

    def get_banks(self) -> list[str]:
        """Get distinct list of banks from statements."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT DISTINCT bank FROM statements ORDER BY bank")
            banks = [row[0] for row in cur.fetchall()]
        return banks

    def get_statement_for_card(
        self, bank: str, card_last4: str
    ) -> dict[str, Any] | None:
        """
        Get the latest statement for a specific credit card.

        Args:
            bank: Statement bank (e.g., 'HDFC Bank', 'ICICI Bank')
            card_last4: Last 4 digits of credit card

        Returns:
            Most recent statement row dict or None if no match found.
        """
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT id, bank, card_last4,
                       total_amount_due, minimum_amount_due,
                       payment_due_date, statement_date,
                       bill_cycle_start, bill_cycle_end
                FROM statements
                WHERE bank = ? AND card_last4 = ?
                ORDER BY statement_date DESC
                LIMIT 1
                """,
                (bank, card_last4),
            ).fetchone()
            return dict(row) if row else None

    def get_statement_covering_date(
        self, bank: str, card_last4: str, txn_date: str
    ) -> dict[str, Any] | None:
        """
        Get the statement covering a specific transaction date using billing cycle window.

        Uses bill_cycle_start <= txn_date <= bill_cycle_end for reliable matching,
        avoiding fragile statement_month string matching across month boundaries.

        Args:
            bank: Statement bank (e.g., 'HDFC Bank', 'ICICI Bank')
            card_last4: Last 4 digits of credit card
            txn_date: Transaction date in ISO format (YYYY-MM-DD)

        Returns:
            Statement row dict or None if no match found.
        """
        with self._get_conn() as conn:
            # Get candidates where txn_date falls within bill cycle window
            # Uses ISO date string comparison (YYYY-MM-DD format)
            rows = conn.execute(
                """
                SELECT id, bank, card_last4,
                       total_amount_due, minimum_amount_due,
                       payment_due_date, statement_date,
                       bill_cycle_start, bill_cycle_end
                FROM statements
                WHERE bank = ? AND card_last4 = ?
                  AND bill_cycle_start IS NOT NULL
                  AND bill_cycle_end IS NOT NULL
                  AND ? >= bill_cycle_start
                  AND ? <= bill_cycle_end
                ORDER BY statement_date DESC
                LIMIT 1
                """,
                (bank, card_last4, txn_date, txn_date),
            ).fetchone()

            if rows:
                return dict(rows)

            # Fallback: no bill_cycle dates available, try matching by payment_due_date
            # with a ±7 day window around the transaction date
            rows = conn.execute(
                """
                SELECT id, bank, card_last4,
                       total_amount_due, minimum_amount_due,
                       payment_due_date, statement_date,
                       bill_cycle_start, bill_cycle_end
                FROM statements
                WHERE bank = ? AND card_last4 = ?
                  AND payment_due_date IS NOT NULL
                  AND payment_due_date >= date(?, '-7 days')
                  AND payment_due_date <= date(?, '+7 days')
                ORDER BY statement_date DESC
                LIMIT 1
                """,
                (bank, card_last4, txn_date, txn_date),
            ).fetchone()

            return dict(rows) if rows else None

    def find_matching_statement(
        self,
        bank: str,
        card_last4: str,
        payment_date: str,
        grace_period_days: int = 5,
    ) -> dict[str, Any] | None:
        """
        Find the matching statement for a credit card payment.

        Matching strategy (in order):
        1. Exact bank + card_last4 match
        2. Payment date <= payment_due_date + grace_period_days
        3. If multiple candidates, take the latest unpaid statement
        4. Fallback to bill_cycle window matching if no due_date match

        Args:
            bank: Statement bank (e.g., 'HDFC Bank', 'ICICI Bank')
            card_last4: Last 4 digits of credit card
            payment_date: Payment date in ISO format (YYYY-MM-DD)
            grace_period_days: Days after due_date to still match (default 5)

        Returns:
            Statement row dict or None if no match found.
        """
        with self._get_conn() as conn:
            # Get ALL candidates for this bank + card
            candidates = conn.execute(
                """
                SELECT id, bank, card_last4,
                       total_amount_due, minimum_amount_due,
                       payment_due_date, statement_date,
                       bill_cycle_start, bill_cycle_end
                FROM statements
                WHERE bank = ? AND card_last4 = ?
                ORDER BY statement_date DESC
                """,
                (bank, card_last4),
            ).fetchall()

        # Parse payment date to date object
        try:
            payment_dt = datetime.strptime(payment_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

        matching_statements = []
        bill_cycle_matches = []

        for row in candidates:
            row_dict = dict(row)
            # Check payment_due_date match (primary)
            due_date_str = row_dict.get("payment_due_date")
            if due_date_str:
                # Parse due date - try multiple formats
                due_dt = None
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                    try:
                        due_dt = datetime.strptime(due_date_str, fmt).date()
                        break
                    except ValueError:
                        continue

                if due_dt:
                    # Payment is within grace period of due_date
                    due_with_grace = due_dt + timedelta(days=grace_period_days)
                    if payment_dt <= due_with_grace:
                        matching_statements.append(row_dict)
                        continue

            # Fallback: bill_cycle matching
            cycle_start = row_dict.get("bill_cycle_start")
            cycle_end = row_dict.get("bill_cycle_end")

            if cycle_start and cycle_end:
                start_dt = end_dt = None
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                    try:
                        if cycle_start:
                            start_dt = datetime.strptime(cycle_start, fmt).date()
                        if cycle_end:
                            end_dt = datetime.strptime(cycle_end, fmt).date()
                        if start_dt and end_dt:
                            break
                    except ValueError:
                        continue

                if start_dt and end_dt and start_dt <= payment_dt <= end_dt:
                    # Payment falls within bill cycle window
                    bill_cycle_matches.append(row_dict)

        # Prefer due_date matches over bill_cycle matches
        if matching_statements:
            # Return the latest unpaid statement (highest statement_date)
            return matching_statements[0]

        if bill_cycle_matches:
            return bill_cycle_matches[0]

        return None
