"""Capability smoke tests for Financial Events."""

from __future__ import annotations

from tests.golden.builders.salary_plus_loan import load_salary_plus_loan


class TestFinancialEventsCapability:
    """Validate Financial Events capability wiring and invariants."""

    def test_import_financial_events_engine(self) -> None:
        """Financial events engine must be importable."""
        from src.engines import financial_events

        assert financial_events is not None

    def test_import_lineage_walker(self) -> None:
        """Lineage walker pure functions must be importable."""
        from src.engines.financial_events.lineage_walker import (
            LineageProposal,
            detect_rollover_scenarios,
            walk_lineage,
        )

        assert walk_lineage is not None
        assert detect_rollover_scenarios is not None
        assert LineageProposal is not None

    def test_golden_dataset_with_financial_events(self) -> None:
        """Golden dataset with financial events must load and validate."""
        data = load_salary_plus_loan()
        assert "transactions" in data or "accounts" in data
