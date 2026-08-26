"""Property-based tests for financial_intelligence: scenario & intelligence.

M9-C42.25 — meaningful behavioral properties binding scenario.py and
intelligence.py. Monetary values are integer paise.
"""

from __future__ import annotations

from decimal import Decimal

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from src.engines.financial_intelligence.intelligence import (
    _compute_health_score,
    _extract_liquidity_months,
    calculate_intelligence_confidence,
    generate_financial_priorities,
)
from src.engines.financial_intelligence.scenario import (
    compare_scenario,
    simulate_credit_behaviour_change,
    simulate_expense_reduction,
    simulate_income_change,
    simulate_new_loan,
)

SETTINGS = settings(max_examples=30, suppress_health_check=[HealthCheck.differing_executors])

pos_paise = st.integers(min_value=1, max_value=10_000_000)
months_st = st.integers(min_value=1, max_value=24)


class TestExpenseReductionProperties:
    @SETTINGS
    @given(reduction=pos_paise, months=months_st)
    def test_cumulative_is_savings_times_months(self, reduction: int, months: int) -> None:
        result = simulate_expense_reduction(100_000, reduction, [], forecast_months=months)
        assert result["cumulative_benefit_paise"] == reduction * months
        assert len(result["forecast"]) == months

    @SETTINGS
    @given(base=pos_paise, reduction=pos_paise)
    def test_each_month_improved_by_savings(self, base: int, reduction: int) -> None:
        forecast = [{"expected_surplus_paise": base}]
        result = simulate_expense_reduction(100_000, reduction, forecast, forecast_months=1)
        assert result["forecast"][0]["projected_surplus_paise"] == base + reduction


class TestIncomeChangeProperties:
    @SETTINGS
    @given(change=st.integers(min_value=-5_000_000, max_value=5_000_000), months=months_st)
    def test_cumulative_is_change_times_months(self, change: int, months: int) -> None:
        result = simulate_income_change(100_000, change, [], forecast_months=months)
        assert result["cumulative_income_change_paise"] == change * months

    @SETTINGS
    @given(base=pos_paise, change=st.integers(min_value=-5_000_000, max_value=5_000_000))
    def test_revised_surplus_shifted(self, base: int, change: int) -> None:
        forecast = [{"expected_surplus_paise": base}]
        result = simulate_income_change(100_000, change, forecast, forecast_months=1)
        assert result["revised_surplus_forecast"][0]["expected_surplus_paise"] == base + change


class TestNewLoanProperties:
    @SETTINGS
    @given(
        principal=st.integers(min_value=100_000, max_value=10_000_000),
        rate=st.integers(min_value=0, max_value=3600),
        tenure=st.integers(min_value=1, max_value=240),
        surplus=pos_paise,
    )
    def test_affordability_consistent_with_foir(
        self, principal: int, rate: int, tenure: int, surplus: int
    ) -> None:
        result = simulate_new_loan(principal, rate, tenure, surplus)
        assert result["monthly_emi_paise"] >= 0
        foir = result["foir"]
        if foir < Decimal("0.40"):
            assert result["affordability"] == "safe"
        elif foir <= Decimal("0.60"):
            assert result["affordability"] == "warning"
        else:
            assert result["affordability"] == "unsafe"

    @SETTINGS
    @given(
        principal=st.integers(min_value=100_000, max_value=10_000_000),
        tenure=st.integers(min_value=1, max_value=240),
    )
    def test_zero_rate_emi_is_principal_over_tenure(self, principal: int, tenure: int) -> None:
        result = simulate_new_loan(principal, 0, tenure, 1_000_000)
        assert result["monthly_emi_paise"] == principal // tenure


class TestCreditBehaviourProperties:
    @SETTINGS
    @given(
        dependency=st.decimals(min_value=0, max_value=1, places=2),
        revolver=st.decimals(min_value=0, max_value=1, places=2),
    )
    def test_projection_never_exceeds_current(self, dependency: Decimal, revolver: Decimal) -> None:
        assume(not dependency.is_nan() and not revolver.is_nan())
        result = simulate_credit_behaviour_change(
            dependency, revolver, average_interest_rate_bps=1200
        )
        assert result["projected_dependency_ratio"] <= dependency

    @SETTINGS
    @given(dependency=st.decimals(min_value=0, max_value=1, places=2))
    def test_zero_revolver_is_unchanged(self, dependency: Decimal) -> None:
        assume(not dependency.is_nan())
        result = simulate_credit_behaviour_change(dependency, Decimal("0"))
        assert result["risk_change"] == "unchanged"
        assert result["projected_dependency_ratio"] == dependency


class TestCompareScenarioProperties:
    @SETTINGS
    @given(base=pos_paise, scenario=pos_paise)
    def test_delta_is_scenario_minus_baseline(self, base: int, scenario: int) -> None:
        result = compare_scenario(
            {"monthly_surplus_paise": base}, {"monthly_surplus_paise": scenario}
        )
        assert result["delta"]["monthly_surplus_paise"] == scenario - base

    @SETTINGS
    @given(value=pos_paise)
    def test_identical_inputs_no_messages(self, value: int) -> None:
        same = {"monthly_surplus_paise": value, "cumulative_benefit_paise": value}
        result = compare_scenario(same, dict(same))
        assert result["improvements"] == []
        assert result["risks"] == []
        assert all(v == 0 for v in result["delta"].values())


class TestIntelligenceConfidenceProperties:
    @SETTINGS
    @given(
        months=st.integers(min_value=0, max_value=24),
        completeness=st.decimals(min_value=0, max_value=1, places=2),
        coverage=st.decimals(min_value=0, max_value=1, places=2),
    )
    def test_confidence_bounded_with_quality_band(
        self, months: int, completeness: Decimal, coverage: Decimal
    ) -> None:
        assume(not completeness.is_nan() and not coverage.is_nan())
        result = calculate_intelligence_confidence(months, completeness, coverage, Decimal("0"))
        assert Decimal("0") <= result["confidence"] <= Decimal("1")
        assert result["data_quality"] in ("excellent", "good", "fair", "poor")

    @SETTINGS
    @given(months=st.integers(min_value=3, max_value=100))
    def test_months_score_caps_at_three(self, months: int) -> None:
        capped = calculate_intelligence_confidence(months, Decimal("1"), Decimal("1"), Decimal("0"))
        assert capped["confidence"] == Decimal("1")


class TestPrioritiesProperties:
    @SETTINGS
    @given(n_actions=st.integers(min_value=0, max_value=8))
    def test_priorities_capped_and_ranked(self, n_actions: int) -> None:
        actions = [{"action": f"act_{i}"} for i in range(n_actions)]
        result = generate_financial_priorities(
            {"recommended_actions": actions},
            {},
            {"projected_min_balance_paise": 10_000_000},
            [],
        )
        assert len(result) <= 5
        assert [p["rank"] for p in result] == list(range(1, len(result) + 1))

    @SETTINGS
    @given(min_balance=pos_paise)
    def test_emergency_injection_threshold(self, min_balance: int) -> None:
        result = generate_financial_priorities(
            {"recommended_actions": []},
            {},
            {"projected_min_balance_paise": min_balance},
            [],
        )
        months = min_balance // 100_000
        if months < 3:
            assert result[0]["action"] == "increase_emergency_fund"
            if months < 1:
                assert result[0]["impact"] == "high"
            else:
                assert result[0]["impact"] == "medium"
        else:
            assert result == []


class TestHealthScoreProperties:
    @SETTINGS
    @given(
        debt_cycle=st.integers(min_value=0, max_value=100),
        revolver=st.decimals(min_value=0, max_value=1, places=2),
    )
    def test_health_score_bounded(self, debt_cycle: int, revolver: Decimal) -> None:
        assume(not revolver.is_nan())
        result = _compute_health_score(
            {
                "debt_cycle_score": debt_cycle or 1,
                "credit_revolver_ratio": revolver,
                "cashflow_stability": Decimal("0.5"),
            }
        )
        assert Decimal("0") <= result <= Decimal("100")

    @SETTINGS
    @given(min_balance=st.integers(min_value=-10_000_000, max_value=10_000_000))
    def test_liquidity_months_non_negative(self, min_balance: int) -> None:
        assert _extract_liquidity_months({"projected_min_balance_paise": min_balance}) >= 0
