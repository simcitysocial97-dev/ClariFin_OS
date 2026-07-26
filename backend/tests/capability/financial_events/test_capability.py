"""Smoke tests for Financial Events capability."""

from __future__ import annotations

from tests.golden.builders.salary_plus_loan import load_salary_plus_loan


class TestFinancialEventsCapability:
    """Validate Financial Events capability wiring."""

    def test_import_financial_events_engine(self) -> None:
        """Financial events engine must be importable."""
        from src.engines import financial_events

        assert financial_events is not None

    def test_golden_dataset_financial_event_scenario(self) -> None:
        """Golden dataset must load and validate."""
        data = load_salary_plus_loan()
        assert "transactions" in data or "accounts" in data
