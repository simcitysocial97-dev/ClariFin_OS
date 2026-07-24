"""Transaction Classification Repository - Persistence for transaction classifications.

LOC WATCH: No repository file > 200 LOC.
"""
from typing import Any

from src.repositories.base import BaseRepository


class TransactionClassificationRepository(BaseRepository):
    """Repository for transaction classification persistence."""

    def insert_classification(
        self,
        transaction_id: int,
        classification: str,
        sub_classification: str | None,
        confidence_bps: int,
        source: str,
        classifier: str = "loan_emi_detector",
        classifier_version: int = 1,
        lifecycle_state: str | None = None,
        outstanding_paise: int = 0,
        payment_channel: str = "DIRECT",
        matched_statement_id: int | None = None,
    ) -> int:
        """
        Insert a classification record.

        Returns the classification ID.
        Uses INSERT OR IGNORE to prevent duplicates for same transaction+classification.

        Args:
            lifecycle_state: Current lifecycle state (fully_paid, revolving, etc.)
            outstanding_paise: Remaining outstanding after payment
            payment_channel: How payment was made (DIRECT, CRED, CHEQ, etc.)
            matched_statement_id: ID of matched statement for CC payments
        """
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO transaction_classifications
                    (transaction_id, classification, sub_classification,
                     confidence_bps, source, classifier, classifier_version,
                     lifecycle_state, outstanding_paise, payment_channel, matched_statement_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction_id,
                    classification,
                    sub_classification,
                    confidence_bps,
                    source,
                    classifier,
                    classifier_version,
                    lifecycle_state,
                    outstanding_paise,
                    payment_channel,
                    matched_statement_id,
                ),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    def get_by_transaction_id(self, transaction_id: int) -> dict[str, Any] | None:
        """Get classification for a transaction."""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT id, transaction_id, classification, sub_classification,
                       confidence_bps, source, classifier, classifier_version, created_at
                FROM transaction_classifications
                WHERE transaction_id = ?
                """,
                (transaction_id,),
            ).fetchone()
            return dict(row) if row else None

    def list_unclassified_transaction_ids(self, limit: int = 1000) -> list[int]:
        """
        Get transaction IDs that have no classification yet.

        Returns list of transaction IDs for processing.
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT t.id
                FROM transactions t
                WHERE t.id NOT IN (
                    SELECT DISTINCT transaction_id FROM transaction_classifications
                )
                AND t.debit > 0
                AND t.account_id IS NOT NULL AND t.account_id != ''
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [int(row[0]) for row in rows]

    def get_classification_by_loan(self, loan_id: int) -> list[dict[str, Any]]:
        """
        Get classifications linked to a specific loan.

        Used for audit/tracking which transactions were classified as EMI for a loan.
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT tc.*, t.date_iso, t.description, t.amount_paise
                FROM transaction_classifications tc
                JOIN transactions t ON tc.transaction_id = t.id
                WHERE tc.classification = 'liability_payment'
                  AND tc.sub_classification = 'emi'
                  AND t.notes LIKE 'loan:%' || ? || '%'
                """,
                (str(loan_id),),
            ).fetchall()
            return [dict(r) for r in rows]
