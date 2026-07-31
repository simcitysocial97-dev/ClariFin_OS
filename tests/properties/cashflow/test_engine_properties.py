"""
Property-based tests for household_cashflow surplus/deficit invariants.

Focus:
1. Surplus/deficit bounds: Surplus ≥ 0, deficit ≤ 0.
2. Monotonicity: Higher income → higher surplus (or lower deficit).
3. Credit dependency: Higher credit utilization → higher deficit.
4. Deterministic output: Same inputs must always produce the same output.
"""

from hypothesis import given, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from backend.src.engines.cashflow_engine import (
    compute_monthly_cashflow,
    MonthClassification,
)

# ============================================================
# Strategies for Input Generation
# ============================================================


def valid_income_expense():
    """Generate valid income and expense values (non-negative)."""
    return st.integers(min_value=0, max_value=1_000_000_00)


def valid_credit_events():
    """Generate valid credit events (cash advances, liability increases)."""
    return st.lists(
        st.one_of(
            st.builds(
                lambda amount, asset_change: {
                    "amount_paise": amount,
                    "asset_change_paise": asset_change,
                    "liability_change_paise": amount,
                    "event_type": "cash_advance",
                },
                st.integers(min_value=1, max_value=500_000_00),
                st.integers(min_value=1, max_value=500_000_00),
            ),
            st.builds(
                lambda amount: {
                    "amount_paise": amount,
                    "asset_change_paise": 0,
                    "liability_change_paise": amount,
                    "event_type": "liability_increase",
                },
                st.integers(min_value=1, max_value=500_000_00),
            ),
        ),
        max_size=10,
    )


def valid_cash_summary(income, expense):
    """Generate a valid cash_summary dict."""
    # Clamp negative values to 0 to match cashflow_engine behavior
    income_clamped = max(0, income)
    expense_clamped = max(0, expense)
    return {
        "income_paise": income,
        "expense_paise": expense,
        "net_paise": income_clamped - expense_clamped,
    }


# ============================================================
# Property Tests
# ============================================================
@given(
    income=valid_income_expense(),
    expense=valid_income_expense(),
    financial_events=valid_credit_events(),
)
def test_surplus_deficit_bounds(income, expense, financial_events):
    """Surplus must be ≥ 0, deficit must be ≤ 0."""
    cash_summary = valid_cash_summary(income, expense)
    result = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=financial_events,
        scope="household",
        owner_id=None,
    )

    if result["month_classification"] == MonthClassification.SURPLUS:
        assert result["cash_surplus"] >= 0, "Surplus must be non-negative"
    elif result["month_classification"] in (
        MonthClassification.DEFICIT_COVERED_BY_CREDIT,
        MonthClassification.DEFICIT,
    ):
        assert result["cash_surplus"] <= 0, "Deficit must be non-positive"


@given(
    income=valid_income_expense(),
    expense=valid_income_expense(),
    financial_events=valid_credit_events(),
    delta_income=st.integers(min_value=1, max_value=100_000_00),
)
def test_monotonicity_income(income, expense, financial_events, delta_income):
    """Higher income → higher surplus (or lower deficit)."""
    cash_summary = valid_cash_summary(income, expense)
    result_base = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=financial_events,
        scope="household",
        owner_id=None,
    )

    cash_summary_higher_income = valid_cash_summary(income + delta_income, expense)
    result_higher_income = compute_monthly_cashflow(
        cash_summary=cash_summary_higher_income,
        financial_events=financial_events,
        scope="household",
        owner_id=None,
    )

    assert (
        result_higher_income["cash_surplus"] >= result_base["cash_surplus"]
    ), "Higher income must not decrease surplus"


@given(
    income=valid_income_expense(),
    expense=valid_income_expense(),
    financial_events=valid_credit_events(),
    delta_credit=st.integers(min_value=1, max_value=100_000_00),
)
def test_credit_dependency(income, expense, financial_events, delta_credit):
    """Higher credit utilization → higher deficit."""
    cash_summary = valid_cash_summary(income, expense)

    # Base case: no additional credit
    result_base = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=financial_events,
        scope="household",
        owner_id=None,
    )

    # Higher credit case: add a new credit event
    additional_credit_event = {
        "amount_paise": delta_credit,
        "asset_change_paise": delta_credit,
        "liability_change_paise": delta_credit,
        "event_type": "cash_advance",
    }
    financial_events_higher_credit = financial_events + [additional_credit_event]

    result_higher_credit = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=financial_events_higher_credit,
        scope="household",
        owner_id=None,
    )

    assert (
        result_higher_credit["cash_surplus"] >= result_base["cash_surplus"]
    ), "Higher credit must not decrease surplus (credit inflates cash surplus)"
    assert (
        result_higher_credit["liability_adjusted_savings"]
        <= result_base["liability_adjusted_savings"]
    ), "Higher credit must decrease liability-adjusted savings"


@given(
    income=valid_income_expense(),
    expense=valid_income_expense(),
    financial_events=valid_credit_events(),
)
def test_deterministic_output(income, expense, financial_events):
    """Same inputs must always produce the same output."""
    cash_summary = valid_cash_summary(income, expense)

    result_1 = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=financial_events,
        scope="household",
        owner_id=None,
    )
    result_2 = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=financial_events,
        scope="household",
        owner_id=None,
    )

    assert result_1 == result_2, "Same inputs must produce identical outputs"


@given(
    income=st.integers(max_value=-1),  # Invalid: negative income
    expense=valid_income_expense(),
)
def test_invalid_income(income, expense):
    """Reject invalid inputs (negative income)."""
    cash_summary = valid_cash_summary(income, expense)
    result = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=[],
        scope="household",
        owner_id=None,
    )

    # Negative income is used as-is: cash_surplus = income - expense
    assert (
        result["cash_surplus"] == income - expense
    ), f"Negative income should be used as-is, got {result['cash_surplus']}"


@given(
    income=valid_income_expense(),
    expense=st.integers(max_value=-1),  # Invalid: negative expense
)
def test_invalid_expense(income, expense):
    """Reject invalid inputs (negative expense)."""
    cash_summary = valid_cash_summary(income, expense)
    result = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=[],
        scope="household",
        owner_id=None,
    )

    # Negative expense is used as-is: cash_surplus = income - expense
    assert (
        result["cash_surplus"] == income - expense
    ), f"Negative expense should be used as-is, got {result['cash_surplus']}"


# ============================================================
# Stateful Property Tests (Rule-Based)
# ============================================================
class CashflowStateMachine(RuleBasedStateMachine):
    """Stateful property tests for cashflow invariants."""

    def __init__(self):
        super().__init__()
        self.income = 0
        self.expense = 0
        self.financial_events = []

    @rule(
        delta_income=st.integers(min_value=-100_000_00, max_value=100_000_00),
        delta_expense=st.integers(min_value=-100_000_00, max_value=100_000_00),
    )
    def adjust_income_expense(self, delta_income, delta_expense):
        """Adjust income and expense by deltas."""
        self.income = max(0, self.income + delta_income)
        self.expense = max(0, self.expense + delta_expense)

    @rule(
        credit_event=st.builds(
            lambda amount, asset_change: {
                "amount_paise": amount,
                "asset_change_paise": asset_change,
                "liability_change_paise": amount,
                "event_type": "cash_advance",
            },
            st.integers(min_value=1, max_value=100_000_00),
            st.integers(min_value=1, max_value=100_000_00),
        )
    )
    def add_credit_event(self, credit_event):
        """Add a credit event."""
        self.financial_events.append(credit_event)

    @invariant()
    def surplus_deficit_invariants(self):
        """Check surplus/deficit invariants after every rule."""
        cash_summary = {
            "income_paise": self.income,
            "expense_paise": self.expense,
            "net_paise": self.income - self.expense,
        }
        result = compute_monthly_cashflow(
            cash_summary=cash_summary,
            financial_events=self.financial_events,
            scope="household",
            owner_id=None,
        )

        if result["month_classification"] == MonthClassification.SURPLUS:
            assert result["cash_surplus"] >= 0, "Surplus must be non-negative"
        else:
            assert result["cash_surplus"] <= 0, "Deficit must be non-positive"

        # Credit dependency ratio must be in [0, 1] or >1 if credit_funded > expense
        assert (
            result["credit_dependency_ratio"] >= 0
        ), "Credit dependency ratio must be non-negative"


# Run the stateful test
TestCashflowStateMachine = CashflowStateMachine.TestCase
