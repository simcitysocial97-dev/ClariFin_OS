"""Transaction Intelligence Service - Orchestrates transaction classification.

Filters to unclassified debits, generates loan schedules, invokes EMI detector,
and persists classifications. Household-aware for multi-user support.
"""
from typing import Any

from src.engines.transaction_intelligence import (
    detect_emi_payment,
    find_loan_candidates_for_account,
)
from src.repositories.account_repository import AccountRepository
from src.repositories.loan_repository import LoanRepository
from src.repositories.transaction_classification_repository import (
    TransactionClassificationRepository,
)
from src.repositories.transaction_repository import TransactionRepository


class TransactionIntelligenceService:
    """
    Orchestrates transaction classification logic.

    Workflow:
        1. Fetch unclassified debit transactions
        2. For each transaction, find matching loan accounts
        3. Generate schedule lazily for each loan (cached after first use)
        4. Invoke detector with plain data (no DB access in detector)
        5. Persist classification on match
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path
        self.txn_repo = TransactionRepository(db_path)
        self.loan_repo = LoanRepository(db_path)
        self.classification_repo = TransactionClassificationRepository(db_path)
        self.account_repo = AccountRepository(db_path)

        # Cache for schedule lookups per loan (avoids regenerating same schedule)
        self._schedule_cache: dict[int, list[dict[str, Any]]] = {}

    def classify_emi_payments(
        self,
        household_id: str | None = None,
        owner_id: str = "self",
    ) -> list[dict[str, Any]]:
        """
        Detect and classify EMI payments among unclassified transactions.

        Args:
            household_id: If provided, filter by household scope.
            owner_id: Default 'self'. If 'self', only classify Self member transactions.

        Returns:
            List of classification results for successful matches.
        """
        results: list[dict[str, Any]] = []

        # Get unclassified debit transactions
        if household_id:
            # Household-scoped: get accounts in household
            accounts = self.account_repo.get_household_accounts(household_id)
            account_ids = [a["id"] for a in accounts] if accounts else []
            txns = self._get_unclassified_debits_for_accounts(account_ids)
        else:
            # Non-household scoped
            txns = self._get_unclassified_debits()

        # Filter by owner_id (multi-user mode)
        # Default owner_id='self' means only classify Self member transactions
        if owner_id == "self":
            txns = [t for t in txns if t.get("member", "Self") == "Self"]

        # Get all active loans
        loans = self.loan_repo.list_loans()

        for txn in txns:
            # Skip if already classified
            if self.classification_repo.get_by_transaction_id(txn["id"]):
                continue

            account_id = txn.get("account_id", "")

            # Find loan candidates where lender matches account
            loan_candidates = find_loan_candidates_for_account(account_id, loans)
            if not loan_candidates:
                continue

            # Build schedule lookup per loan (cached)
            schedule_lookup: dict[tuple[int, str], dict[str, Any]] = {}
            for loan in loan_candidates:
                loan_id = int(loan["id"])
                if loan_id not in self._schedule_cache:
                    self._schedule_cache[loan_id] = self._get_loan_schedule(loan_id)

                for row in self._schedule_cache[loan_id]:
                    key = (loan_id, row["due_date"])
                    # Bank statement rows take precedence over computed
                    if key not in schedule_lookup or row.get("source") == "bank_statement":
                        schedule_lookup[key] = row

            # Detect EMI payment
            detection = detect_emi_payment(txn, loan_candidates, schedule_lookup)
            if not detection:
                continue

            # Persist classification
            self.classification_repo.insert_classification(
                transaction_id=txn["id"],
                classification=detection.classification,
                sub_classification=detection.sub_classification,
                confidence_bps=detection.confidence_bps,
                source=detection.source,
                classifier="loan_emi_detector",
                classifier_version=1,
            )

            results.append({
                "transaction_id": txn["id"],
                "loan_id": detection.matched_entity_id,
                "classification": detection.classification,
                "sub_classification": detection.sub_classification,
                "confidence_bps": detection.confidence_bps,
                "match_reason": detection.match_reason,
            })

        return results

    def _get_unclassified_debits(self) -> list[dict[str, Any]]:
        """Get unclassified debit transactions."""
        classified_ids: list[int] = []
        with self.txn_repo._get_conn() as conn:
            rows = conn.execute(
                "SELECT transaction_id FROM transaction_classifications"
            ).fetchall()
            classified_ids = [int(r[0]) for r in rows]

        with self.txn_repo._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, account_id, date_iso, debit, amount_paise, description
                FROM transactions
                WHERE id NOT IN ({})
                  AND debit > 0
                  AND account_id IS NOT NULL AND account_id != ''
                  AND date_iso IS NOT NULL AND date_iso != ''
            """.format(",".join("?" for _ in classified_ids) if classified_ids else "SELECT id FROM transactions WHERE 1=0"),
                classified_ids if classified_ids else [],
            ).fetchall()
            return [dict(r) for r in rows]

    def _get_unclassified_debits_for_accounts(self, account_ids: list[str]) -> list[dict[str, Any]]:
        """Get unclassified debit transactions for specific accounts."""
        classified_ids: list[int] = []
        with self.txn_repo._get_conn() as conn:
            rows = conn.execute(
                "SELECT transaction_id FROM transaction_classifications"
            ).fetchall()
            classified_ids = [int(r[0]) for r in rows]

        if not account_ids:
            return []

        placeholders = ",".join("?" * len(account_ids))
        with self.txn_repo._get_conn() as conn:
            rows = conn.execute(f"""
                SELECT id, account_id, date_iso, debit, amount_paise, description
                FROM transactions
                WHERE id NOT IN ({",".join("?" for _ in classified_ids) if classified_ids else "SELECT id FROM transactions WHERE 1=0"})
                  AND account_id IN ({placeholders})
                  AND debit > 0
                  AND date_iso IS NOT NULL AND date_iso != ''
            """, classified_ids + account_ids).fetchall()
            return [dict(r) for r in rows]

    def _get_loan_schedule(self, loan_id: int) -> list[dict[str, Any]]:
        """
        Get schedule rows for a loan, using cache and lazy generation.

        This is called via LoanService.get_or_generate_schedule in production.
        Here we inline the logic to avoid circular import.
        """
        # Check cache first
        if loan_id in self._schedule_cache:
            return self._schedule_cache[loan_id]

        # Check if already persisted
        cached = self.loan_repo.get_schedule_rows(loan_id)
        if cached:
            self._schedule_cache[loan_id] = cached
            return cached

        # Generate fresh schedule
        from src.engines.loan_engine import generate_schedule

        loan = self.loan_repo.get_loan(loan_id)
        if not loan:
            return []

        rate_bps = int(loan["interest_rate"] * 100)
        remaining_months = loan["tenure_months"] or 0

        schedule = generate_schedule(
            principal_paise=loan["outstanding_paise"],
            annual_rate_bps=rate_bps,
            tenure_months=remaining_months,
            start_date=loan.get("disbursed_date") or "2025-01-01",
        )

        schedule_dicts = [
            {
                "due_date": row.payment_date,
                "emi_paise": row.emi_paise,
                "principal_paise": row.principal_paise,
                "interest_paise": row.interest_paise,
                "balance_paise": row.balance_paise,
                "source": "computed",
            }
            for row in schedule
        ]

        self.loan_repo.persist_schedule_rows(loan_id, schedule_dicts, source="computed")
        self._schedule_cache[loan_id] = schedule_dicts

        return schedule_dicts