"""Statement Builder - Plain Python builder for statement data."""
from __future__ import annotations

from typing import Any


class StatementBuilder:
    """Build statement data dictionaries for testing."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {
            "bank": "HDFC",
            "file_name": "test_statement.pdf",
            "statement_date": "2025-01-31",
            "due_date": "2025-02-21",
            "total_outstanding_paise": 5000000,
            "min_due_paise": 50000,
        }

    def with_statement_date(self, date_iso: str) -> StatementBuilder:
        """Set statement date."""
        self._data["statement_date"] = date_iso
        return self

    def with_due_date(self, date_iso: str) -> StatementBuilder:
        """Set due date."""
        self._data["due_date"] = date_iso
        return self

    def with_outstanding(self, outstanding_paise: int) -> StatementBuilder:
        """Set total outstanding in paise."""
        self._data["total_outstanding_paise"] = outstanding_paise
        return self

    def with_min_due(self, min_due_paise: int) -> StatementBuilder:
        """Set minimum due in paise."""
        self._data["min_due_paise"] = min_due_paise
        return self

    def build(self) -> dict[str, Any]:
        """Build and return statement dictionary."""
        return dict(self._data)
