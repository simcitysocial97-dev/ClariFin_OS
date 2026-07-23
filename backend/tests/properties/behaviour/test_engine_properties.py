"""Property tests for Behaviour Engine — behaviour scoring and profile."""
from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tests.domain.invariants import assert_behaviour_score_valid


class TestBehaviourEngineProperties:
    """Property tests for Behaviour Engine (business capability: behaviour)."""

    @given(
        monthly_incomes=st.lists(
            st.integers(min_value=100000, max_value=2000000), min_size=3, max_size=24
        ),
        monthly_expenses=st.lists(
            st.integers(min_value=50000, max_value=1500000), min_size=3, max_size=24
        ),
    )
    @settings(max_examples=20)
    def test_income_stability_range(
        self, monthly_incomes: list[int], monthly_expenses: list[int]
    ) -> None:
        """Income stability must be in [0, 1] range."""
        from src.engines.behaviour_engine.cashflow import compute_income_stability

        # Ensure lists match length
        n = min(len(monthly_incomes), len(monthly_expenses))
        incomes = monthly_incomes[:n]

        stability = compute_income_stability(incomes)
        assert 0 <= stability <= 1

    @given(
        credit_advances_count=st.integers(min_value=0, max_value=10),
        revolving_months=st.integers(min_value=0, max_value=12),
        debt_increase_trend=st.floats(
            min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False
        ),
    )
    @settings(max_examples=20)
    def test_debt_cycle_score_range(
        self,
        credit_advances_count: int,
        revolving_months: int,
        debt_increase_trend: float,
    ) -> None:
        """Debt cycle score must be in [0, 100]."""
        from src.engines.behaviour_engine.debt import compute_debt_cycle_score

        score = compute_debt_cycle_score(
            credit_advances_count, revolving_months, debt_increase_trend
        )
        assert_behaviour_score_valid(score, score_name="debt_cycle_score")


class TestAccountEngineProperties:
    """Property tests for Account Engine (business capability: behaviour)."""

    @given(
        balances=st.lists(
            st.integers(min_value=0, max_value=10000000), min_size=1, max_size=100
        ),
    )
    @settings(max_examples=20)
    def test_average_balance_integer(
        self, balances: list[int]
    ) -> None:
        """Average balance must be an integer (paise)."""
        from src.engines.account_engine.balance import compute_average_balance

        avg = compute_average_balance(balances)
        assert isinstance(avg, int)

    @given(
        opening=st.integers(min_value=0, max_value=10000000),
        closing=st.integers(min_value=0, max_value=10000000),
    )
    @settings(max_examples=20)
    def test_balance_change_identity(
        self, opening: int, closing: int
    ) -> None:
        """Balance change = closing - opening."""
        from src.engines.account_engine.balance import compute_balance_change

        change = compute_balance_change(opening, closing)
        assert change == closing - opening
