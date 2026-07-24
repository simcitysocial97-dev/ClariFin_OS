"""Account Builder - Plain Python builder for account data."""
from __future__ import annotations

from typing import Any


class AccountBuilder:
    """Build account data dictionaries for testing."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {
            "name": "Test Account",
            "bank": "HDFC",
            "account_type": "savings",
            "balance_paise": 0,
            "is_active": 1,
        }

    def with_balance(self, balance_paise: int) -> AccountBuilder:
        """Set account balance in paise."""
        self._data["balance_paise"] = balance_paise
        return self

    def with_type(self, account_type: str) -> AccountBuilder:
        """Set account type (savings/current/credit)."""
        self._data["account_type"] = account_type
        return self

    def with_bank(self, bank: str) -> AccountBuilder:
        """Set bank name."""
        self._data["bank"] = bank
        return self

    def build(self) -> dict[str, Any]:
        """Build and return account dictionary."""
        return dict(self._data)
