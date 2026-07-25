"""Transaction Intelligence Service - Orchestrates transaction classification.

Filters to unclassified debits, generates loan schedules, invokes EMI detector,
and persists classifications. Household-aware for multi-user support.
Also emits FinancialEvents for classified transactions.
"""

from typing import Any

# DEFAULT_ROLLOVER_LOOKBACK_DAYS removed - unused in this file
from src.engines.transaction_intelligence import (
    detect_cash_conversion,
    detect_emi_payment,
    find_loan_candidates_for_account,
)
from src.engines.transaction_intelligence.cc_payment_detector import (
    detect_cc_payment,
    extract_card_last4,
)
from src.models.financial_event import FinancialEvent
from src.repositories.account_repository import AccountRepository
from src.repositories.credit_card_repository import CreditCardRepository
from src.repositories.financial_event_repository import FinancialEventRepository
from src.repositories.liquidity_pattern_repository import LiquidityPatternRepository
from src.repositories.loan_repository import LoanRepository
from src.repositories.statement_repository import StatementRepository
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
        self.event_repo = FinancialEventRepository(db_path)

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
                    if (
                        key not in schedule_lookup
                        or row.get("source") == "bank_statement"
                    ):
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

            # Emit FinancialEvent for EMI payment
            event_id = self._emit_financial_event(
                event_type="emi_payment",
                transaction_id=txn["id"],
                account_id=txn.get("account_id", ""),
                amount_paise=txn.get("amount_paise", 0),
                date_iso=txn.get("date_iso", ""),
                category=detection.classification,
                sub_type=detection.sub_classification,
                confidence_bps=detection.confidence_bps,
                household_id=household_id or "primary",
            )

            results.append(
                {
                    "transaction_id": txn["id"],
                    "loan_id": detection.matched_entity_id,
                    "classification": detection.classification,
                    "sub_classification": detection.sub_classification,
                    "confidence_bps": detection.confidence_bps,
                    "match_reason": detection.match_reason,
                    "event_id": event_id,
                }
            )

        return results

    def classify_cc_payments(
        self,
        household_id: str | None = None,
        owner_id: str = "self",
    ) -> list[dict[str, Any]]:
        """
        Detect and classify credit card payments among unclassified transactions.

        Args:
            household_id: If provided, filter by household scope.
            owner_id: Default 'self'. If 'self', only classify Self member transactions.

        Returns:
            List of classification results for successful matches.
        """
        results: list[dict[str, Any]] = []

        # Get unclassified debit transactions
        if household_id:
            accounts = self.account_repo.get_household_accounts(household_id)
            account_ids = [a["id"] for a in accounts] if accounts else []
            txns = self._get_unclassified_debits_for_accounts(account_ids)
        else:
            txns = self._get_unclassified_debits()

        # Filter by owner_id
        if owner_id == "self":
            txns = [t for t in txns if t.get("member", "Self") == "Self"]

        stmt_repo = StatementRepository(self.db_path)

        for txn in txns:
            # Skip if already classified
            if self.classification_repo.get_by_transaction_id(txn["id"]):
                continue

            description = txn.get("description", "")
            date_iso = txn.get("date_iso", "")

            # Extract card last4 from description
            card_last4 = extract_card_last4(description)
            if not card_last4:
                continue

            # Get bank from account (for now, use account_id as bank hint)
            # In production, would need to map account to bank for CC statements
            account_id = txn.get("account_id", "")

            # Try to find matching statement for this card
            statement = stmt_repo.find_matching_statement(
                bank=account_id,  # Using account_id as bank hint
                card_last4=card_last4,
                payment_date=date_iso,
            )

            # Detect CC payment
            detection = detect_cc_payment(txn, statement)
            if not detection:
                continue

            # Persist classification with lifecycle details
            self.classification_repo.insert_classification(
                transaction_id=txn["id"],
                classification=detection.classification,
                sub_classification="cc_payment",
                confidence_bps=detection.confidence_bps,
                source=detection.source,
                classifier="cc_payment_detector",
                classifier_version=1,
                lifecycle_state=detection.lifecycle_state,
                outstanding_paise=detection.remaining_outstanding_paise,
                payment_channel=detection.payment_channel,
                matched_statement_id=detection.matched_statement_id,
            )

            results.append(
                {
                    "transaction_id": txn["id"],
                    "matched_statement_id": detection.matched_statement_id,
                    "classification": detection.classification,
                    "lifecycle_state": detection.lifecycle_state,
                    "payment_channel": detection.payment_channel,
                    "confidence_bps": detection.confidence_bps,
                    "match_reason": detection.match_reason,
                }
            )

        return results

    def classify_cash_conversions(
        self,
        household_id: str | None = None,
        owner_id: str = "self",
    ) -> list[dict[str, Any]]:
        """
        Detect and classify cash conversions (liquidity extraction) among unclassified transactions.

        Liquidity extraction: Debit from bank account via CRED/Cheq/Spaid/NoBroker
        with a corresponding credit to savings/current account.

        Args:
            household_id: If provided, filter by household scope.
            owner_id: Default 'self'. If 'self', only classify Self member transactions.

        Returns:
            List of classification results for successful matches.
        """
        results: list[dict[str, Any]] = []

        # Initialize pattern repository
        pattern_repo = LiquidityPatternRepository(self.db_path)

        # Get active patterns
        provider_patterns = pattern_repo.get_active_provider_patterns()
        purpose_patterns = pattern_repo.get_active_purpose_patterns()

        # Get unclassified debit transactions
        if household_id:
            accounts = self.account_repo.get_household_accounts(household_id)
            account_ids = [a["id"] for a in accounts] if accounts else []
            txns = self._get_unclassified_debits_for_accounts(account_ids)
        else:
            txns = self._get_unclassified_debits()

        # Filter by owner_id
        if owner_id == "self":
            txns = [t for t in txns if t.get("member", "Self") == "Self"]

        # Get household-scoped credit candidates (savings/current accounts only)
        # Also build account context for statement lookup
        all_accounts_for_context: list[dict[str, Any]] = []
        if household_id:
            all_accounts_for_context = self.account_repo.get_household_accounts(
                household_id
            )
            household_account_ids = (
                [a["id"] for a in all_accounts_for_context]
                if all_accounts_for_context
                else []
            )
            credit_candidates = self._get_unclassified_credits_for_accounts(
                household_account_ids
            )
        else:
            all_accounts_for_context = self.account_repo.get_all_accounts()
            credit_candidates = self._get_unclassified_credits()

        # Build account context for household/id checks
        account_context: dict[str, dict[str, Any]] = {}
        for acc in all_accounts_for_context:
            account_context[acc["id"]] = acc

        # Enrich transactions with household_id and account_type
        for txn in txns:
            acc = account_context.get(txn.get("account_id", ""), {})
            txn["household_id"] = acc.get("household_id", household_id or "primary")
            txn["account_type"] = acc.get("account_type", "savings")

        for credit in credit_candidates:
            acc = account_context.get(credit.get("account_id", ""), {})
            credit["household_id"] = acc.get("household_id", household_id or "primary")
            credit["account_type"] = acc.get("account_type", "savings")

        card_repo = CreditCardRepository(self.db_path)
        stmt_repo = StatementRepository(self.db_path)

        for txn in txns:
            # Skip if already classified
            if self.classification_repo.get_by_transaction_id(txn["id"]):
                continue

            # Check if this transaction looks like liquidity extraction
            description = txn.get("description", "")
            has_provider_pattern = any(
                self._match_description_pattern_for_detection(
                    description, p["description_pattern"]
                )
                for p in provider_patterns
            )

            if not has_provider_pattern:
                continue

            # Try to find matching statement for due date bonus
            # Only applies to credit card account types (CC cash advances)
            account_id = txn.get("account_id", "")
            date_iso = txn.get("date_iso", "")
            account_info = account_context.get(account_id, {})

            statement_row = None
            if account_info.get("account_type") == "credit_card":
                # Get CC info for this account
                cards = card_repo.list_cards(account_id)
                if cards:
                    card = cards[0]  # Take first active card if multiple
                    bank = card.get("bank", "")
                    card_last4 = card.get("card_last4", "")
                    if bank and card_last4:
                        statement_row = stmt_repo.get_statement_covering_date(
                            bank=bank,
                            card_last4=card_last4,
                            txn_date=date_iso,
                        )

            # Detect cash conversion
            detection = detect_cash_conversion(
                cc_debit_txn=txn,
                candidate_credits=credit_candidates,
                provider_patterns=provider_patterns,
                purpose_patterns=purpose_patterns,
                statement_row=statement_row,
            )

            if not detection:
                continue

            # Persist classification
            # For unknown providers, skip auto-classification
            if detection.zone == "unmatched_provider":
                results.append(
                    {
                        "transaction_id": txn["id"],
                        "classification": "cash_conversion",
                        "sub_classification": "unmatched_provider",
                        "confidence_bps": detection.confidence_bps,
                        "zone": detection.zone,
                        "provider_name": detection.provider_name,
                        "purpose": detection.purpose,
                        "fee_paise": detection.fee_paise,
                        "fee_bps": detection.fee_bps,
                        "match_reason": detection.match_reason,
                        "narrative": detection.narrative,
                    }
                )
                continue  # Don't persist, just report

            # Emit financial event for cash conversion
            # Stores both debit and credit transaction IDs, plus fee/asset/liability details
            event_id = self._emit_cash_advance_event(
                debit_txn_id=txn["id"],
                credit_txn_id=detection.matched_credit_transaction_id,
                account_id=txn.get("account_id", ""),
                amount_paise=txn.get("debit", 0) or 0,
                fee_paise=detection.fee_paise,
                date_iso=txn.get("date_iso", ""),
                provider=detection.provider_name,
                category="cash_conversion",
                sub_type=detection.purpose,
                confidence_bps=detection.confidence_bps,
                household_id=txn.get("household_id", "primary"),
            )

            results.append(
                {
                    "transaction_id": txn["id"],
                    "matched_credit_transaction_id": detection.matched_credit_transaction_id,
                    "classification": "cash_conversion",
                    "provider_name": detection.provider_name,
                    "purpose": detection.purpose,
                    "zone": detection.zone,
                    "confidence_bps": detection.confidence_bps,
                    "fee_paise": detection.fee_paise,
                    "fee_bps": detection.fee_bps,
                    "match_reason": detection.match_reason,
                    "narrative": detection.narrative,
                    "event_id": event_id,
                }
            )

        return results

    def _emit_financial_event(
        self,
        event_type: str,
        transaction_id: int,
        account_id: str,
        amount_paise: int,
        date_iso: str,
        category: str = "",
        sub_type: str | None = None,
        provider: str | None = None,
        confidence_bps: int = 0,
        household_id: str = "primary",
        outstanding_paise: int = 0,
    ) -> int:
        """
        Create and persist a FinancialEvent from a classification result.

        Returns the database ID of the created event.
        """
        event = FinancialEvent(
            event_type=event_type,  # type: ignore[arg-type]
            transaction_ids=[transaction_id],
            amount_paise=amount_paise,
            date_iso=date_iso,
            account_id=account_id,
            category=category,
            sub_type=sub_type,
            provider=provider,
            confidence_bps=confidence_bps,
            household_id=household_id,
            outstanding_paise=outstanding_paise,
        )
        return self.event_repo.insert_event(event)

    def _emit_cash_advance_event(
        self,
        debit_txn_id: int,
        credit_txn_id: int,
        account_id: str,
        amount_paise: int,
        fee_paise: int,
        date_iso: str,
        provider: str | None = None,
        category: str = "cash_conversion",
        sub_type: str | None = None,
        confidence_bps: int = 0,
        household_id: str = "primary",
    ) -> int:
        """
        Create and persist a credit_card_cash_advance FinancialEvent.

        Stores both debit and credit transaction IDs, along with the granular
        fee/asset/liability details needed for true cashflow calculation.

        Returns the database ID of the created event.
        """
        # asset_change_paise = credit received (positive)
        # liability_change_paise = amount transacted (positive - borrowing)
        # expense_paise = fee only
        credit_txn_amount = None
        with self.txn_repo._get_conn() as conn:
            row = conn.execute(
                "SELECT credit FROM transactions WHERE id = ?",
                (credit_txn_id,),
            ).fetchone()
            if row:
                credit_txn_amount = int(row["credit"]) if row["credit"] else 0

        asset_change_paise = (
            credit_txn_amount if credit_txn_amount else amount_paise - fee_paise
        )
        liability_change_paise = amount_paise
        expense_paise = fee_paise

        event = FinancialEvent(
            event_type="credit_card_cash_advance",
            transaction_ids=[debit_txn_id, credit_txn_id],
            amount_paise=amount_paise,
            asset_change_paise=asset_change_paise,
            liability_change_paise=liability_change_paise,
            expense_paise=expense_paise,
            date_iso=date_iso,
            account_id=account_id,
            category=category,
            sub_type=sub_type,
            provider=provider,
            confidence_bps=confidence_bps,
            household_id=household_id,
        )
        return self.event_repo.insert_event(event)

    def _match_description_pattern_for_detection(
        self, description: str, pattern: str
    ) -> bool:
        """Check if description matches a regex pattern (case-insensitive)."""
        import re

        try:
            return bool(re.search(pattern, description, re.IGNORECASE))
        except re.error:
            return False

    def _get_unclassified_credits(self) -> list[dict[str, Any]]:
        """Get unclassified credit transactions."""
        with self.txn_repo._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, account_id, date_iso, credit, amount_paise, description
                FROM transactions
                WHERE (id NOT IN (
                    SELECT DISTINCT transaction_id FROM transaction_classifications
                ))
                AND credit > 0
                AND account_id IS NOT NULL AND account_id != ''
                AND date_iso IS NOT NULL AND date_iso != ''
            """).fetchall()
        return [dict(r) for r in rows]

    def _get_unclassified_credits_for_accounts(
        self, account_ids: list[str]
    ) -> list[dict[str, Any]]:
        """Get unclassified credit transactions for specific accounts."""
        if not account_ids:
            return []

        with self.txn_repo._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, account_id, date_iso, credit, amount_paise, description
                FROM transactions
                WHERE (id NOT IN (
                    SELECT DISTINCT transaction_id FROM transaction_classifications
                ))
                AND account_id IN ({})
                AND credit > 0
                AND account_id IS NOT NULL AND account_id != ''
                AND date_iso IS NOT NULL AND date_iso != ''
            """.format(",".join("?" for _ in account_ids)),
                account_ids,
            ).fetchall()
        return [dict(r) for r in rows]

    def _get_unclassified_debits(self) -> list[dict[str, Any]]:
        """Get unclassified debit transactions."""
        classified_ids: list[int] = []
        with self.txn_repo._get_conn() as conn:
            rows = conn.execute(
                "SELECT transaction_id FROM transaction_classifications"
            ).fetchall()
            classified_ids = [int(r[0]) for r in rows]

        with self.txn_repo._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, account_id, date_iso, debit, amount_paise, description
                FROM transactions
                WHERE id NOT IN ({})
                  AND debit > 0
                  AND account_id IS NOT NULL AND account_id != ''
                  AND date_iso IS NOT NULL AND date_iso != ''
            """.format(
                    ",".join("?" for _ in classified_ids)
                    if classified_ids
                    else "SELECT id FROM transactions WHERE 1=0"
                ),
                classified_ids if classified_ids else [],
            ).fetchall()
            return [dict(r) for r in rows]

    def _get_unclassified_debits_for_accounts(
        self, account_ids: list[str]
    ) -> list[dict[str, Any]]:
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
            rows = conn.execute(
                f"""
                SELECT id, account_id, date_iso, debit, amount_paise, description
                FROM transactions
                WHERE id NOT IN ({",".join("?" for _ in classified_ids) if classified_ids else "SELECT id FROM transactions WHERE 1=0"})
                  AND account_id IN ({placeholders})
                  AND debit > 0
                  AND date_iso IS NOT NULL AND date_iso != ''
            """,
                classified_ids + [str(aid) for aid in account_ids],
            ).fetchall()
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
