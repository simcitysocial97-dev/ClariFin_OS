"""Loan Payment Repository."""


from src.models.loan_payment import LoanPayment, LoanPaymentCreate
from src.repositories.base import BaseRepository


class LoanPaymentRepository(BaseRepository):
    """Repository for loan payment operations."""

    def get_by_loan_id(self, loan_id: int) -> list[LoanPayment]:
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
                (loan_id,),
            ).fetchall()
        return [LoanPayment.from_db_row(dict(r)) for r in rows]

    def create(self, payment: LoanPaymentCreate) -> int:
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
                    payment.loan_id,
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

    def get_latest_payment(self, loan_id: int) -> LoanPayment | None:
        """Get the most recent payment for a loan."""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM loan_payments
                WHERE loan_id = ?
                ORDER BY payment_date DESC
                LIMIT 1
                """,
                (loan_id,),
            ).fetchone()
        return LoanPayment.from_db_row(dict(row)) if row else None

    def get_total_paid(self, loan_id: int) -> dict[str, int]:
        """Get total amounts paid for a loan."""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(amount_paise), 0) as total_amount_paise,
                    COALESCE(SUM(principal_paise), 0) as total_principal_paise,
                    COALESCE(SUM(interest_paise), 0) as total_interest_paise
                FROM loan_payments
                WHERE loan_id = ?
                """,
                (loan_id,),
            ).fetchone()
        return {
            "total_amount_paise": row["total_amount_paise"] if row else 0,
            "total_principal_paise": row["total_principal_paise"] if row else 0,
            "total_interest_paise": row["total_interest_paise"] if row else 0,
        }
