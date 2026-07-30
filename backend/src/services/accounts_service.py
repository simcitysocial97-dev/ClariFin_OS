"""Accounts business orchestration service for Stage 4 Accounts Intelligence Workspace.

Orchestrates account data aggregation and type breakdown calculations.
All monetary values in paise (integer).
"""

from typing import Any, Literal

from src.core.dtos.accounts_dto import (
    AccountCalculationStepDTO,
    AccountDetailDTO,
    AccountEvidenceChainDTO,
    AccountEvidenceItemDTO,
    AccountInsightDTO,
    AccountsDTO,
    AccountsHistoryResponse,
    AccountsTransactionsResponse,
    AccountTransactionDTO,
    AccountTypeBreakdownDTO,
    BalanceHistoryDTO,
)
from src.repositories import (
    AccountBalanceRepository,
    AccountRepository,
    TransactionRepository,
)
from src.services.base import BaseService

# Type alias for account type
AccountType = Literal[
    "savings", "current", "credit_card", "investment", "loan", "other"
]


class AccountsService(BaseService):
    """Service for accounts data aggregation and orchestration."""

    def __init__(self, db_path: str | None = None):
        super().__init__(db_path)
        self.account_repo = AccountRepository(self.db_path)
        self.balance_repo = AccountBalanceRepository(self.db_path)
        self.transaction_repo = TransactionRepository(self.db_path)

    def get_accounts(
        self,
        account_types: list[str] | None = None,
        institutions: list[str] | None = None,
        statuses: list[str] | None = None,
    ) -> AccountsDTO:
        """
        Get all accounts with optional filtering.

        Args:
            account_types: Filter by account types (savings, current, etc.)
            institutions: Filter by institution names
            statuses: Filter by account statuses (active, inactive, closed)

        Returns:
            AccountsDTO with accounts list, total balance, and type breakdown.
        """
        # Get accounts from repository
        accounts = self.account_repo.get_all_accounts()

        # Apply filters
        if account_types:
            accounts = [a for a in accounts if a.get("type") in account_types]
        if institutions:
            accounts = [a for a in accounts if a.get("bank") in institutions]
        if statuses:
            accounts = [a for a in accounts if a.get("status") in statuses]

        # Calculate total balance
        total_balance_paise = sum(int(a.get("balance_paise", 0) or 0) for a in accounts)

        # Calculate type breakdown
        type_breakdown = self._compute_type_breakdown(accounts)

        # Generate insights
        insights = self._generate_insights(accounts, type_breakdown)

        # Build evidence chain
        evidence_chain = self._build_evidence_chain(accounts, total_balance_paise)

        # Map to DTOs
        account_dtos = [
            AccountDetailDTO(
                id=str(a.get("id", "")),
                name=a.get("name", "") or "",
                type=a.get("type", "other") or "other",
                institution=a.get("bank", "") or "",
                balance_paise=int(a.get("balance_paise", 0) or 0),
                currency=a.get("currency", "INR") or "INR",
                status=a.get("status", "active") or "active",
                account_number_last4=a.get("account_number_last4"),
                opened_date=a.get("opened_date"),
                closed_date=a.get("closed_date"),
            )
            for a in accounts
        ]

        return AccountsDTO(
            accounts=account_dtos,
            total_balance_paise=total_balance_paise,
            account_count=len(accounts),
            type_breakdown=type_breakdown,
            insights=insights,
            evidence_chain=evidence_chain,
        )

    def get_account_detail(self, account_id: int | str) -> AccountDetailDTO | None:
        """
        Get detailed information for a single account.

        Args:
            account_id: The account identifier

        Returns:
            AccountDetailDTO or None if not found.
        """
        account = self.account_repo.get_account_by_id(account_id)
        if not account:
            return None

        return AccountDetailDTO(
            id=str(account.get("id", "")),
            name=account.get("name", "") or "",
            type=account.get("type", "other") or "other",
            institution=account.get("bank", "") or "",
            balance_paise=int(account.get("balance_paise", 0) or 0),
            currency=account.get("currency", "INR") or "INR",
            status=account.get("status", "active") or "active",
            account_number_last4=account.get("account_number_last4"),
            opened_date=account.get("opened_date"),
            closed_date=account.get("closed_date"),
        )

    def get_balance_history(
        self, account_id: int | str, limit: int = 90
    ) -> AccountsHistoryResponse:
        """
        Get balance history for an account.

        Args:
            account_id: The account identifier
            limit: Maximum number of history entries (default 90)

        Returns:
            AccountsHistoryResponse with balance history entries.
        """
        history = self.balance_repo.get_balance_history(str(account_id), limit)

        history_dtos = [
            BalanceHistoryDTO(
                date=h.get("date_iso", "") or "",
                balance_paise=int(h.get("balance_paise", 0) or 0),
                account_id=str(account_id),
            )
            for h in history
        ]

        return AccountsHistoryResponse(
            history=history_dtos,
            total_count=len(history_dtos),
        )

    def get_transactions(
        self,
        account_id: int | str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AccountsTransactionsResponse:
        """
        Get transactions for accounts view.

        Args:
            account_id: Optional account filter
            limit: Maximum number of transactions
            offset: Number of transactions to skip

        Returns:
            AccountsTransactionsResponse with transaction data.
        """
        # Get all transactions
        transactions = self.transaction_repo.get_all_transactions()

        # Filter by account if specified
        if account_id:
            transactions = [
                t
                for t in transactions
                if str(t.get("account_id", "")) == str(account_id)
            ]

        # Apply pagination
        paginated = transactions[offset : offset + limit]

        txn_dtos = [
            AccountTransactionDTO(
                id=str(t.get("id", "")),
                date=t.get("date_iso", "") or "",
                description=t.get("description", "") or "",
                amount_paise=int(t.get("amount_paise", 0) or 0),
                category=t.get("category", "uncategorized") or "uncategorized",
                merchant=t.get("merchant"),
            )
            for t in paginated
        ]

        return AccountsTransactionsResponse(
            transactions=txn_dtos,
            total=len(transactions),
            limit=limit,
            offset=offset,
        )

    def get_type_breakdown(self) -> list[AccountTypeBreakdownDTO]:
        """
        Get account type breakdown for analytics.

        Returns:
            List of AccountTypeBreakdownDTO with type distribution.
        """
        accounts = self.account_repo.get_all_accounts()
        return self._compute_type_breakdown(accounts)

    def get_summary(self) -> AccountsDTO:
        """
        Get accounts summary with all accounts.

        Returns:
            AccountsDTO with summary data.
        """
        return self.get_accounts()

    def get_insights(self) -> list[AccountInsightDTO]:
        """
        Generate insights about accounts.

        Returns:
            List of AccountInsightDTO with actionable insights.
        """
        accounts = self.account_repo.get_all_accounts()
        type_breakdown = self._compute_type_breakdown(accounts)
        return self._generate_insights(accounts, type_breakdown)

    def _compute_type_breakdown(
        self, accounts: list[dict[str, Any]]
    ) -> list[AccountTypeBreakdownDTO]:
        """
        Compute account type breakdown from accounts list.

        Args:
            accounts: List of account dictionaries

        Returns:
            List of AccountTypeBreakdownDTO with type distribution.
        """
        # Group by type
        type_totals: dict[str, int] = {}
        type_counts: dict[str, int] = {}

        for account in accounts:
            acc_type = account.get("type", "other") or "other"
            balance = int(account.get("balance_paise", 0) or 0)
            type_totals[acc_type] = type_totals.get(acc_type, 0) + balance
            type_counts[acc_type] = type_counts.get(acc_type, 0) + 1

        # Calculate total for percentage
        total = sum(type_totals.values())

        # Build breakdown
        breakdown: list[AccountTypeBreakdownDTO] = []
        for acc_type, total_balance in type_totals.items():
            percentage = (total_balance / total * 100) if total > 0 else 0.0
            # Cast to the expected type for mypy
            acc_type_literal: AccountType = acc_type  # type: ignore[assignment]
            breakdown.append(
                AccountTypeBreakdownDTO(
                    type=acc_type_literal,
                    count=type_counts[acc_type],
                    total_balance_paise=total_balance,
                    percentage=percentage,
                )
            )

        return breakdown

    def _generate_insights(
        self,
        accounts: list[dict[str, Any]],
        type_breakdown: list[AccountTypeBreakdownDTO],
    ) -> list[AccountInsightDTO]:
        """
        Generate insights about accounts.

        Args:
            accounts: List of account dictionaries
            type_breakdown: Type breakdown data

        Returns:
            List of AccountInsightDTO with insights.
        """
        insights: list[AccountInsightDTO] = []

        # Check for dormant accounts
        for account in accounts:
            if account.get("status") == "inactive":
                insights.append(
                    AccountInsightDTO(
                        type="warning",
                        severity="medium",
                        message=f"Account {account.get('name', 'Unknown')} is inactive",
                        action_url=f"/accounts/{account.get('id')}",
                    )
                )

        # Check for high-value accounts
        for account in accounts:
            balance = int(account.get("balance_paise", 0) or 0)
            if balance > 100000000:  # > ₹10,00,000
                insights.append(
                    AccountInsightDTO(
                        type="positive",
                        severity="low",
                        message=f"High balance in {account.get('name', 'Unknown')}",
                        action_url=f"/accounts/{account.get('id')}",
                    )
                )

        return insights

    def _build_evidence_chain(
        self,
        accounts: list[dict[str, Any]],
        total_balance_paise: int,
    ) -> AccountEvidenceChainDTO | None:
        """
        Build evidence chain for accounts calculation.

        Args:
            accounts: List of account dictionaries
            total_balance_paise: Total balance across all accounts

        Returns:
            AccountEvidenceChainDTO with calculation evidence.
        """
        if not accounts:
            return None

        evidence_items = [
            AccountEvidenceItemDTO(
                type="account",
                summary=f"Account {a.get('name', 'Unknown')} with balance {a.get('balance_paise', 0)} paise",
                source=f"account:{a.get('id')}",
                confidence=100.0,
            )
            for a in accounts[:5]  # Limit to first 5 for evidence
        ]

        return AccountEvidenceChainDTO(
            summary=f"Total balance computed from {len(accounts)} accounts",
            evidence=evidence_items,
            calculation_steps=[
                AccountCalculationStepDTO(
                    name="sum_balances",
                    description="Sum all account balances",
                    inputs={"account_count": len(accounts)},
                    outputs={"total_balance_paise": total_balance_paise},
                )
            ],
            source_references=[f"account:{a.get('id')}" for a in accounts[:5]],
            confidence_score=100.0,
        )
