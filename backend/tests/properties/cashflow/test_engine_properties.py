"""Property tests for Cashflow Engine — business capability: cashflow."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tests.domain.invariants import assert_cashflow_result_invariants
from tests.properties.conftest import cash_summary_strategy, financial_event_strategy


class TestCashflowEngineProperties:
    """Property tests for Cashflow Engine (business capability: cashflow)."""

    @given(
        cash_summary=cash_summary_strategy(),
        events=st.lists(financial_event_strategy(), max_size=5),
    )
    @settings(max_examples=20)
    def test_cashflow_result_invariants_hold(
        self, cash_summary: dict[str, Any], events: list[dict[str, Any]]
    ) -> None:
        """Cashflow engine result must satisfy all invariants."""
        from src.engines.cashflow_engine import compute_monthly_cashflow

        result = compute_monthly_cashflow(
            cash_summary=cash_summary,
            financial_events=events,
            scope="household",
            owner_id="self",
        )
        assert_cashflow_result_invariants(result)
        assert isinstance(result["cash_surplus"], int)
        assert isinstance(result["true_savings"], int)
        assert result["credit_dependency_ratio"] >= 0

    @given(
        income_paise=st.integers(min_value=50000, max_value=1000000),
        expense_paise=st.integers(min_value=50000, max_value=1000000),
    )
    @settings(max_examples=20)
    def test_cashflow_no_events_true_savings(
        self, income_paise: int, expense_paise: int
    ) -> None:
        """Without events, true_savings equals cash_surplus."""
        from src.engines.cashflow_engine import compute_monthly_cashflow

        cash_summary = {"income_paise": income_paise, "expense_paise": expense_paise}
        result = compute_monthly_cashflow(
            cash_summary=cash_summary,
            financial_events=[],
            scope="household",
            owner_id="self",
        )
        assert result["true_savings"] == result["cash_surplus"]

    @given(
        cash_summary=cash_summary_strategy(),
        events=st.lists(financial_event_strategy(), max_size=3),
    )
    @settings(max_examples=20)
    def test_cashflow_classification_valid(
        self, cash_summary: dict[str, Any], events: list[dict[str, Any]]
    ) -> None:
        """Month classification must be one of the three valid values."""
        from src.engines.cashflow_engine import compute_monthly_cashflow

        result = compute_monthly_cashflow(
            cash_summary=cash_summary,
            financial_events=events,
            scope="household",
            owner_id="self",
        )
        valid = {"surplus", "deficit_covered_by_credit", "deficit"}
        assert result["month_classification"] in valid

    @given(
        income_paise=st.integers(min_value=100000, max_value=500000),
        expense_paise=st.integers(min_value=10000, max_value=99999),
    )
    @settings(max_examples=20)
    def test_cashflow_surplus_classification(
        self, income_paise: int, expense_paise: int
    ) -> None:
        """When income > expense, month is classified as surplus."""
        from src.engines.cashflow_engine import compute_monthly_cashflow

        cash_summary = {"income_paise": income_paise, "expense_paise": expense_paise}
        result = compute_monthly_cashflow(
            cash_summary=cash_summary,
            financial_events=[],
            scope="household",
            owner_id="self",
        )
        assert result["month_classification"] == "surplus"
        assert result["credit_dependency_ratio"] == 0.0
