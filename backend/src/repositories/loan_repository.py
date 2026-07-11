"""Loan domain repository - Persistence only.

All methods are focused solely on data persistence.
No financial calculations or business logic.
"""

from typing import Any

from src.models.loan import Loan
from src.repositories.base import BaseRepository


class LoanRepository(BaseRepository):
    """Repository for loan-related persistence operations.

    Only handles CRUD and metadata storage for loans and related entities.
    All calculations belong to loan_engine.
    """

    # ============================================================
    # Loan CRUD Operations
    # ============================================================

    def create_loan(self, name: str, lender: str, loan_type: str, principal_paise: int,
                    outstanding_paise: int, interest_rate: float,
                    disbursed_date: str, tenure_months: int | None = None,
                    emi_paise: int | None = None,
                    next_emi_date: str | None = None,
                    gold_weight_grams: float | None = None,
                    gold_purity: str | None = None,
                    interest_type: str = 'reducing',
                    notes: str | None = None) -> int:
        """Create a new loan record. Returns the new loan ID."""
        with self._get_conn() as conn:
            cur = conn.execute("""
                INSERT INTO loans (
                    name, lender, loan_type, principal_paise,
                    outstanding_paise, interest_rate, tenure_months,
                    emi_paise, disbursed_date, gold_weight_grams, gold_purity,
                    interest_type, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, lender, loan_type, principal_paise,
                  outstanding_paise, interest_rate, tenure_months,
                  emi_paise, disbursed_date, gold_weight_grams, gold_purity,
                  interest_type, notes))
            conn.commit()
        return cur.lastrowid or 0

    def get_loan(self, loan_id: int | str) -> dict[str, Any] | None:
        """Get a single loan by ID as a raw dict."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM loans WHERE id = ?", (int(loan_id),)
            ).fetchone()
        return dict(row) if row else None

    def list_loans(self) -> list[dict[str, Any]]:
        """Get all active loans as raw dicts for summaries."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, name, lender, loan_type, principal_paise,
                       outstanding_paise, interest_rate, tenure_months,
                       emi_paise, disbursed_date, gold_weight_grams, gold_purity,
                       interest_type, notes, created_at, updated_at
                FROM loans
                WHERE is_active = 1
                ORDER BY created_at DESC
            """).fetchall()
        return [dict(r) for r in rows]

    def list_loans_models(self) -> list[Loan]:
        """Return all active loans as Loan domain models."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, name, principal_paise, interest_rate,
                       disbursed_date AS start_date,
                       tenure_months,
                       COALESCE(emi_paise, 0) AS emi_paise
                FROM loans
                WHERE is_active = 1
                ORDER BY created_at DESC
            """).fetchall()
        return [Loan.from_db_row(dict(r)) for r in rows]

    def update_loan(self, loan_id: int | str, **kwargs: str | int | float | None) -> dict[str, Any] | None:
        """Update loan fields. Only updates provided fields."""
        allowed = {
            'name', 'lender', 'outstanding_paise', 'interest_rate',
            'tenure_months', 'emi_paise', 'gold_weight_grams',
            'gold_purity', 'interest_type', 'notes'
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return self.get_loan(loan_id)

        set_clause = ', '.join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = datetime('now')"
        values = list(updates.values()) + [int(loan_id)]

        with self._get_conn() as conn:
            conn.execute(
                f"UPDATE loans SET {set_clause} WHERE id = ?", values
            )
            conn.commit()
        return self.get_loan(loan_id)

    def delete_loan(self, loan_id: int | str) -> bool:
        """Soft delete a loan (set is_active to 0)."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE loans SET is_active = 0, updated_at = datetime('now') WHERE id = ?",
                (int(loan_id),)
            )
            conn.commit()
            changes_row = conn.execute("SELECT changes()").fetchone()
        return bool(changes_row[0]) if changes_row else False

    # ============================================================
    # Prepayment Persistence
    # ============================================================

    def add_prepayment(self, loan_id: int | str, amount_paise: int, prepayment_date: str,
                       mode: str = 'reduce_tenure') -> int:
        """Persist a prepayment record. Returns the prepayment ID."""
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO loan_prepayments (loan_id, amount_paise, prepayment_date, mode)
                VALUES (?, ?, ?, ?)
                """,
                (int(loan_id), amount_paise, prepayment_date, mode)
            )
            conn.commit()
        return cur.lastrowid or 0

    def list_prepayments(self, loan_id: int | str) -> list[dict[str, Any]]:
        """Get all prepayments for a loan."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, loan_id, amount_paise, prepayment_date, mode, created_at
                FROM loan_prepayments
                WHERE loan_id = ?
                ORDER BY prepayment_date DESC
                """,
                (int(loan_id),)
            ).fetchall()
        return [dict(r) for r in rows]

    def remove_prepayment(self, prepayment_id: int) -> bool:
        """Delete a prepayment record by ID."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM loan_prepayments WHERE id = ?", (prepayment_id,))
            conn.commit()
            changes = conn.execute("SELECT changes()").fetchone()
        return bool(changes[0]) if changes else False

    # ============================================================
    # Floating Rate Change Persistence
    # ============================================================

    def add_rate_change(self, loan_id: int | str, change_date: str, new_rate_bps: int,
                        mode: str = 'adjust_emi') -> int:
        """Persist a floating rate change record. Returns the rate change ID."""
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO loan_rate_changes (loan_id, change_date, new_rate_bps, mode)
                VALUES (?, ?, ?, ?)
                """,
                (int(loan_id), change_date, new_rate_bps, mode)
            )
            conn.commit()
        return cur.lastrowid or 0

    def list_rate_changes(self, loan_id: int | str) -> list[dict[str, Any]]:
        """Get all rate changes for a loan."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, loan_id, change_date, new_rate_bps, mode, created_at
                FROM loan_rate_changes
                WHERE loan_id = ?
                ORDER BY change_date
                """,
                (int(loan_id),)
            ).fetchall()
        return [dict(r) for r in rows]

    def remove_rate_change(self, rate_change_id: int) -> bool:
        """Delete a rate change record by ID."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM loan_rate_changes WHERE id = ?", (rate_change_id,))
            conn.commit()
            changes = conn.execute("SELECT changes()").fetchone()
        return bool(changes[0]) if changes else False