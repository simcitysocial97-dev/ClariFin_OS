"""Loan domain repository."""
from src.repositories.base import BaseRepository


class LoanRepository(BaseRepository):
    """Repository for loan-related operations."""

    def get_all(self) -> list[dict]:
        """Get all active loans."""
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

    def update(self, loan_id: int | str, **kwargs) -> dict | None:
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
            result = conn.execute(
                "SELECT changes()"
            ).fetchone()[0] > 0
        return result
