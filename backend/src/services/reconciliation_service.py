"""Reconciliation business orchestration service."""

from typing import Any

from src.engines.reconciliation_engine import find_potential_matches
from src.repositories.reconciliation_repository import ReconciliationRepository
from src.services.base import BaseService


class ReconciliationService(BaseService):
    """
    Business logic for reconciliation operations.

    Orchestrates reconciliation repository and reconciliation engine.
    """

    def __init__(self, db_path: str | None = None):
        super().__init__(db_path)
        self.repo = ReconciliationRepository(self.db_path)

    def scan_potential_matches(self) -> list[dict[str, Any]]:
        """
        Scan for potential transfer matches across accounts.

        Phase 2B.1: Deterministic matching with confidence scoring.
        Returns potential matches that can be saved as reconciliations.
        """
        return find_potential_matches(self.db_path)

    def get_reconciliations(self, status: str | None = None) -> list[dict[str, Any]]:
        """
        Get all reconciliations with transaction details.

        Args:
            status: Optional filter by status ('pending', 'confirmed', 'rejected')

        Returns:
            List of reconciliation records with transaction details including bank names
        """
        return self.repo.get_reconciliations(status)

    def get_pending_reconciliations(self) -> list[dict[str, Any]]:
        """Get all pending reconciliations."""
        return self.repo.get_pending_reconciliations()

    def insert_reconciliation(
        self,
        debit_txn_id: int,
        credit_txn_id: int,
        debit_account_id: str,
        credit_account_id: str,
        amount_paise: int,
        date_diff_days: int = 0,
        confidence_bps: int = 0,
        match_type: str = "exact",
    ) -> bool:
        """
        Create a reconciliation record between two transactions.

        Phase 2B: Metadata-only, no ledger mutation.
        Uses INSERT OR IGNORE for idempotency.

        Returns:
            True if inserted, False if already exists (ignored)
        """
        return self.repo.insert_reconciliation(
            debit_txn_id=debit_txn_id,
            credit_txn_id=credit_txn_id,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            amount_paise=amount_paise,
            date_diff_days=date_diff_days,
            confidence_bps=confidence_bps,
            match_type=match_type,
        )

    def confirm_reconciliation(self, reconciliation_id: int) -> bool:
        """
        Confirm a pending reconciliation.

        Phase 2B: Updates reconciliation.status only. No ledger mutation.

        Returns:
            True if updated, False if not found or not pending
        """
        return self.repo.confirm_reconciliation(reconciliation_id)

    def reject_reconciliation(self, reconciliation_id: int) -> bool:
        """
        Reject a pending reconciliation.

        Phase 2B: Updates reconciliation.status only. No ledger mutation.

        Returns:
            True if updated, False if not found or not pending
        """
        return self.repo.reject_reconciliation(reconciliation_id)
