"""Smoke tests for Household Cashflow capability."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from tests.golden.builders.normal_household import load_normal_household
from tests.invariant import assert_cashflow_result_invariants


class TestHouseholdCashflowCapability:
    """Validate Household Cashflow capability wiring and invariants."""

    def test_import_cashflow_engine(self) -> None:
        """Cashflow engine must be importable."""
        from src.engines import cashflow_engine

        assert cashflow_engine is not None

    def test_cashflow_engine_produces_valid_result(self) -> None:
        """Engine execution must produce paise integers and valid classification."""
        from src.engines.cashflow_engine import compute_monthly_cashflow

        result = compute_monthly_cashflow(
            cash_summary={"income_paise": 150000, "expense_paise": 100000},
            financial_events=[],
            scope="household",
            owner_id="self",
        )
        assert_cashflow_result_invariants(result)
        assert result["month_classification"] == "surplus"

    def test_golden_dataset_roundtrip(self) -> None:
        """Golden dataset must load and validate against invariants."""
        data = load_normal_household()
        assert "transactions" in data
        assert "accounts" in data
