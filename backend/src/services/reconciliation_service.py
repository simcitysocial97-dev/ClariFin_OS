"""Reconciliation business orchestration service.

Phase 3: Proper orchestration with repository fetching and pure engine.
"""

import json
from datetime import datetime
from typing import Any

from src.engines.reconciliation_engine import (
    find_matches_for_transaction,
    find_potential_matches,
)
from src.models.explanation import (
    CalculationStep,
    Confidence,
    Evidence,
    Explanation,
    ReconciliationMatch,
    ReconciliationResponse,
    SourceReference,
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

    def scan_with_explanation(
        self,
        household_id: str | None = None,
    ) -> ReconciliationResponse:
        """
        Scan for potential transfer matches with full explainability.

        Returns:
            ReconciliationResponse with explanation containing:
            - Evidence for matched transaction pairs
            - Evidence for unmatched transactions
            - Source references for each transaction
            - Calculation steps: load-candidates, match-by-rules, compute-matched, compute-unmatched, summary
            - Confidence based on reconciliation quality
        """
        # Build household account map
        household_account_map: dict[str, str] | None = None
        if household_id:
            accounts = self.account_repo.get_household_accounts(household_id)
            household_account_map = {a["id"]: household_id for a in accounts}
        else:
            all_accounts = self.account_repo.get_all_accounts()
            household_account_map = {}
            for acc in all_accounts:
                hid = acc.get("household_id", "primary")
                if hid:
                    household_account_map[acc["id"]] = hid

        # Fetch unreconciled transactions via repository
        debits = self.repo.get_unreconciled_debits(household_id)
        credits = self.repo.get_unreconciled_credits(household_id)

        # Build evidence for candidate transactions
        candidate_evidence: list[Evidence] = []
        candidate_sources: list[SourceReference] = []

        for debit in debits:
            candidate_evidence.append(Evidence(
                id=f"debit-candidate-{debit.get('id', 'unknown')}",
                type="data",
                description=f"Unreconciled debit: {debit.get('description', 'Unknown')}",
                value=debit.get("debit", 0),
                sourceId=str(debit.get("id", "unknown")),
            ))
            candidate_sources.append(SourceReference(
                type="transaction",
                id=debit.get("id", "unknown"),
                name=debit.get("description", "Unknown"),
                date=debit.get("date_iso"),
            ))

        for credit in credits:
            candidate_evidence.append(Evidence(
                id=f"credit-candidate-{credit.get('id', 'unknown')}",
                type="data",
                description=f"Unreconciled credit: {credit.get('description', 'Unknown')}",
                value=credit.get("credit", 0),
                sourceId=str(credit.get("id", "unknown")),
            ))
            candidate_sources.append(SourceReference(
                type="transaction",
                id=credit.get("id", "unknown"),
                name=credit.get("description", "Unknown"),
                date=credit.get("date_iso"),
            ))

        # Call pure engine function
        matches = find_potential_matches(
            debits=debits,
            credits=credits,
            household_account_map=household_account_map,
            max_date_window_days=3,
        )

        # Build evidence for matched pairs
        matched_evidence: list[Evidence] = []
        matched_sources: list[SourceReference] = []

        for match in matches:
            matched_evidence.append(Evidence(
                id=f"match-{match.get('deterministic_key', 'unknown')}",
                type="data",
                description=f"Matched pair: {match.get('deterministic_key', 'Unknown')}",
                value=match.get("amount", 0) * 100,  # Convert to paise
                sourceId=match.get("deterministic_key", "unknown"),
            ))
            matched_sources.append(SourceReference(
                type="transaction",
                id=match.get("deterministic_key", "unknown"),
                name=f"Match: {match.get('deterministic_key', 'Unknown')}",
            ))

        # Build evidence for unmatched transactions
        matched_debit_ids = {m.get("debit_txn_id") for m in matches}
        matched_credit_ids = {m.get("credit_txn_id") for m in matches}

        unmatched_evidence: list[Evidence] = []
        for debit in debits:
            if debit.get("id") not in matched_debit_ids:
                unmatched_evidence.append(Evidence(
                    id=f"unmatched-debit-{debit.get('id', 'unknown')}",
                    type="data",
                    description=f"Unmatched debit: {debit.get('description', 'Unknown')}",
                    value=debit.get("debit", 0),
                    sourceId=str(debit.get("id", "unknown")),
                ))

        for credit in credits:
            if credit.get("id") not in matched_credit_ids:
                unmatched_evidence.append(Evidence(
                    id=f"unmatched-credit-{credit.get('id', 'unknown')}",
                    type="data",
                    description=f"Unmatched credit: {credit.get('description', 'Unknown')}",
                    value=credit.get("credit", 0),
                    sourceId=str(credit.get("id", "unknown")),
                ))

        # Calculate confidence based on reconciliation quality
        total_candidates = len(debits) + len(credits)
        matched_count = len(matches)
        unmatched_count = len(unmatched_evidence)

        # Confidence: higher when more matches, lower when more unmatched
        confidence_bps = 10000
        confidence_reasons: list[str] = []

        if total_candidates == 0:
            confidence_bps = 0
            confidence_reasons.append("No candidate transactions")
        else:
            # Reduce confidence for unmatched items
            if unmatched_count > 0:
                unmatched_ratio = unmatched_count / total_candidates
                confidence_bps -= int(unmatched_ratio * 3000)  # Up to 30% reduction
                confidence_reasons.append(f"{unmatched_count} unmatched transactions")

            # Reduce confidence for low match rate
            if matched_count == 0:
                confidence_bps -= 2000
                confidence_reasons.append("No matches found")

        # Build calculation steps
        calculation_steps: list[CalculationStep] = [
            CalculationStep(
                stepId="load-candidates",
                description="Load candidate transactions from repository",
                operation="LOOKUP",
                inputIds=[e.id for e in candidate_evidence],
                outputId="candidates-loaded",
                order=1,
            ),
            CalculationStep(
                stepId="match-by-rules",
                description="Match by reconciliation rules (date window, amount match)",
                operation="MATCH",
                inputIds=["candidates-loaded"],
                outputId="matches-found",
                order=2,
            ),
            CalculationStep(
                stepId="compute-matched",
                description="Compute matched amount and pairs",
                operation="ADD",
                inputIds=[e.id for e in matched_evidence],
                outputId="matched-amount",
                order=3,
            ),
            CalculationStep(
                stepId="compute-unmatched",
                description="Compute unmatched transactions",
                operation="FILTER",
                inputIds=[e.id for e in unmatched_evidence],
                outputId="unmatched-items",
                order=4,
            ),
            CalculationStep(
                stepId="reconciliation-summary",
                description="Generate reconciliation summary with confidence",
                operation="LOOKUP",
                inputIds=["matches-found", "unmatched-items"],
                outputId="reconciliation-result",
                order=5,
            ),
        ]

        # Build explanation
        all_evidence = candidate_evidence + matched_evidence + unmatched_evidence
        all_sources = candidate_sources + matched_sources

        explanation = Explanation(
            metric="reconciliation",
            value=matched_count,
            confidence=Confidence(
                value=confidence_bps,
                reason=", ".join(confidence_reasons) if confidence_reasons else "Complete reconciliation analysis",
            ),
            evidence=all_evidence,
            sources=all_sources,
            calculationSteps=calculation_steps,
        )

        # Build response matches
        response_matches: list[ReconciliationMatch] = []
        for m in matches:
            response_matches.append(ReconciliationMatch(
                id=None,
                debit_txn_id=m.get("debit_txn_id", 0),
                credit_txn_id=m.get("credit_txn_id", 0),
                debit_account_id=m.get("debit_account_id", ""),
                credit_account_id=m.get("credit_account_id", ""),
                amount_paise=int(m.get("amount", 0) * 100),
                date_diff_days=m.get("date_diff_days", 0),
                match_confidence=m.get("match_confidence", 0.0),
                match_type=m.get("match_type", "exact"),
                status="pending",
                created_at=None,
                confirmed_at=None,
                debit_date=m.get("debit_date", ""),
                debit_date_iso=m.get("debit_date_iso", ""),
                debit_description=m.get("debit_description", ""),
                debit_amount_paise=m.get("debit_amount_paise", 0),
                debit_bank=m.get("debit_bank", ""),
                credit_date=m.get("credit_date", ""),
                credit_date_iso=m.get("credit_date_iso", ""),
                credit_description=m.get("credit_description", ""),
                credit_amount_paise=m.get("credit_amount_paise", 0),
                credit_bank=m.get("credit_bank", ""),
            ))

        return ReconciliationResponse(
            matches=response_matches,
            count=len(response_matches),
            is_partial=total_candidates == 0,
            partial_reason="No candidate transactions available" if total_candidates == 0 else None,
            last_updated=datetime.now().isoformat(),
            explanation=explanation,
        )

    def get_reconciliation_stats(
        self, household_id: str | None = None
    ) -> dict[str, int | float]:
        """
        Get reconciliation statistics for health score calculation.

        Delegates to repository for data fetching and computes statistics.

        Args:
            household_id: Optional household filter. If None, computes stats for all transactions.

        Returns:
            Dict with coverage_ratio, accuracy_score, health_score, total_transactions,
            matched_transactions, confirmed_count, rejected_count
        """
        return self.repo.get_reconciliation_stats(household_id=household_id)

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