"""Transaction Builder - Plain Python builder for transaction data."""
from __future__ import annotations

from typing import Any


class TransactionBuilder:
    """Build transaction data dictionaries for testing."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {
            "date_iso": "2025-01-01",
            "description": "Test Transaction",
            "amount_paise": 10000,
            "type": "debit",
            "account_id": "HDFC_SB",
            "member": "Self",
            "category": "Miscellaneous",
        }

    def with_amount(self, amount_paise: int) -> TransactionBuilder:
        """Set transaction amount in paise."""
        self._data["amount_paise"] = amount_paise
        return self

    def with_type(self, txn_type: str) -> TransactionBuilder:
        """Set transaction type (debit/credit)."""
        self._data["type"] = txn_type
        return self

    def with_date(self, date_iso: str) -> TransactionBuilder:
        """Set transaction date (ISO format)."""
        self._data["date_iso"] = date_iso
        return self

    def with_description(self, description: str) -> TransactionBuilder:
        """Set transaction description."""
        self._data["description"] = description
        return self

    def with_account(self, account_id: str) -> TransactionBuilder:
        """Set account ID."""
        self._data["account_id"] = account_id
        return self

    def build(self) -> dict[str, Any]:
        """Build and return transaction dictionary."""
        return dict(self._data)
