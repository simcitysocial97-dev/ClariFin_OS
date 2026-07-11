"""Loan Payment Repository - Persistence only.

All methods handle payment record persistence.
Financial aggregations belong in LoanService.
"""

from src.models.loan_payment import LoanPayment, LoanPaymentCreate
from src.repositories.base import BaseRepository


class LoanPaymentRepository(BaseRepository):
    """Repository for loan payment persistence operations."""

    def create_payment(self, payment: LoanPaymentCreate) -> int:
        """Create a new loan payment record."""
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO loan_payments (
                    loan_id, payment_date, amount_paise,
                    principal_paise, interest_paise, late_fee_paise,
                    source_account_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(payment.loan_id),
                    payment.payment_date,
                    payment.amount_paise,
                    payment.principal_paise or 0,
                    payment.interest_paise or 0,
                    payment.late_fee_paise,
                    payment.source_account_id,
                ),
            )
            conn.commit()
        return cur.lastrowid or 0

    def list_payments(self, loan_id: int | str) -> list[LoanPayment]:
        """Get all payments for a loan."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, loan_id, payment_date, amount_paise,
                       principal_paise, interest_paise, late_fee_paise,
                       source_account_id, created_at
                FROM loan_payments
                WHERE loan_id = ?
                ORDER BY payment_date DESC
                """,
                (int(loan_id),),
            ).fetchall()
        return [LoanPayment.from_db_row(dict(r)) for r in rows]

    def get_latest_payment(self, loan_id: int | str) -> LoanPayment | None:
        """Get the most recent payment for a loan."""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM loan_payments
                WHERE loan_id = ?
                ORDER BY payment_date DESC
                LIMIT 1
                """,
                (int(loan_id),),
            ).fetchone()
        return LoanPayment.from_db_row(dict(row)) if row else None

    # ============================================================
    # Legacy Compatibility Methods (deprecated)
    # ============================================================

    def create(self, payment: LoanPaymentCreate) -> int:
        """Legacy method - use create_payment() instead."""
        return self.create_payment(payment)

    def get_by_loan_id(self, loan_id: int) -> list[LoanPayment]:
        """Legacy method - use list_payments() instead."""
        return self.list_payments(loan_id)
