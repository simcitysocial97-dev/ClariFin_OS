"""Property tests for Behaviour Engine — behaviour scoring and profile."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from tests.invariants import assert_behaviour_score_valid

# --- Strategies ---

@st.composite
def transaction_list(draw):
    """Generate a list of transactions for testing."""
    num_transactions = draw(st.integers(min_value=1, max_value=50))
    transactions = []
    for i in range(num_transactions):
        amount = draw(st.integers(min_value=1, max_value=1000000))
        is_debit = draw(st.booleans())
        transactions.append({
            "id": i + 1,
            "date_iso": f"2023-01-{min(i + 1, 28):02d}",
            "description": f"Transaction {i + 1}",
            "amount": amount if is_debit else -amount,
            "category": draw(st.sampled_from(["Food", "Transport", "Entertainment", "Salary", "Shopping", "Bills"])),
            "account_id": "test_account",
        })
    return transactions


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

    # --- Tests for Utility Functions ---

    @given(
        value=st.floats(min_value=-1000.0, max_value=1000.0),
        min_val=st.floats(min_value=-100.0, max_value=100.0),
        max_val=st.floats(min_value=-100.0, max_value=100.0).filter(lambda x: x > 0),
    )
    @settings(max_examples=20)
    def test_normalize_score_bounds(self, value: float, min_val: float, max_val: float) -> None:
        """Normalize score must return values in [0, 1] range."""
        from src.engines.behavior_engine import _normalize_score

        normalized = _normalize_score(value, min_val, max_val)
        assert 0.0 <= normalized <= 1.0

    @given(
        value=st.floats(min_value=-1000.0, max_value=1000.0),
    )
    @settings(max_examples=20)
    def test_normalize_score_default_bounds(self, value: float) -> None:
        """Normalize score with default bounds must return values in [0, 1] range."""
        from src.engines.behavior_engine import _normalize_score

        normalized = _normalize_score(value)
        assert 0.0 <= normalized <= 1.0

    @given(
        values=st.lists(st.floats(min_value=0.1, max_value=100.0), min_size=2, max_size=20),
    )
    @settings(max_examples=20)
    def test_coefficient_of_variation_non_negative(self, values: list[float]) -> None:
        """Coefficient of variation must be non-negative."""
        from src.engines.behavior_engine import _coefficient_of_variation

        cv = _coefficient_of_variation(values)
        assert cv >= 0.0

    @given(
        values=st.lists(st.floats(min_value=0.0, max_value=100.0), min_size=1, max_size=1),
    )
    @settings(max_examples=20)
    def test_coefficient_of_variation_single_value(self, values: list[float]) -> None:
        """Coefficient of variation with single value must be 0."""
        from src.engines.behavior_engine import _coefficient_of_variation

        cv = _coefficient_of_variation(values)
        assert cv == 0.0

    @given(
        values=st.lists(st.floats(min_value=0.0, max_value=100.0), min_size=2, max_size=20),
        window=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=20)
    def test_moving_average_length(self, values: list[float], window: int) -> None:
        """Moving average must return list of same length as input."""
        from src.engines.behavior_engine import _moving_average

        window = min(window, len(values))
        ma = _moving_average(values, window)
        assert len(ma) == len(values)

    # --- Tests for Core Behaviour Functions ---

    @given(transaction_list())
    @settings(max_examples=20)
    def test_impulsivity_score_bounds(self, transactions: list[dict]) -> None:
        """Impulsivity score must be in [0, 1] range."""
        from src.engines.behavior_engine import _compute_impulsivity_score

        result = _compute_impulsivity_score(transactions)
        score = result.get("impulsivity_score", 0.0)
        assert 0.0 <= score <= 1.0

    @given(transaction_list())
    @settings(max_examples=20)
    def test_habit_stability_score_bounds(self, transactions: list[dict]) -> None:
        """Habit stability score must be in [0, 1] range."""
        from src.engines.behavior_engine import _compute_habit_stability_score

        result = _compute_habit_stability_score(transactions)
        score = result.get("habit_stability_score", 0.0)
        assert 0.0 <= score <= 1.0

    @given(transaction_list())
    @settings(max_examples=20)
    def test_loss_aversion_index_bounds(self, transactions: list[dict]) -> None:
        """Loss aversion index must be in [0, 1] range."""
        from src.engines.behavior_engine import _compute_loss_aversion_index

        result = _compute_loss_aversion_index(transactions)
        index = result.get("loss_aversion_index", 0.0)
        assert 0.0 <= index <= 1.0

    @given(transaction_list())
    @settings(max_examples=20)
    def test_financial_stress_index_bounds(self, transactions: list[dict]) -> None:
        """Financial stress index must be in [0, 1] range."""
        from src.engines.behavior_engine import _compute_financial_stress_index

        result = _compute_financial_stress_index(transactions)
        index = result.get("financial_stress_index", 0.0)
        assert 0.0 <= index <= 1.0

    @given(transaction_list())
    @settings(max_examples=20)
    def test_savings_discipline_score_bounds(self, transactions: list[dict]) -> None:
        """Savings discipline score must be in [0, 1] range."""
        from src.engines.behavior_engine import _compute_savings_discipline_score

        result = _compute_savings_discipline_score(transactions)
        score = result.get("savings_discipline_score", 0.0)
        assert 0.0 <= score <= 1.0

    @given(transaction_list())
    @settings(max_examples=20)
    def test_temporal_patterns_deterministic(self, transactions: list[dict]) -> None:
        """Temporal patterns computation must be deterministic."""
        from src.engines.behavior_engine import _compute_temporal_patterns

        result1 = _compute_temporal_patterns(transactions)
        result2 = _compute_temporal_patterns(transactions)

        # Should return the same result for the same input
        assert result1 == result2

    @given(transaction_list())
    @settings(max_examples=20)
    def test_india_risk_patterns_deterministic(self, transactions: list[dict]) -> None:
        """India risk patterns detection must be deterministic."""
        from src.engines.behavior_engine import detect_india_risk_patterns

        result1 = detect_india_risk_patterns(transactions)
        result2 = detect_india_risk_patterns(transactions)

        # Should return the same result for the same input
        assert result1 == result2


class TestAccountEngineProperties:
    """Property tests for Account Engine (business capability: behaviour)."""

    @given(
        balances=st.lists(
            st.integers(min_value=0, max_value=10000000), min_size=1, max_size=100
        ),
    )
    @settings(max_examples=20)
    def test_average_balance_integer(self, balances: list[int]) -> None:
        """Average balance must be an integer (paise)."""
        from src.engines.account_engine.balance import compute_average_balance

        avg = compute_average_balance(balances)
        assert isinstance(avg, int)

    @given(
        opening=st.integers(min_value=0, max_value=10000000),
        closing=st.integers(min_value=0, max_value=10000000),
    )
    @settings(max_examples=20)
    def test_balance_change_identity(self, opening: int, closing: int) -> None:
        """Balance change = closing - opening."""
        from src.engines.account_engine.balance import compute_balance_change

        change = compute_balance_change(opening, closing)
        assert change == closing - opening
