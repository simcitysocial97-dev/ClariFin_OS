"""Reconciliation domain repository."""
from src.repositories.base import BaseRepository


class ReconciliationRepository(BaseRepository):
    """Repository for reconciliation operations."""

    def get_reconciliations(self, status: str | None = None) -> list[dict]:
        """
        Get all reconciliations with transaction details.

        Args:
            status: Optional filter by status ('pending', 'confirmed', 'rejected')

        Returns:
            List of reconciliation records with transaction details including bank names
        """
        return self._db().get_reconciliations(status=status)

    def get_pending_reconciliations(self) -> list[dict]:
        """Get all pending reconciliations."""
        return self._db().get_pending_reconciliations()

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
        return self._db().insert_reconciliation(
            debit_txn_id=debit_txn_id,
            credit_txn_id=credit_txn_id,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            amount=amount,
            date_diff_days=date_diff_days,
            match_confidence=match_confidence,
            match_type=match_type,
        )

    def confirm_reconciliation(self, reconciliation_id: int) -> bool:
        """
        Confirm a pending reconciliation.

        Phase 2B: Updates reconciliation.status only. No ledger mutation.

        Returns:
            True if updated, False if not found or not pending
        """
        return self._db().confirm_reconciliation(reconciliation_id)

    def reject_reconciliation(self, reconciliation_id: int) -> bool:
        """
        Reject a pending reconciliation.

        Phase 2B: Updates reconciliation.status only. No ledger mutation.

        Returns:
            True if updated, False if not found or not pending
        """
        return self._db().reject_reconciliation(reconciliation_id)

    def get_confirmed_transfer_ids(self) -> list[tuple]:
        """
        Get all transaction IDs involved in confirmed transfers.

        Returns list of (debit_txn_id, credit_txn_id) tuples for confirmed reconciliations.
        Used by analytics to exclude transfers from spending totals.
        """
        return self._db().get_confirmed_transfer_ids()
