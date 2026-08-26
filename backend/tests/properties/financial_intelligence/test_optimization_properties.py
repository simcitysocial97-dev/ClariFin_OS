"""Property-based tests for financial_intelligence: optimization & planning.

M9-C42.25 — meaningful behavioral properties binding optimization.py,
goal_planner.py, and scenario.py. Monetary values are integer paise; rates
are integer basis points.
"""

from __future__ import annotations

from decimal import Decimal

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from src.engines.financial_intelligence.goal_planner import (
    calculate_debt_payoff_projection,
    calculate_emergency_fund_target,
    calculate_goal_projection,
)
from src.engines.financial_intelligence.optimization import (
    _sum_high_interest_debt,
    calculate_financial_action_score,
    derive_cash_advance_debt_entry,
    rank_debt_payoff_strategy,
)

SETTINGS = settings(max_examples=30, suppress_health_check=[HealthCheck.differing_executors])

paise = st.integers(min_value=0, max_value=10_000_000)
pos_paise = st.integers(min_value=1, max_value=10_000_000)
rate_bps = st.integers(min_value=0, max_value=6000)


class TestEmergencyFundProperties:
    @SETTINGS
    @given(expenses=paise, months=st.integers(min_value=1, max_value=24))
    def test_target_is_product(self, expenses: int, months: int) -> None:
        result = calculate_emergency_fund_target(expenses, months_of_cover=months)
        if expenses <= 0:
            assert result["recommended_target_paise"] == 0
        else:
            assert result["recommended_target_paise"] == expenses * months
        assert result["months_of_cover"] == months


class TestGoalProjectionProperties:
    @SETTINGS
    @given(target=pos_paise, current=paise)
    def test_already_achieved_fast_path(self, target: int, current: int) -> None:
        assume(current >= target)
        result = calculate_goal_projection(target, current, [])
        assert result["achieved"] is True
        assert result["months_required"] == 0
        assert result["confidence"] == Decimal("1.0")

    @SETTINGS
    @given(target=pos_paise, current=paise)
    def test_no_forecast_never_achieved(self, target: int, current: int) -> None:
        assume(current < target)
        result = calculate_goal_projection(target, current, [])
        assert result["achieved"] is False
        assert result["months_required"] is None

    @SETTINGS
    @given(
        target=pos_paise,
        surplus=pos_paise,
        months=st.integers(min_value=1, max_value=24),
    )
    def test_projection_months_monotone_with_surplus(
        self, target: int, surplus: int, months: int
    ) -> None:
        # Larger per-month surplus should never require MORE months.
        forecast_small = [{"month": f"m{i}", "expected_surplus_paise": surplus} for i in range(months)]
        forecast_big = [{"month": f"m{i}", "expected_surplus_paise": surplus * 2} for i in range(months)]
        small = calculate_goal_projection(target, 0, forecast_small)
        big = calculate_goal_projection(target, 0, forecast_big)
        if big["achieved"] and small["achieved"]:
            assert big["months_required"] <= small["months_required"]


class TestDebtPayoffProperties:
    @SETTINGS
    @given(outstanding=pos_paise, payment=pos_paise)
    def test_payoff_months_consistent(self, outstanding: int, payment: int) -> None:
        loans = [{"id": 1, "outstanding_paise": outstanding, "interest_rate_bps": 1200}]
        result = calculate_debt_payoff_projection(loans, [], payment, allocation_ratio=Decimal("1.0"))
        if payment > 0:
            assert isinstance(result["estimated_months"], int)
            assert result["estimated_months"] >= 1

    @SETTINGS
    @given(outstanding=pos_paise, rate=rate_bps)
    def test_allocation_ratio_zero_never_finishes(self, outstanding: int, rate: int) -> None:
        loans = [{"id": 1, "outstanding_paise": outstanding, "interest_rate_bps": rate}]
        result = calculate_debt_payoff_projection(loans, [], 100_000, allocation_ratio=Decimal("0"))
        # Zero allocation -> never pays off.
        assert result["estimated_months"] is None

    @SETTINGS
    @given(
        rate_a=rate_bps,
        rate_b=rate_bps,
    )
    def test_avalanche_highest_rate_first(self, rate_a: int, rate_b: int) -> None:
        assume(rate_a != rate_b)
        loans = [
            {"id": "A", "outstanding_paise": 100_000, "interest_rate_bps": rate_a},
            {"id": "B", "outstanding_paise": 100_000, "interest_rate_bps": rate_b},
        ]
        result = calculate_debt_payoff_projection(loans, [], 50_000)
        first = result["payoff_order"][0]
        assert first["interest_rate_bps"] == max(rate_a, rate_b)


class TestRankStrategyProperties:
    @SETTINGS
    @given(rate=rate_bps, balance=pos_paise)
    def test_empty_strategy_never_crashes(self, rate: int, balance: int) -> None:
        debts = [{"id": "x", "interest_rate_bps": rate, "outstanding_paise": balance}]
        for strategy in ("avalanche", "snowball", "balanced", "bogus"):
            result = rank_debt_payoff_strategy(debts, strategy=strategy)
            assert len(result["priority_order"]) == 1

    @SETTINGS
    @given(balance=pos_paise)
    def test_rank_output_shape(self, balance: int) -> None:
        debts = [{"id": "x", "interest_rate_bps": 1000, "outstanding_paise": balance}]
        result = rank_debt_payoff_strategy(debts)
        entry = result["priority_order"][0]
        assert set(entry.keys()) == {
            "id",
            "type",
            "outstanding_paise",
            "interest_rate_bps",
            "minimum_payment_paise",
        }


class TestActionScoreProperties:
    @SETTINGS
    @given(
        rate=rate_bps,
        revolver=st.decimals(min_value=0, max_value=1, places=2),
    )
    def test_score_bounded_zero_one(self, rate: int, revolver: Decimal) -> None:
        assume(not revolver.is_nan() and not revolver.is_infinite())
        context = {"interest_rate_bps": rate, "credit_revolver_ratio": revolver}
        for action in (
            "pay_credit_card",
            "increase_emergency_fund",
            "increase_investment",
            "reduce_expenses",
        ):
            result = calculate_financial_action_score(action, context)
            assert Decimal("0") <= result["score"] <= Decimal("1")
            assert result["impact"] in ("high", "medium", "low")

    @SETTINGS
    @given(rate=rate_bps)
    def test_impact_consistent_with_score(self, rate: int) -> None:
        result = calculate_financial_action_score("reduce_expenses", {"interest_rate_bps": rate})
        if result["score"] >= Decimal("0.7"):
            assert result["impact"] == "high"
        elif result["score"] >= Decimal("0.4"):
            assert result["impact"] == "medium"
        else:
            assert result["impact"] == "low"


class TestCashAdvanceEntryProperties:
    @SETTINGS
    @given(
        liability=pos_paise,
        expense=paise,
        days=st.integers(min_value=0, max_value=365),
    )
    def test_rate_non_negative(self, liability: int, expense: int, days: int) -> None:
        event = {"id": 1, "liability_change_paise": liability, "expense_paise": expense}
        entry = derive_cash_advance_debt_entry(event, days)
        assert entry["interest_rate_bps"] >= 0
        assert entry["outstanding_paise"] == liability

    @SETTINGS
    @given(liability=pos_paise)
    def test_zero_fee_zero_rate(self, liability: int) -> None:
        event = {"id": 1, "liability_change_paise": liability, "expense_paise": 0}
        assert derive_cash_advance_debt_entry(event, 10)["interest_rate_bps"] == 0


class TestHighInterestSumProperties:
    @SETTINGS
    @given(amounts=st.lists(paise, min_size=0, max_size=5), rate=rate_bps)
    def test_only_high_interest_counted(self, amounts, rate: int) -> None:
        debts = [{"interest_rate_bps": rate, "outstanding_paise": a} for a in amounts]
        total = _sum_high_interest_debt(debts)
        if rate >= 1800:
            assert total == sum(amounts)
        else:
            assert total == 0
