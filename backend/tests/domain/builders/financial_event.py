"""Financial Event Builder - Plain Python builder for financial event data."""

from __future__ import annotations

from typing import Any


class FinancialEventBuilder:
    """Build financial event data dictionaries for testing."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {
            "event_type": "cash_advance",
            "amount_paise": 100000,
            "asset_change_paise": 100000,
            "liability_change_paise": 0,
            "expense_paise": 0,
            "income_paise": 0,
            "provider": "CRED",
            "date_iso": "2025-01-15",
        }

    def with_type(self, event_type: str) -> FinancialEventBuilder:
        """Set event type."""
        self._data["event_type"] = event_type
        return self

    def with_amount(self, amount_paise: int) -> FinancialEventBuilder:
        """Set event amount in paise."""
        self._data["amount_paise"] = amount_paise
        return self

    def with_provider(self, provider: str) -> FinancialEventBuilder:
        """Set provider name."""
        self._data["provider"] = provider
        return self

    def with_date(self, date_iso: str) -> FinancialEventBuilder:
        """Set event date (ISO format)."""
        self._data["date_iso"] = date_iso
        return self

    def with_asset_change(self, change_paise: int) -> FinancialEventBuilder:
        """Set asset change in paise."""
        self._data["asset_change_paise"] = change_paise
        return self

    def with_liability_change(self, change_paise: int) -> FinancialEventBuilder:
        """Set liability change in paise."""
        self._data["liability_change_paise"] = change_paise
        return self

    def build(self) -> dict[str, Any]:
        """Build and return financial event dictionary."""
        return dict(self._data)
