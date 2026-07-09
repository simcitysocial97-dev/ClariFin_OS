"""Account business orchestration service."""

from typing import Any

from src.engines.balance_engine import (
    compute_account_balance,
    compute_running_balance,
    get_accounts_list,
)
from src.repositories.account_repository import AccountRepository
from src.services.base import BaseService


class AccountService(BaseService):
    """
    Business logic for account management.

    Orchestrates account repository and balance engine.
    """

    def __init__(self, db_path: str | None = None):
        super().__init__(db_path)
        self.repo = AccountRepository(self.db_path)

    def get_accounts_list(self) -> list[dict[str, Any]]:
        """Get list of all accounts (banks) with their current balances."""
        return get_accounts_list(self.db_path)

    def compute_account_balance(
        self, account_id: str, starting_balance_paise: int = 0
    ) -> dict[str, Any]:
        """Compute current balance for a single account."""
        return compute_account_balance(
            db_path=self.db_path,
            account_id=account_id,
            starting_balance_paise=starting_balance_paise,
        )

    def compute_running_balance(
        self, account_id: str | None = None, starting_balance_paise: int = 0
    ) -> list[dict[str, Any]]:
        """Compute running balance by replaying all transactions chronologically."""
        return compute_running_balance(
            db_path=self.db_path,
            account_id=account_id,
            starting_balance_paise=starting_balance_paise,
        )
