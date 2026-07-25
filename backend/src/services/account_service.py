"""Account Service - Orchestration layer for account operations.

Coordinates repositories and account_engine to implement business logic.
No direct database access - uses repositories only.
"""

from datetime import date
from typing import Any, Literal

from src.engines.account_engine import (
    compute_account_metrics,
    compute_account_status,
    compute_average_balance,
    compute_balance_change,
    compute_balance_growth_percentage,
    compute_balance_trend,
    compute_balance_velocity,
    compute_cash_flow_rate,
    compute_days_since_activity,
    compute_income_expense_ratio,
    is_account_dormant,
)
from src.repositories.account_balance_repository import AccountBalanceRepository
from src.repositories.account_link_repository import AccountLinkRepository
from src.repositories.account_repository import AccountRepository
from src.repositories.institution_repository import InstitutionRepository

BalanceSource = Literal["actual", "projected", "adjusted"]
InstitutionType = Literal["BANK", "WALLET", "BROKER", "OTHER"]
RelationshipType = Literal["TRANSFER", "JOINT", "GUARANTOR"]


def _validate_iso_date(date_str: str) -> date:
    """Validate ISO-8601 date string. Raises ValueError if invalid."""
    return date.fromisoformat(date_str)


class AccountService:
    """Orchestrates account calculation and persistence logic.

    Delegates calculations to account_engine (pure functions).
    Delegates persistence to repositories.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.account_repo = AccountRepository(db_path)
        self.balance_repo = AccountBalanceRepository(db_path)
        self.institution_repo = InstitutionRepository(db_path)
        self.link_repo = AccountLinkRepository(db_path)

    # ============================================================
    # Account CRUD Operations
    # ============================================================

    def create_account(
        self,
        name: str,
        bank: str,
        account_type: str = "savings",
        balance_paise: int = 0,
        account_number_last4: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any] | None:
        """Create a new account record."""
        return self.account_repo.create_account(
            name=name,
            bank=bank,
            account_type=account_type,
            balance_paise=balance_paise,
            account_number_last4=account_number_last4,
            notes=notes,
        )

    def get_account(self, account_id: int | str) -> dict[str, Any] | None:
        """Get account details."""
        return self.account_repo.get_account_by_id(account_id)

    def list_accounts(self) -> list[dict[str, Any]]:
        """Get all active accounts."""
        return self.account_repo.get_all_accounts()

    def update_account(
        self,
        account_id: int | str,
        name: str | None = None,
        bank: str | None = None,
        account_type: str | None = None,
        balance_paise: int | None = None,
        account_number_last4: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any] | None:
        """Update account fields."""
        return self.account_repo.update_account(
            account_id=account_id,
            name=name,
            bank=bank,
            account_type=account_type,
            balance_paise=balance_paise,
            account_number_last4=account_number_last4,
            notes=notes,
        )

    def deactivate_account(self, account_id: int | str) -> bool:
        """Soft delete an account."""
        return self.account_repo.deactivate_account(account_id)

    def get_accounts_by_type(self, account_type: str) -> list[dict[str, Any]]:
        """Get accounts filtered by type."""
        return self.account_repo.get_accounts_by_type(account_type)

    def get_accounts_by_institution(self, bank: str) -> list[dict[str, Any]]:
        """Get accounts filtered by institution."""
        return self.account_repo.get_accounts_by_institution(bank)

    # ============================================================
    # Balance Snapshot Operations
    # ============================================================

    def insert_balance_snapshot(
        self,
        account_id: str,
        balance_paise: int,
        date_iso: str,
        source: BalanceSource = "actual",
    ) -> int:
        """Insert a balance snapshot for an account.

        Validates that account exists and is active before inserting.
        """
        if balance_paise < 0:
            raise ValueError(f"Balance cannot be negative: {balance_paise}")

        _validate_iso_date(date_iso)  # Validate ISO format

        # Verify account exists and is active
        account = self.account_repo.get_account_by_id(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        if not account.get("is_active", 1):
            raise ValueError(f"Account {account_id} is not active")

        return self.balance_repo.insert_balance_snapshot(
            account_id=account_id,
            balance_paise=balance_paise,
            date_iso=date_iso,
            source=source,
        )

    def get_balance_history(
        self, account_id: str, limit: int = 90
    ) -> list[dict[str, Any]]:
        """Get balance history for an account."""
        return self.balance_repo.get_balance_history(account_id, limit)

    def get_latest_balance(self, account_id: str) -> dict[str, Any] | None:
        """Get the most recent balance snapshot for an account."""
        return self.balance_repo.get_latest_balance(account_id)

    # ============================================================
    # Balance Analytics (Engine Delegation)
    # ============================================================

    def calculate_average_balance(self, account_id: str) -> int:
        """Calculate average balance from history."""
        history = self.balance_repo.get_balance_history(account_id)
        balances = [h["balance_paise"] for h in history]
        return compute_average_balance(balances)

    def calculate_balance_change(self, account_id: str) -> int:
        """Calculate balance change between latest two snapshots."""
        history = self.balance_repo.get_balance_history(account_id, limit=2)
        if len(history) < 2:
            return 0
        return compute_balance_change(
            history[1]["balance_paise"], history[0]["balance_paise"]
        )

    def calculate_balance_growth(self, account_id: str) -> int:
        """Calculate balance growth percentage."""
        history = self.balance_repo.get_balance_history(account_id, limit=2)
        if len(history) < 2:
            return 0
        return compute_balance_growth_percentage(
            history[1]["balance_paise"], history[0]["balance_paise"]
        )

    def calculate_balance_trend(self, account_id: str) -> str:
        """Calculate balance trend direction."""
        history = self.balance_repo.get_balance_history(account_id)
        balances = [h["balance_paise"] for h in history]
        return compute_balance_trend(balances)

    def calculate_balance_velocity(self, account_id: str, days: int = 30) -> int:
        """Calculate balance velocity (paise/day)."""
        history = self.balance_repo.get_balance_history(account_id)
        if len(history) < 2:
            return 0

        balances = [h["balance_paise"] for h in history]
        return compute_balance_velocity(balances[-1], balances[0], days)

    # ============================================================
    # Cash Flow (Engine Delegation)
    # ============================================================

    def calculate_cash_flow(self, account_id: str, days: int = 30) -> dict[str, int]:
        """
        Calculate cash flow metrics for an account.

        Note: Transaction integration is pending. This method uses
        balance history as proxy; transaction-based aggregation will be
        added when transaction integration is available.
        """
        history = self.balance_repo.get_balance_history(account_id)
        if len(history) < 2:
            return {
                "net_flow_paise": 0,
                "flow_rate_paise": 0,
                "income_expense_ratio_bps": 0,
            }

        # Use balance changes as proxy for cash flow
        balances = [h["balance_paise"] for h in history]
        net_flow = compute_balance_change(balances[-1], balances[0])
        flow_rate = compute_cash_flow_rate(net_flow, days)

        # Without transaction data, assume balanced flow
        income = max(net_flow, 0) + 100000  # Placeholder
        expense = max(-net_flow, 0) + 100000  # Placeholder
        ratio = compute_income_expense_ratio(income, expense)

        return {
            "net_flow_paise": net_flow,
            "flow_rate_paise": flow_rate,
            "income_expense_ratio_bps": ratio,
        }

    # ============================================================
    # Dormancy (Engine Delegation)
    # ============================================================

    def get_account_status(self, account_id: str) -> str:
        """Get account status (ACTIVE/DORMANT/CLOSED)."""
        account = self.account_repo.get_account_by_id(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        is_active = account.get("is_active", 1)
        # Get last activity from balance history
        history = self.balance_repo.get_balance_history(account_id, limit=1)
        last_activity_date = history[0]["date_iso"] if history else None

        # Get current date - would come from transaction query in full impl
        today = date.today().isoformat()

        return compute_account_status(is_active, last_activity_date, today)

    def is_account_dormant(self, account_id: str, threshold_days: int = 365) -> bool:
        """Check if account is dormant."""
        history = self.balance_repo.get_balance_history(account_id, limit=1)
        if not history:
            return True  # No activity = dormant

        last_activity = history[0]["date_iso"]
        today = date.today().isoformat()
        days = compute_days_since_activity(last_activity, today)
        return is_account_dormant(days, threshold_days)

    def get_days_since_activity(self, account_id: str) -> int:
        """Get days since last activity for an account.

        Returns 0 if no activity history exists.
        """
        history = self.balance_repo.get_balance_history(account_id, limit=1)
        if not history:
            return 0

        last_activity = history[0]["date_iso"]
        today = date.today().isoformat()
        return compute_days_since_activity(last_activity, today)

    # ============================================================
    # Metrics (Engine Delegation)
    # ============================================================

    def get_account_metrics(self, account_id: str) -> dict[str, Any]:
        """Get comprehensive account metrics."""
        account = self.account_repo.get_account_by_id(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Get current balance
        balance = account.get("balance_paise", 0)

        # Get average from history
        avg_balance = self.calculate_average_balance(account_id)

        # Get activity info
        history = self.balance_repo.get_balance_history(account_id, limit=1)
        days_since = 0
        if history:
            today = date.today().isoformat()
            days_since = compute_days_since_activity(history[0]["date_iso"], today)

        # Without transaction integration, use placeholders
        cash_in = 0
        cash_out = 0

        return compute_account_metrics(
            current_balance_paise=balance,
            average_balance_paise=avg_balance,
            cash_in_paise=cash_in,
            cash_out_paise=cash_out,
            days_since_activity=days_since,
        )

    # ============================================================
    # Institution Operations (Pure Orchestration)
    # ============================================================

    def create_institution(
        self,
        institution_id: str,
        name: str,
        institution_type: InstitutionType,
        interest_rate_bps: int | None = None,
        supported_features_json: str | None = None,
    ) -> str:
        """Create an institution record."""
        return self.institution_repo.create(
            institution_id=institution_id,
            name=name,
            institution_type=institution_type,
            interest_rate_bps=interest_rate_bps,
            supported_features_json=supported_features_json,
        )

    def get_institution(self, institution_id: str) -> dict[str, Any] | None:
        """Get institution details."""
        return self.institution_repo.get(institution_id)

    def list_institutions(self) -> list[dict[str, Any]]:
        """Get all institutions."""
        return self.institution_repo.list()

    def update_institution(
        self,
        institution_id: str,
        name: str | None = None,
        institution_type: InstitutionType | None = None,
        interest_rate_bps: int | None = None,
        supported_features_json: str | None = None,
    ) -> dict[str, Any] | None:
        """Update institution fields."""
        return self.institution_repo.update(
            institution_id=institution_id,
            name=name,
            institution_type=institution_type,
            interest_rate_bps=interest_rate_bps,
            supported_features_json=supported_features_json,
        )

    # ============================================================
    # Account Link Operations (Pure Delegation)
    # ============================================================

    def link_accounts(
        self,
        primary_account_id: str,
        linked_account_id: str,
        relationship_type: RelationshipType,
    ) -> bool:
        """Create a link between two accounts."""
        # Validate both accounts exist
        if not self.account_repo.get_account_by_id(primary_account_id):
            raise ValueError(f"Primary account {primary_account_id} not found")
        if not self.account_repo.get_account_by_id(linked_account_id):
            raise ValueError(f"Linked account {linked_account_id} not found")

        return self.link_repo.link_accounts(
            primary_account_id=primary_account_id,
            linked_account_id=linked_account_id,
            relationship_type=relationship_type,
        )

    def unlink_accounts(self, primary_account_id: str, linked_account_id: str) -> bool:
        """Remove a link between two accounts."""
        return self.link_repo.unlink_accounts(primary_account_id, linked_account_id)

    def get_linked_accounts(self, account_id: str) -> list[dict[str, Any]]:
        """Get all accounts linked to the given account."""
        return self.link_repo.get_linked_accounts(account_id)

    # ============================================================
    # Balance Computation (for managed accounts router)
    # ============================================================

    def compute_account_balance(self, account_id: int | str) -> dict[str, Any]:
        """Compute current account balance.

        Returns account with current balance from repository.
        """
        account = self.account_repo.get_account_by_id(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        return account

    def compute_running_balance(self, account_id: int | str) -> list[dict[str, Any]]:
        """Get running balance history for an account.

        Returns balance history as running balance entries.
        """
        history = self.balance_repo.get_balance_history(str(account_id))
        return [
            {
                "date_iso": h["date_iso"],
                "balance_paise": h["balance_paise"],
            }
            for h in history
        ]
