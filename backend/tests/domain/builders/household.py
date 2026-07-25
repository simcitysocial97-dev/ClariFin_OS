"""Household Builder - Plain Python builder for household data."""

from __future__ import annotations

from typing import Any


class HouseholdBuilder:
    """Build household data dictionaries for testing."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {
            "id": "primary",
            "name": "Primary Household",
        }

    def with_id(self, household_id: str) -> HouseholdBuilder:
        """Set household ID."""
        self._data["id"] = household_id
        return self

    def build(self) -> dict[str, Any]:
        """Build and return household dictionary."""
        return dict(self._data)
