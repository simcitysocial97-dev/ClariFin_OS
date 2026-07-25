"""Credit Card Builder - Plain Python builder for credit card data."""

from __future__ import annotations

from typing import Any


class CreditCardBuilder:
    """Build credit card data dictionaries for testing."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {
            "name": "Test Credit Card",
            "bank": "HDFC",
            "account_type": "credit_card",
            "balance_paise": 0,
            "credit_limit_paise": 5000000,
            "is_active": 1,
        }

    def with_balance(self, balance_paise: int) -> CreditCardBuilder:
        """Set credit card balance in paise (negative = debt)."""
        self._data["balance_paise"] = balance_paise
        return self

    def with_credit_limit(self, limit_paise: int) -> CreditCardBuilder:
        """Set credit limit in paise."""
        self._data["credit_limit_paise"] = limit_paise
        return self

    def with_bank(self, bank: str) -> CreditCardBuilder:
        """Set bank name."""
        self._data["bank"] = bank
        return self

    def with_name(self, name: str) -> CreditCardBuilder:
        """Set card name."""
        self._data["name"] = name
        return self

    def build(self) -> dict[str, Any]:
        """Build and return credit card dictionary."""
        return dict(self._data)
