"""Reconciliation domain repository.

LOC WATCH: No repository file > 200 LOC.
If it grows beyond 200, split by sub-domain.
"""
from src.models.reconciliation import Reconciliation
from src.repositories.base import BaseRepository


class ReconciliationRepository(BaseRepository):
    """Repository for reconciliation operations."""

    def get_all_models(self) -> list[Reconciliation]:
        """
        Return all reconciliations as Reconciliation domain models.

        The `amount_paise` column stores integer paise (₹1.00 = 100).
        """
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, debit_txn_id, credit_txn_id,
                       debit_account_id, credit_account_id,
                       amount_paise, date_diff_days,
                       match_confidence, match_type, status
                FROM reconciliations
                ORDER BY created_at DESC
            """).fetchall()
        return [Reconciliation.from_db_row(dict(r)) for r in rows]

    def get_reconciliations(self, status: str | None = None) -> list[dict]:
        """
        Get all reconciliations with transaction details.

        Args:
            status: Optional filter by status ('pending', 'confirmed', 'rejected')

        Returns:
            List of reconciliation records with transaction details including bank names
        """
        with self._get_conn() as conn:
            where_clause = "WHERE r.status = ?" if status else ""
            params = [status] if status else []

            sql = f"""
                SELECT
                    r.id,
                    r.debit_txn_id, r.credit_txn_id,
                    r.debit_account_id, r.credit_account_id,
                    r.amount_paise, r.date_diff_days,
                    r.match_confidence, r.match_type,
                    r.status, r.deterministic_key,
                    r.created_at, r.confirmed_at,
                    dt.date as debit_date, dt.date_iso as debit_date_iso,
                    dt.description as debit_description, dt.debit as debit_amount_paise,
                    dt.account_id as debit_bank,
                    ct.date as credit_date, ct.date_iso as credit_date_iso,
                    ct.description as credit_description, ct.credit as credit_amount_paise,
                    ct.account_id as credit_bank
                FROM reconciliations r
                JOIN transactions dt ON r.debit_txn_id = dt.id
                JOIN transactions ct ON r.credit_txn_id = ct.id
                {where_clause}
                ORDER BY r.created_at DESC
            """

            cur = conn.execute(sql, params)
            rows = [dict(row) for row in cur.fetchall()]
        return rows

    def get_pending_reconciliations(self) -> list[dict]:
        """Get all pending reconciliations."""
        return self.get_reconciliations(status='pending')

    def insert_reconciliation(
        self,
        debit_txn_id: int,
        credit_txn_id: int,
        debit_account_id: str,
        credit_account_id: str,
        amount: float,
        date_diff_days: int = 0,
        match_confidence: float = 0.0,
        match_type: str = "exact",
    ) -> bool:
        """
        Create a reconciliation record between two transactions.

        Phase 2B: Metadata-only, no ledger mutation.
        Uses INSERT OR IGNORE for idempotency.

        Returns:
            True if inserted, False if already exists (ignored)
        """
        with self._get_conn() as conn:
            # Generate deterministic key (smaller id first for consistency)
            min_id = min(debit_txn_id, credit_txn_id)
            max_id = max(debit_txn_id, credit_txn_id)
            deterministic_key = f"{min_id}:{max_id}"

            # Use INSERT OR IGNORE for idempotency
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO reconciliations (
                    debit_txn_id, credit_txn_id,
                    debit_account_id, credit_account_id,
                    amount_paise, date_diff_days,
                    match_confidence, match_type,
                    deterministic_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    debit_txn_id, credit_txn_id,
                    debit_account_id, credit_account_id,
                    int(round(amount * 100)), date_diff_days,
                    round(match_confidence, 4), match_type,
                    deterministic_key
                ),
            )

            inserted = cur.rowcount > 0
        return inserted

    def confirm_reconciliation(self, reconciliation_id: int) -> bool:
        """
        Confirm a pending reconciliation.

        Phase 2B: Updates reconciliation.status only. No ledger mutation.

        Returns:
            True if updated, False if not found or not pending
        """
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                UPDATE reconciliations
                SET status = 'confirmed', confirmed_at = datetime('now')
                WHERE id = ? AND status = 'pending'
                """,
                (reconciliation_id,),
            )
            updated = cur.rowcount > 0
        return updated

    def reject_reconciliation(self, reconciliation_id: int) -> bool:
        """
        Reject a pending reconciliation.

        Phase 2B: Updates reconciliation.status only. No ledger mutation.

        Returns:
            True if updated, False if not found or not pending
        """
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                UPDATE reconciliations
                SET status = 'rejected'
                WHERE id = ? AND status = 'pending'
                """,
                (reconciliation_id,),
            )
            updated = cur.rowcount > 0
        return updated

    def get_confirmed_transfer_ids(self) -> list[tuple]:
        """
        Get all transaction IDs involved in confirmed transfers.

        Returns list of (debit_txn_id, credit_txn_id) tuples for confirmed reconciliations.
        Used by analytics to exclude transfers from spending totals.
        """
        with self._get_conn() as conn:
            cur = conn.execute("""
                SELECT debit_txn_id, credit_txn_id
                FROM reconciliations
                WHERE status = 'confirmed'
            """)
            rows = [(row[0], row[1]) for row in cur.fetchall()]
        return rows
