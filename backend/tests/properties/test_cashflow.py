"""Property tests for Cashflow Engine using Hypothesis."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Import domain invariants
from tests.domain.invariants import assert_cashflow_result_invariants

# Import Hypothesis strategies from conftest
from .conftest import (
    cash_summary_strategy,
    financial_event_strategy,
)


class TestCashflowEngineProperties:
    """Property tests for compute_monthly_cashflow."""

    @given(
        cash_summary=cash_summary_strategy(),
        events=st.lists(financial_event_strategy(), max_size=5),
    )
    @settings(max_examples=20)
    def test_cashflow_result_satisfies_invariants(
        self, cash_summary: dict[str, Any], events: list[dict[str, Any]]
    ) -> None:
        """Cashflow engine output must satisfy all invariants."""
        from src.engines.cashflow_engine import compute_monthly_cashflow

        result = compute_monthly_cashflow(
            cash_summary=cash_summary,
            financial_events=events,
            scope="household",
            owner_id="self",
        )

        # Validate result structure
        assert_cashflow_result_invariants(result)

        # Cash surplus should be integer
        assert isinstance(result["cash_surplus"], int)

    @given(
        income_paise=st.integers(min_value=50000, max_value=1000000),
        expense_paise=st.integers(min_value=50000, max_value=1000000),
    )
    @settings(max_examples=20)
    def test_no_events_surplus_equals_income_minus_expense(
        self, income_paise: int, expense_paise: int
    ) -> None:
        """Without financial events, cash surplus = income - expense."""
        from src.engines.cashflow_engine import compute_monthly_cashflow

        cash_summary = {"income_paise": income_paise, "expense_paise": expense_paise}

        result = compute_monthly_cashflow(
            cash_summary=cash_summary,
            financial_events=[],
            scope="household",
            owner_id="self",
        )

        expected_surplus = income_paise - expense_paise
        assert result["cash_surplus"] == expected_surplus
        assert result["true_savings"] == expected_surplus
