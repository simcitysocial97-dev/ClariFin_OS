"""Loan domain repository."""
from src.models.loan import Loan
from src.repositories.base import BaseRepository


class LoanRepository(BaseRepository):
    """Repository for loan-related operations."""

    def get_all(self) -> list[dict]:
        """Get all active loans (raw dicts, for summaries / net worth)."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, name, lender, loan_type, principal_paise,
                       outstanding_paise, interest_rate, tenure_months,
                       emi_paise, disbursed_date, gold_weight_grams, gold_purity,
                       interest_type, notes, created_at, updated_at
                FROM loans
                WHERE status = 'active'
                ORDER BY created_at DESC
            """).fetchall()
        return [dict(r) for r in rows]

    def get_all_models(self) -> list[Loan]:
        """
        Return all active loans as Loan domain models.

        Maps canonical paise columns (principal_paise, emi_paise) into Money
        value objects. `disbursed_date` is exposed to the model as `start_date`.
        COALESCE guards nullable columns so the required model fields always
        receive valid values.
        """
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, name, principal_paise, interest_rate,
                       COALESCE(disbursed_date, '1970-01-01') AS start_date,
                       tenure_months,
                       COALESCE(emi_paise, 0) AS emi_paise
                FROM loans
                WHERE status = 'active'
                ORDER BY created_at DESC
            """).fetchall()
        return [Loan.from_db_row(dict(r)) for r in rows]

    def create(self, name: str, lender: str, loan_type: str, principal_paise: int,
               outstanding_paise: int, interest_rate: float,
               disbursed_date: str, tenure_months: int | None = None,
               emi_paise: int | None = None,
               next_emi_date: str | None = None,
               gold_weight_grams: float | None = None,
               gold_purity: str | None = None,
               interest_type: str = 'reducing',
               notes: str | None = None) -> int:
        """Create a new loan record."""
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

    def get_by_id(self, loan_id: int | str) -> dict | None:
        """Get a single loan by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM loans WHERE id = ?", (loan_id,)
            ).fetchone()
        return dict(row) if row else None

    def update(self, loan_id: int | str, **kwargs: str | int | float | None) -> dict | None:
        """Update loan fields. Only updates provided fields."""
        allowed = {
            'name', 'lender', 'outstanding_paise', 'interest_rate',
            'tenure_months', 'emi_paise', 'gold_weight_grams',
            'gold_purity', 'interest_type', 'notes'
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return self.get_by_id(loan_id)

        set_clause = ', '.join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = datetime('now')"
        values = list(updates.values()) + [loan_id]

        with self._get_conn() as conn:
            conn.execute(
                f"UPDATE loans SET {set_clause} WHERE id = ?", values
            )
            conn.commit()
        return self.get_by_id(loan_id)

    def delete(self, loan_id: int | str) -> bool:
        """Soft delete a loan (set status to inactive)."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE loans SET status = 'inactive', updated_at = datetime('now') WHERE id = ?",
                (loan_id,)
            )
            conn.commit()
            changes_row = conn.execute("SELECT changes()").fetchone()
        return bool(changes_row[0]) if changes_row else False
