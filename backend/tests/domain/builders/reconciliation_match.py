"""Reconciliation Match Builder - Plain Python builder for reconciliation match data."""

from __future__ import annotations

from typing import Any


class ReconciliationMatchBuilder:
    """Build reconciliation match data dictionaries for testing."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {
            "debit_txn_id": 1,
            "credit_txn_id": 2,
            "debit_account_id": "Account_A",
            "credit_account_id": "Account_B",
            "amount_paise": 100000,
            "date_diff_days": 0,
            "match_confidence": 0.95,
            "match_type": "exact_amount",
            "deterministic_key": "1:2",
        }

    def with_amount(self, amount_paise: int) -> ReconciliationMatchBuilder:
        """Set match amount in paise."""
        self._data["amount_paise"] = amount_paise
        return self

    def with_confidence(self, confidence: float) -> ReconciliationMatchBuilder:
        """Set match confidence (0.0 to 1.0)."""
        self._data["match_confidence"] = confidence
        return self

    def with_date_diff(self, days: int) -> ReconciliationMatchBuilder:
        """Set date difference in days."""
        self._data["date_diff_days"] = days
        return self

    def with_match_type(self, match_type: str) -> ReconciliationMatchBuilder:
        """Set match type."""
        self._data["match_type"] = match_type
        return self

    def with_accounts(
        self, debit_id: str, credit_id: str
    ) -> ReconciliationMatchBuilder:
        """Set debit and credit account IDs."""
        self._data["debit_account_id"] = debit_id
        self._data["credit_account_id"] = credit_id
        return self

    def build(self) -> dict[str, Any]:
        """Build and return reconciliation match dictionary."""
        return dict(self._data)
