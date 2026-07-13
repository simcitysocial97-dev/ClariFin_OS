"""Reconciliation business orchestration service.

Phase 3: Proper orchestration with repository fetching and pure engine.
"""

import json
from typing import Any

from src.engines.reconciliation_engine import (
    find_potential_matches,
    find_matches_for_transaction,
)
from src.repositories.account_repository import AccountRepository
from src.repositories.reconciliation_repository import ReconciliationRepository
from src.repositories.transaction_repository import TransactionRepository
from src.services.base import BaseService


class ReconciliationService(BaseService):
    """
    Business logic for reconciliation operations.

    Orchestrates reconciliation repository and reconciliation engine.
    Phase 3: Uses repository for data fetching, pure functions for matching.
    """

    def __init__(self, db_path: str | None = None):
        super().__init__(db_path)
        self.repo = ReconciliationRepository(self.db_path)
        self.account_repo = AccountRepository(self.db_path)
        self.txn_repo = TransactionRepository(self.db_path)

    def scan_potential_matches(
        self,
        household_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Scan for potential transfer matches across accounts.

        Phase 3: Fetches unreconciled transactions via repository,
        passes to pure engine function, returns matches.

        Args:
            household_id: Optional household filter. If None, scans all households.
        """
        # Build household account map
        household_account_map: dict[str, str] | None = None
        if household_id:
            # Single household mode - build map for that household
            accounts = self.account_repo.get_household_accounts(household_id)
            household_account_map = {a["id"]: household_id for a in accounts}
        else:
            # All households mode - build map for all accounts
            all_accounts = self.account_repo.get_all_accounts()
            household_account_map = {}
            for acc in all_accounts:
                hid = acc.get("household_id", "primary")
                if hid:
                    household_account_map[acc["id"]] = hid

        # Fetch unreconciled transactions via repository
        debits = self.repo.get_unreconciled_debits(household_id)
        credits = self.repo.get_unreconciled_credits(household_id)

        # Call pure engine function
        matches = find_potential_matches(
            debits=debits,
            credits=credits,
            household_account_map=household_account_map,
            max_date_window_days=3,
        )

        return matches

    def scan_for_transaction(
        self,
        txn_id: int,
        max_date_window_days: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Find potential matches for a specific transaction.

        Phase 3: Fetches candidates via repository, calls pure engine function.
        """
        # Get target transaction via repository (NOT direct sqlite3)
        target = self.txn_repo.get_transaction_by_id(txn_id)

        if not target:
            return []

        # Fetch all unreconciled transactions for candidates
        # (excluding the target transaction itself)
        all_debits = self.repo.get_unreconciled_debits()
        all_credits = self.repo.get_unreconciled_credits()

        # Determine which pool to use based on transaction type
        if (target.get("debit") or 0) > 0:
            # This is a debit - match against credits
            candidates = all_credits
        else:
            # This is a credit - match against debits
            candidates = all_debits

        # Call pure engine function
        matches = find_matches_for_transaction(
            target_txn=target,
            candidates=candidates,
            max_date_window_days=max_date_window_days,
        )

        return matches

    def insert_match(self, match: dict[str, Any]) -> bool:
        """
        Insert a reconciliation match.

        Phase 3: Uses confidence_bps from match if available.
        """
        return self.repo.insert_reconciliation(
            debit_txn_id=match["debit_txn_id"],
            credit_txn_id=match["credit_txn_id"],
            debit_account_id=match["debit_account_id"],
            credit_account_id=match["credit_account_id"],
            amount=match["amount"],
            date_diff_days=match["date_diff_days"],
            match_confidence=match["match_confidence"],
            match_type=match["match_type"],
            confidence_bps=match.get("confidence_bps"),
        )

    def confirm_reconciliation_with_audit(
        self,
        reconciliation_id: int,
        actor: str = "system",
    ) -> bool:
        """
        Confirm a reconciliation with audit logging.

        Phase 3: Logs audit before and after state change.
        """
        # Get before state
        before = self.repo._get_reconciliation_row(reconciliation_id)
        if not before:
            return False

        # Confirm
        result = self.repo.confirm_reconciliation(reconciliation_id)

        if result:
            # Get after state
            after = self.repo._get_reconciliation_row(reconciliation_id)
            if after:
                self.repo.insert_audit_log(
                    reconciliation_id=reconciliation_id,
                    action="confirm",
                    actor=actor,
                    previous_state=json.dumps({"status": before.get("status")}),
                    new_state=json.dumps({"status": after.get("status")}),
                )

        return result

    def reject_reconciliation_with_audit(
        self,
        reconciliation_id: int,
        actor: str = "system",
    ) -> bool:
        """
        Reject a reconciliation with audit logging.

        Phase 3: Logs audit before and after state change.
        """
        # Get before state
        before = self.repo._get_reconciliation_row(reconciliation_id)
        if not before:
            return False

        # Reject
        result = self.repo.reject_reconciliation(reconciliation_id)

        if result:
            # Get after state
            after = self.repo._get_reconciliation_row(reconciliation_id)
            if after:
                self.repo.insert_audit_log(
                    reconciliation_id=reconciliation_id,
                    action="reject",
                    actor=actor,
                    previous_state=json.dumps({"status": before.get("status")}),
                    new_state=json.dumps({"status": after.get("status")}),
                )

        return result