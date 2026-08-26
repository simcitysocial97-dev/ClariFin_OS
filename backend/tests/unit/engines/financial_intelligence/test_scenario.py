"""Direct unit tests for src/engines/financial_intelligence/scenario.py.

M9-C42.25 — direct behavioral ownership of scenario simulations: expense
reduction, income change, debt prepayment, new loan affordability, credit
behaviour change, and baseline-vs-scenario comparison.

Anomaly FIN-E1 (see C42.25 inventory): compare_scenario's foir risk branch
contains an impossible range condition, so any negative foir change appends
'FOIR increased above safe threshold'. Current behavior pinned intentionally.
"""

from decimal import Decimal

from src.engines.financial_intelligence.scenario import (
    compare_scenario,
    simulate_credit_behaviour_change,
    simulate_debt_prepayment,
    simulate_expense_reduction,
    simulate_income_change,
    simulate_new_loan,
)

# ============================================================
# simulate_expense_reduction
# ============================================================


def test_expense_reduction_savings_and_cumulative():
    base = [{"expected_surplus_paise": 10_000} for _ in range(3)]
    result = simulate_expense_reduction(100_000, 50_000, base, forecast_months=3)
    assert result["monthly_savings_created_paise"] == 50_000
    assert result["projected_surplus_change_paise"] == 50_000
    assert result["cumulative_benefit_paise"] == 150_000
    assert len(result["forecast"]) == 3


def test_expense_reduction_improves_each_month():
    base = [{"expected_surplus_paise": 10_000}, {"expected_surplus_paise": 20_000}]
    result = simulate_expense_reduction(100_000, 5_000, base, forecast_months=2)
    assert result["forecast"][0]["projected_surplus_paise"] == 15_000
    assert result["forecast"][1]["projected_surplus_paise"] == 25_000


def test_expense_reduction_months_start_at_2026_08():
    result = simulate_expense_reduction(100_000, 1_000, [], forecast_months=1)
    assert result["forecast"][0]["month"] == "2026-08"


def test_expense_reduction_forecast_shorter_than_horizon_pads_zero():
    base = [{"expected_surplus_paise": 7_000}]
    result = simulate_expense_reduction(100_000, 1_000, base, forecast_months=2)
    assert result["forecast"][1]["projected_surplus_paise"] == 1_000


# ============================================================
# simulate_income_change
# ============================================================


def test_income_change_increase_cumulative():
    base = [{"expected_surplus_paise": 10_000}]
    result = simulate_income_change(100_000, 20_000, base, forecast_months=12)
    assert result["income_change_paise"] == 20_000
    assert result["cumulative_income_change_paise"] == 240_000
    assert len(result["revised_surplus_forecast"]) == 12
    assert result["revised_surplus_forecast"][0]["expected_surplus_paise"] == 30_000


def test_income_change_decrease_allowed():
    base = [{"expected_surplus_paise": 50_000}]
    result = simulate_income_change(100_000, -30_000, base, forecast_months=1)
    assert result["income_change_paise"] == -30_000
    assert result["cumulative_income_change_paise"] == -30_000
    assert result["revised_surplus_forecast"][0]["expected_surplus_paise"] == 20_000


def test_income_change_pads_missing_base():
    result = simulate_income_change(100_000, 5_000, [], forecast_months=2)
    assert result["revised_surplus_forecast"][0]["expected_surplus_paise"] == 5_000


# ============================================================
# simulate_debt_prepayment
# ============================================================

LOANS_12PCT = [{"outstanding_paise": 1_200_000, "interest_rate_bps": 1200}]


def test_debt_prepayment_saves_months():
    result = simulate_debt_prepayment(LOANS_12PCT, extra_payment_paise=50_000, monthly_surplus_paise=100_000)
    # Baseline: 50_000/month -> 24 months; revised 75_000 -> 16 months.
    assert result["estimated_months_saved"] == 8
    assert result["interest_saved_paise"] == 96_000
    assert result["revised_payoff_projection"]


def test_debt_prepayment_zero_extra_no_savings():
    result = simulate_debt_prepayment(LOANS_12PCT, extra_payment_paise=0, monthly_surplus_paise=100_000)
    assert result["estimated_months_saved"] == 0
    assert result["interest_saved_paise"] == 0


def test_debt_prepayment_empty_debts_safe():
    result = simulate_debt_prepayment([], extra_payment_paise=10_000, monthly_surplus_paise=50_000)
    assert result["estimated_months_saved"] == 0
    assert result["interest_saved_paise"] == 0
    assert result["revised_payoff_projection"] == []


def test_debt_prepayment_multiple_loans_average_rate():
    loans = [
        {"outstanding_paise": 100_000, "interest_rate_bps": 1200},
        {"outstanding_paise": 100_000, "interest_rate_bps": 2400},
    ]
    result = simulate_debt_prepayment(loans, extra_payment_paise=50_000, monthly_surplus_paise=50_000)
    # Baseline allocation 25_000: 4+4 = 8 months; revised 75_000: 2+2 = 4 -> 4 saved.
    assert result["estimated_months_saved"] == 4
    # avg_rate = (1200+2400)/2 = 1800 -> int(18) -> 200_000*18//100 = 36_000
    # annual interest 36_000; monthly 3_000 * 4 = 12_000
    assert result["interest_saved_paise"] == 12_000


# ============================================================
# simulate_new_loan
# ============================================================


def test_new_loan_emi_matches_loan_engine():
    result = simulate_new_loan(1_000_000, 1200, 12, 500_000)
    assert result["monthly_emi_paise"] == 88_849
    assert result["surplus_impact_paise"] == result["monthly_emi_paise"]


def test_new_loan_foir_safe():
    result = simulate_new_loan(1_000_000, 1200, 12, 500_000)
    # 88_849 / 500_000 ~= 0.1777 < 0.40
    assert result["affordability"] == "safe"
    assert result["foir"] == Decimal("88849") / Decimal("500000")


def test_new_loan_zero_surplus_foir_one_unsafe():
    result = simulate_new_loan(1_000_000, 1200, 12, 0)
    assert result["foir"] == Decimal("1.0")
    assert result["affordability"] == "unsafe"


def test_new_loan_foir_exactly_safe_boundary_is_warning():
    # Zero-rate loan: EMI = principal // tenure = exactly 100_000.
    result = simulate_new_loan(1_000_000, 0, 10, 250_000)
    assert result["monthly_emi_paise"] == 100_000
    assert result["foir"] == Decimal("0.4")
    assert result["affordability"] == "warning"


def test_new_loan_foir_one_below_safe_boundary_is_safe():
    result = simulate_new_loan(1_000_000, 0, 10, 250_001)
    assert result["affordability"] == "safe"


def test_new_loan_foir_warning_band():
    result = simulate_new_loan(1_000_000, 1200, 12, 177_698)
    # 88_849 / 177_698 ~= 0.5 -> warning band (0.40, 0.60]
    assert result["affordability"] == "warning"


def test_new_loan_foir_warning_upper_boundary_is_unsafe():
    result = simulate_new_loan(1_000_000, 0, 10, 166_666)
    # foir = 100_000/166_666 = 0.600003... > 0.60 -> unsafe
    assert result["affordability"] == "unsafe"


# ============================================================
# simulate_credit_behaviour_change
# ============================================================


def test_credit_behaviour_zero_revolver_unchanged():
    result = simulate_credit_behaviour_change(Decimal("0.5"), Decimal("0"))
    assert result["projected_dependency_ratio"] == Decimal("0.5")
    assert result["interest_saved_paise"] == 0
    assert result["risk_change"] == "unchanged"
    assert result["requires_rate_input"] is False


def test_credit_behaviour_without_rate_requires_input():
    result = simulate_credit_behaviour_change(Decimal("0.5"), Decimal("0.5"))
    assert result["requires_rate_input"] is True
    assert result["interest_saved_paise"] is None
    assert result["risk_change"] == "improved"
    assert result["projected_dependency_ratio"] == Decimal("0.5")


def test_credit_behaviour_with_rate_improves_ratio():
    result = simulate_credit_behaviour_change(
        Decimal("0.5"), Decimal("0.5"), average_interest_rate_bps=3600
    )
    # improvement factor = 1 - 0.5*0.8 = 0.6 -> 0.3
    assert result["projected_dependency_ratio"] == Decimal("0.5") * Decimal("0.6")
    assert result["risk_change"] == "improved"
    assert result["requires_rate_input"] is False


def test_credit_behaviour_full_revolver_floor():
    result = simulate_credit_behaviour_change(
        Decimal("0.8"), Decimal("1.0"), average_interest_rate_bps=1200
    )
    # factor = 1 - 0.8 = 0.2 -> 0.16
    assert result["projected_dependency_ratio"] == Decimal("0.8") * Decimal("0.2")


# ============================================================
# compare_scenario
# ============================================================


def test_compare_surplus_increase_is_improvement():
    baseline = {"monthly_surplus_paise": 100_000}
    scenario = {"monthly_surplus_paise": 150_000}
    result = compare_scenario(baseline, scenario)
    assert result["delta"]["monthly_surplus_paise"] == 50_000
    assert "Monthly surplus increased by ₹500" in result["improvements"]
    assert result["risks"] == []


def test_compare_surplus_decrease_is_risk():
    result = compare_scenario(
        {"monthly_surplus_paise": 100_000}, {"monthly_surplus_paise": 40_000}
    )
    assert result["delta"]["monthly_surplus_paise"] == -60_000
    assert "Monthly surplus decreased by ₹600" in result["risks"]


def test_compare_cumulative_benefit_improvement():
    result = compare_scenario(
        {"cumulative_benefit_paise": 0}, {"cumulative_benefit_paise": 100_000}
    )
    assert "Cumulative benefit increased by ₹1000" in result["improvements"]


def test_compare_interest_savings_improvement():
    result = compare_scenario(
        {"interest_saved_paise": 0}, {"interest_saved_paise": 200_000}
    )
    assert "Interest savings projected at ₹2000" in result["improvements"]


def test_compare_foir_increase_flagged():
    result = compare_scenario({"foir": Decimal("0.3")}, {"foir": Decimal("0.5")})
    assert result["delta"]["foir"] > 0
    assert "FOIR improved below safe threshold" in result["improvements"]


def test_compare_foir_decrease_risk_pinned_anomaly_fin_e1():
    # FIN-E1: impossible range condition -> every negative foir change adds a
    # risk message, even though a lower FOIR is an improvement.
    result = compare_scenario({"foir": Decimal("0.5")}, {"foir": Decimal("0.3")})
    assert result["delta"]["foir"] < 0
    assert "FOIR increased above safe threshold" in result["risks"]


def test_compare_missing_values_skipped():
    result = compare_scenario({"monthly_surplus_paise": None}, {"monthly_surplus_paise": 5})
    assert result["delta"] == {}
    assert result["improvements"] == []
    assert result["risks"] == []


def test_compare_decimal_values_coerced():
    result = compare_scenario(
        {"monthly_surplus_paise": Decimal("100")}, {"monthly_surplus_paise": Decimal("150")}
    )
    assert result["delta"]["monthly_surplus_paise"] == 50


def test_compare_unlisted_metrics_ignored():
    result = compare_scenario({"custom_metric": 1}, {"custom_metric": 2})
    assert result["delta"] == {}


def test_compare_months_metric_delta_recorded_without_message():
    result = compare_scenario(
        {"months_to_debt_free": 24}, {"months_to_debt_free": 14}
    )
    assert result["delta"]["months_to_debt_free"] == -10
    assert result["improvements"] == []
    assert result["risks"] == []
