"""Account domain repository."""
from src.engines.balance_engine import (
    compute_account_balance,
    compute_running_balance,
    get_accounts_list,
)
from src.repositories.base import BaseRepository


class AccountRepository(BaseRepository):
    """Repository for managed account operations."""

    def get_all_accounts(self) -> list[dict]:
        """Get all active persistent accounts."""
        return self._db().get_all_accounts()

    def get_accounts_list(self) -> list[dict]:
        """Get list of all accounts (banks) with their current balances."""
        return get_accounts_list(self.db_path)

    def create_account(
        self,
        name: str,
        bank: str,
        account_type: str = "savings",
        balance_paise: int = 0,
        account_number_last4: str | None = None,
        notes: str | None = None,
    ) -> dict:
        """Create a new persistent account."""
        return self._db().create_account(
            account_id=0,  # Will use auto-increment
            name=name,
            bank=bank,
            account_type=account_type,
            balance_paise=balance_paise,
            account_number_last4=account_number_last4,
            notes=notes,
        )

    def update_account(
        self,
        account_id: int | str,
        name: str | None = None,
        bank: str | None = None,
        account_type: str | None = None,
        balance_paise: int | None = None,
        account_number_last4: str | None = None,
        notes: str | None = None,
    ) -> dict | None:
        """Update an existing account. Only updates provided fields."""
        return self._db().update_account(
            account_id,
            **{k: v for k, v in {
                "name": name,
                "bank": bank,
                "account_type": account_type,
                "balance_paise": balance_paise,
                "account_number_last4": account_number_last4,
                "notes": notes,
            }.items() if v is not None},
        )

    def delete_account(self, account_id: int | str) -> bool:
        """Soft delete an account."""
        return self._db().delete_account(account_id)

    def compute_account_balance(
        self,
        account_id: str,
        starting_balance_paise: int = 0,
    ) -> dict:
        """Compute current balance for a single account."""
        return compute_account_balance(
            db_path=self.db_path,
            account_id=account_id,
            starting_balance_paise=starting_balance_paise,
        )

    def compute_running_balance(
        self,
        account_id: str | None = None,
        starting_balance_paise: int = 0,
    ) -> list[dict]:
        """Compute running balance by replaying all transactions chronologically."""
        return compute_running_balance(
            db_path=self.db_path,
            account_id=account_id,
            starting_balance_paise=starting_balance_paise,
        )
