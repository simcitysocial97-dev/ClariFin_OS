"""
Consolidated Behaviour Engine Metrics Tests
============================================

Merges tests from:
- test_behaviour_engine_metrics.py  (savings, cashflow stability, resilience, lifestyle, edge cases, determinism)
- test_behaviour_engine_account.py  (account concentration, idle cash, balance volatility, low balance risk)
- test_behaviour_engine_debt.py  (credit dependency, debt cycle, FOIR, revolver ratio, determinism)
- test_behaviour_engine_income.py  (income classification, salary dependence, diversification, true income)

All monetary values are integers in paise (₹1.00 = 100 paise).
"""

from decimal import Decimal
from typing import Any

import pytest

from src.engines.behaviour_engine import (
    classify_income_source,
    compute_account_concentration,
    compute_borrowed_lifestyle_ratio,
    compute_cashflow_stability_index,
    compute_credit_dependency_ratio,
    compute_credit_revolver_ratio,
    compute_debt_cycle_score,
    compute_expense_stability,
    compute_foir,
    compute_idle_cash_amount,
    compute_income_diversification_score,
    compute_income_stability,
    compute_lifestyle_creep_index,
    compute_lifestyle_inflation,
    compute_liquidity_months,
    compute_monthly_surplus,
    compute_resilience_index,
    compute_salary_dependence_ratio,
    compute_true_income_total,
    compute_true_savings_rate,
    detect_balance_volatility,
    detect_low_balance_risk,
    filter_true_income,
)

# ============================================================
# Test Fixtures
# ============================================================


@pytest.fixture
def sample_monthly_incomes() -> list[int]:
    """Sample monthly income data in paise (5 months, stable)."""
    return [5000000, 5000000, 5100000, 5000000, 5000000]  # ₹5L, ₹5L, ₹5.1L, ₹5L, ₹5L


@pytest.fixture
def volatile_monthly_incomes() -> list[int]:
    """Volatile monthly income data in paise."""
    return [3000000, 8000000, 2000000, 9000000, 10000000]  # Variable: ₹3L to ₹10L


@pytest.fixture
def sample_monthly_expenses() -> list[int]:
    """Sample monthly expense data in paise (5 months, stable)."""
    return [4000000, 4100000, 3900000, 4000000, 4200000]  # ₹4L range


@pytest.fixture
def salary_transactions() -> list[dict[str, Any]]:
    """Sample salary income transactions."""
    return [
        {"description": "Salary credit", "amount_paise": 5000000},
        {"description": "PAYROLL transfer", "amount_paise": 4500000},
        {"description": "Professional fees - salaried", "amount_paise": 500000},
    ]


@pytest.fixture
def diversified_transactions() -> list[dict[str, Any]]:
    """Sample diversified income transactions (salary + investment)."""
    return [
        {"description": "Salary credit", "amount_paise": 5000000},
        {"description": "Dividend from stocks", "amount_paise": 100000},
        {"description": "Mutual fund interest", "amount_paise": 50000},
    ]


@pytest.fixture
def mixed_transactions() -> list[dict[str, Any]]:
    """Mixed income transactions including non-true income."""
    return [
        {"description": "Salary credit", "amount_paise": 5000000},
        {"description": "Transfer to own account", "amount_paise": 100000},
        {"description": "Loan from bank", "amount_paise": 500000},
        {"description": "Refund from Amazon", "amount_paise": 2000},
        {"description": "Business consulting income", "amount_paise": 200000},
        {
            "description": "Dividend from stocks",
            "amount_paise": 50000,
        },  # Added investment
    ]


# ============================================================
# Savings Metrics Tests (from test_behaviour_engine_metrics.py)
# ============================================================


class TestSavingsMetrics:
    """Tests for savings-related metrics."""

    # --- compute_true_savings_rate ---

    def test_true_savings_rate_positive(self):
        """Test positive savings rate with valid inputs."""
        # Income: ₹5L, Expenses: ₹4L, Fees: ₹10K
        result = compute_true_savings_rate(5000000, 4000000, 100000)
        # (5000000 - 4000000 - 100000) / 5000000 = 0.18
        assert result == Decimal("0.18")

    def test_true_savings_rate_zero_income(self):
        """Test savings rate with zero income returns 0."""
        result = compute_true_savings_rate(0, 100000, 50000)
        assert result == Decimal("0")

    def test_true_savings_rate_negative(self):
        """Test negative savings rate (overspending)."""
        # Income: ₹3L, Expenses: ₹4L, Fees: ₹50K = deficit
        result = compute_true_savings_rate(3000000, 4000000, 50000)
        # (3000000 - 4000000 - 50000) / 3000000 = -0.35
        assert result == Decimal("-0.35")

    def test_true_savings_rate_perfect_savings(self):
        """Test zero expenses and zero fees."""
        result = compute_true_savings_rate(5000000, 0, 0)
        assert result == Decimal("1")

    def test_true_savings_rate_zero_fees(self):
        """Test with zero fees."""
        result = compute_true_savings_rate(5000000, 4000000, 0)
        assert result == Decimal("0.2")

    def test_true_savings_rate_deterministic(self):
        """Test that same inputs produce same outputs."""
        result1 = compute_true_savings_rate(5000000, 4000000, 100000)
        result2 = compute_true_savings_rate(5000000, 4000000, 100000)
        assert result1 == result2

    # --- compute_borrowed_lifestyle_ratio ---

    def test_borrowed_lifestyle_ratio_normal(self):
        """Test normal ratio calculation."""
        result = compute_borrowed_lifestyle_ratio(2000000, 4000000)
        # 2000000 / 4000000 = 0.5
        assert result == Decimal("0.5")

    def test_borrowed_lifestyle_ratio_zero_expenses(self):
        """Test ratio with zero expenses returns 0."""
        result = compute_borrowed_lifestyle_ratio(1000000, 0)
        assert result == Decimal("0")

    def test_borrowed_lifestyle_ratio_all_credit_funded(self):
        """Test when all expenses are credit-funded."""
        result = compute_borrowed_lifestyle_ratio(5000000, 5000000)
        assert result == Decimal("1")

    def test_borrowed_lifestyle_ratio_credit_exceeds_expenses(self):
        """Test when credit funding exceeds reported expenses."""
        result = compute_borrowed_lifestyle_ratio(6000000, 5000000)
        # Ratio > 1 indicates unusual pattern
        assert result == Decimal("1.2")

    def test_borrowed_lifestyle_ratio_deterministic(self):
        """Test determinism of ratio calculation."""
        result1 = compute_borrowed_lifestyle_ratio(2000000, 4000000)
        result2 = compute_borrowed_lifestyle_ratio(2000000, 4000000)
        assert result1 == result2

    # --- compute_monthly_surplus ---

    def test_monthly_surplus_positive(self):
        """Test positive surplus."""
        result = compute_monthly_surplus(5000000, 4000000, 100000)
        assert result == 900000  # ₹90K surplus

    def test_monthly_surplus_negative(self):
        """Test negative surplus (deficit)."""
        result = compute_monthly_surplus(3000000, 4000000, 100000)
        assert result == -1100000  # ₹1.1L deficit

    def test_monthly_surplus_zero_fees(self):
        """Test surplus with no fees."""
        result = compute_monthly_surplus(5000000, 4000000, 0)
        assert result == 1000000

    def test_monthly_surplus_zero_income(self):
        """Test surplus with zero income."""
        result = compute_monthly_surplus(0, 100000, 50000)
        assert result == -150000


# ============================================================
# Cashflow Stability Tests (from test_behaviour_engine_metrics.py)
# ============================================================


class TestCashflowStability:
    """Tests for cashflow-related stability metrics."""

    # --- compute_income_stability ---

    def test_income_stability_stable(self, sample_monthly_incomes):
        """Test stable income returns high stability score."""
        result = compute_income_stability(sample_monthly_incomes)
        # Should be close to 1 for stable income
        assert Decimal("0.7") < result <= Decimal("1")

    def test_income_stability_volatile(self, volatile_monthly_incomes):
        """Test volatile income returns lower stability score."""
        result = compute_income_stability(volatile_monthly_incomes)
        # Should be lower for volatile income
        assert result < Decimal("0.5")

    def test_income_stability_single_month(self):
        """Test single month returns 1 (assumed stable)."""
        result = compute_income_stability([5000000])
        assert result == Decimal("1")

    def test_income_stability_empty(self):
        """Test empty list returns 1 (assumed stable)."""
        result = compute_income_stability([])
        assert result == Decimal("1")

    def test_income_stability_deterministic(self):
        """Test determinism of income stability."""
        data = [5000000, 5100000, 5000000, 4900000, 5000000]
        result1 = compute_income_stability(data)
        result2 = compute_income_stability(data)
        assert result1 == result2

    # --- compute_expense_stability ---

    def test_expense_stability_stable(self, sample_monthly_expenses):
        """Test stable expenses return high stability score."""
        result = compute_expense_stability(sample_monthly_expenses)
        assert Decimal("0.5") < result <= Decimal("1")

    def test_expense_stability_constant(self):
        """Test constant expenses return 1."""
        result = compute_expense_stability([4000000, 4000000, 4000000])
        assert result == Decimal("1")

    def test_expense_stability_single_month(self):
        """Test single month returns 1."""
        result = compute_expense_stability([4000000])
        assert result == Decimal("1")

    def test_expense_stability_empty(self):
        """Test empty list returns 1."""
        result = compute_expense_stability([])
        assert result == Decimal("1")

    # --- compute_cashflow_stability_index ---

    def test_cashflow_stability_index_averages(self):
        """Test that cashflow index averages income and expense stability."""
        # Income = [5M, 5M, 5M] -> stability = 1
        # Expenses = [4M, 5M, 6M] -> some variance
        result = compute_cashflow_stability_index(
            [5000000, 5000000, 5000000], [4000000, 5000000, 6000000]
        )
        # Should be between 0.5 and 1
        assert Decimal("0.5") < result <= Decimal("1")

    def test_cashflow_stability_index_both_stable(self):
        """Test index when both income and expenses are stable."""
        incomes = [5000000, 5000000, 5000000, 5000000]
        expenses = [4000000, 4000000, 4000000, 4000000]
        result = compute_cashflow_stability_index(incomes, expenses)
        assert result == Decimal("1")

    def test_cashflow_stability_index_deterministic(self):
        """Test determinism of cashflow index."""
        incomes = [5000000, 5000000, 5100000]
        expenses = [4000000, 4100000, 4000000]
        result1 = compute_cashflow_stability_index(incomes, expenses)
        result2 = compute_cashflow_stability_index(incomes, expenses)
        assert result1 == result2


# ============================================================
# Resilience Tests (from test_behaviour_engine_metrics.py)
# ============================================================


class TestResilienceMetrics:
    """Tests for resilience-related metrics."""

    # --- compute_liquidity_months ---

    def test_liquidity_months_normal(self):
        """Test normal liquidity calculation."""
        # Liquid: ₹6L, Essential monthly: ₹5L -> 1 month
        result = compute_liquidity_months(6000000, 5000000)
        assert result == 1

    def test_liquidity_months_multiple(self):
        """Test multiple months of liquidity."""
        # Liquid: ₹24L, Essential monthly: ₹2L -> 12 months
        result = compute_liquidity_months(24000000, 2000000)
        assert result == 12

    def test_liquidity_months_zero_essential(self):
        """Test zero essential expenses returns 999 (infinite coverage)."""
        result = compute_liquidity_months(6000000, 0)
        assert result == 999

    def test_liquidity_months_zero_liquid(self):
        """Test zero liquid assets with positive expenses returns 0."""
        result = compute_liquidity_months(0, 2000000)
        assert result == 0

    def test_liquidity_months_partial_month(self):
        """Test partial month returns floor value."""
        # Liquid: ₹3L, Essential monthly: ₹2L -> 1 month (floor)
        result = compute_liquidity_months(3000000, 2000000)
        assert result == 1

    # --- compute_resilience_index ---

    def test_resilience_index_high(self):
        """Test high resilience with good liquidity and stable income."""
        result = compute_resilience_index(
            liquid_assets_paise=12000000,  # ₹12L = 12 months
            essential_monthly_expenses_paise=1000000,  # ₹10L/month
            total_income_paise=5000000,
            monthly_incomes_paise=[5000000, 5000000, 5000000],
        )
        # Liquidity = 1.0, Income stability = 1.0
        # Result = 0.6 * 1.0 + 0.4 * 1.0 = 1.0
        assert result == Decimal("1")

    def test_resilience_index_low_liquidity(self):
        """Test low resilience with poor liquidity."""
        result = compute_resilience_index(
            liquid_assets_paise=0,
            essential_monthly_expenses_paise=2000000,
            total_income_paise=5000000,
            monthly_incomes_paise=[5000000, 5000000, 5000000],
        )
        # Liquidity = 0, Income stability = 1.0
        # Result = 0.6 * 0 + 0.4 * 1.0 = 0.4
        assert result == Decimal("0.4")

    def test_resilience_index_capped_liquidity(self):
        """Test that liquidity is capped at 12 months."""
        result = compute_resilience_index(
            liquid_assets_paise=1000000000,  # ₹10M (>12 months)
            essential_monthly_expenses_paise=2000000,
            total_income_paise=5000000,
            monthly_incomes_paise=[5000000, 5000000, 5000000],
        )
        # Liquidity capped at 12, stability = 1.0
        # Result = 0.6 * 1.0 + 0.4 * 1.0 = 1.0
        assert result == Decimal("1")

    def test_resilience_index_volatile_income(self):
        """Test resilience with volatile income."""
        result = compute_resilience_index(
            liquid_assets_paise=6000000,
            essential_monthly_expenses_paise=1000000,
            total_income_paise=5000000,
            monthly_incomes_paise=[3000000, 8000000, 2000000],
        )
        # Liquidity = 6 months = 0.5, Income stability < 1
        assert Decimal("0.2") < result < Decimal("1")


# ============================================================
# Lifestyle Tests (from test_behaviour_engine_metrics.py)
# ============================================================


class TestLifestyleMetrics:
    """Tests for lifestyle-related metrics."""

    # --- compute_lifestyle_inflation ---

    def test_lifestyle_inflation_positive(self):
        """Test positive lifestyle inflation."""
        result = compute_lifestyle_inflation(6000000, 4000000)
        # (6M - 4M) / 4M = 0.5
        assert result == Decimal("0.5")

    def test_lifestyle_inflation_zero(self):
        """Test zero inflation (same spending)."""
        result = compute_lifestyle_inflation(4000000, 4000000)
        assert result == Decimal("0")

    def test_lifestyle_inflation_decrease(self):
        """Test negative inflation (reduced spending)."""
        result = compute_lifestyle_inflation(3000000, 4000000)
        # (3M - 4M) / 4M = -0.25
        assert result == Decimal("-0.25")

    def test_lifestyle_inflation_zero_previous(self):
        """Test with zero previous spending."""
        result = compute_lifestyle_inflation(500000, 0)
        assert result == Decimal("0")

    def test_lifestyle_inflation_zero_current(self):
        """Test with zero current spending."""
        result = compute_lifestyle_inflation(0, 4000000)
        assert result == Decimal("-1")

    def test_lifestyle_inflation_deterministic(self):
        """Test determinism of inflation calculation."""
        result1 = compute_lifestyle_inflation(6000000, 4000000)
        result2 = compute_lifestyle_inflation(6000000, 4000000)
        assert result1 == result2

    # --- compute_lifestyle_creep_index ---

    def test_lifestyle_creep_index_positive(self):
        """Test positive creep over months."""
        # Spending grew from 2L to 4L over months
        result = compute_lifestyle_creep_index(
            [2000000, 2500000, 3000000, 3500000, 4000000]
        )
        # (4M - 2M) / 2M = 1.0
        assert result == Decimal("1")

    def test_lifestyle_creep_index_negative(self):
        """Test negative creep (decreasing spending)."""
        result = compute_lifestyle_creep_index(
            [4000000, 3500000, 3000000, 2500000, 2000000]
        )
        # (2M - 4M) / 4M = -0.5
        assert result == Decimal("-0.5")

    def test_lifestyle_creep_index_single_month(self):
        """Test single month returns 0 (no trend)."""
        result = compute_lifestyle_creep_index([3000000])
        assert result == Decimal("0")

    def test_lifestyle_creep_index_empty(self):
        """Test empty list returns 0."""
        result = compute_lifestyle_creep_index([])
        assert result == Decimal("0")

    def test_lifestyle_creep_index_zero_earliest(self):
        """Test with zero earliest value."""
        result = compute_lifestyle_creep_index([0, 1000000, 2000000])
        assert result == Decimal("0")

    def test_lifestyle_creep_index_deterministic(self):
        """Test determinism of creep index."""
        data = [2000000, 2500000, 3000000, 3500000, 4000000]
        result1 = compute_lifestyle_creep_index(data)
        result2 = compute_lifestyle_creep_index(data)
        assert result1 == result2


# ============================================================
# Edge Cases and Boundary Conditions (from test_behaviour_engine_metrics.py)
# ============================================================


class TestMetricsEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_all_zero_inputs_savings(self):
        """Test all zeros in savings calculations."""
        assert compute_true_savings_rate(0, 0, 0) == Decimal("0")
        assert compute_borrowed_lifestyle_ratio(0, 0) == Decimal("0")
        assert compute_monthly_surplus(0, 0, 0) == 0

    def test_large_values(self):
        """Test with large monetary values."""
        # ₹10Cr income, ₹8Cr expenses
        result = compute_true_savings_rate(1000000000, 800000000, 10000000)
        assert result == Decimal("0.19")

    def test_missing_months_handling(self):
        """Test that functions work with whatever data is provided."""
        # Only passing 3 months instead of 5
        partial_incomes = [5000000, 5000000, 5000000]
        partial_expenses = [4000000, 4000000, 4000000]

        result = compute_cashflow_stability_index(partial_incomes, partial_expenses)
        assert result == Decimal("1")  # All equal = stable

    def test_negative_values_savings(self):
        """Test negative values in savings metrics."""
        # Negative expenses shouldn't happen in real data, but test robustness
        result = compute_monthly_surplus(5000000, -100000, 0)
        assert result == 5100000  # ₹5.1L


# ============================================================
# Determinism Tests (from test_behaviour_engine_metrics.py)
# ============================================================


class TestMetricsDeterminism:
    """Verify all functions are deterministic."""

    def test_all_savings_deterministic(self):
        """Test all savings functions produce same output for same input."""
        inputs = {
            "income": 5000000,
            "expenses": 4000000,
            "fees": 100000,
            "credit_funded": 2000000,
        }

        # Run each function twice
        r1 = compute_true_savings_rate(
            inputs["income"], inputs["expenses"], inputs["fees"]
        )
        r2 = compute_true_savings_rate(
            inputs["income"], inputs["expenses"], inputs["fees"]
        )
        assert r1 == r2

        r1 = compute_borrowed_lifestyle_ratio(
            inputs["credit_funded"], inputs["expenses"]
        )
        r2 = compute_borrowed_lifestyle_ratio(
            inputs["credit_funded"], inputs["expenses"]
        )
        assert r1 == r2

        r1 = compute_monthly_surplus(
            inputs["income"], inputs["expenses"], inputs["fees"]
        )
        r2 = compute_monthly_surplus(
            inputs["income"], inputs["expenses"], inputs["fees"]
        )
        assert r1 == r2

    def test_all_cashflow_deterministic(self):
        """Test all cashflow functions produce same output for same input."""
        incomes = [5000000, 5100000, 5000000]
        expenses = [4000000, 4100000, 4000000]

        for _ in range(2):
            r1 = compute_income_stability(incomes)
            r2 = compute_income_stability(incomes)
            assert r1 == r2

            r1 = compute_expense_stability(expenses)
            r2 = compute_expense_stability(expenses)
            assert r1 == r2

            r1 = compute_cashflow_stability_index(incomes, expenses)
            r2 = compute_cashflow_stability_index(incomes, expenses)
            assert r1 == r2


# ============================================================
# Account Concentration Tests (from test_behaviour_engine_account.py)
# ============================================================


class TestAccountConcentration:
    """Tests for compute_account_concentration function."""

    def test_concentration_single_account(self):
        """Test single account returns 1.0 (fully concentrated)."""
        result = compute_account_concentration([5000000])
        # Single account = fully concentrated
        assert result == Decimal("1")

    def test_concentration_multiple_equal(self):
        """Test equal balances across accounts."""
        # 3 accounts with equal balances
        result = compute_account_concentration([4000000, 4000000, 4000000])
        # Each account is 1/3 of total = 0.333...
        assert result == Decimal("0.3333")

    def test_concentration_one_large(self):
        """Test one large balance among many small ones."""
        # One large account: 8L, many small: 2L each (total 4L)
        result = compute_account_concentration([8000000, 2000000, 2000000, 2000000])
        # 8L / 14L = 0.5714
        assert result == Decimal("0.5714")

    def test_concentration_one_huge(self):
        """Test one huge balance vs many small (over-concentration)."""
        # One account has almost all the money: 99L / (99L + 3K) ≈ 0.9997
        result = compute_account_concentration([9900000, 10000, 10000, 10000])
        # 9900000 / 9903000 ≈ 0.9997 (very high concentration)
        assert Decimal("0.99") < result < Decimal("1")  # Very high but < 1

    def test_concentration_empty_list(self):
        """Test empty list returns 0."""
        result = compute_account_concentration([])
        assert result == Decimal("0")

    def test_concentration_all_zeros(self):
        """Test all zero balances returns 0 (no assets to concentrate)."""
        result = compute_account_concentration([0, 0, 0])
        assert result == Decimal("0")

    def test_concentration_deterministic(self):
        """Test that same inputs produce same outputs."""
        data = [5000000, 3000000, 2000000]
        r1 = compute_account_concentration(data)
        r2 = compute_account_concentration(data)
        assert r1 == r2


# ============================================================
# Idle Cash Tests (from test_behaviour_engine_account.py)
# ============================================================


class TestIdleCash:
    """Tests for compute_idle_cash_amount function."""

    def test_idle_cash_not_idle(self):
        """Test when deposit rate > loan rate (no idle cash)."""
        # Deposit rate 4% > Loan rate 12% by threshold 300bps
        result = compute_idle_cash_amount(
            cash_balance_paise=500000,
            loan_interest_rate_bps=1200,  # 12%
            deposit_interest_rate_bps=1500,  # 15%
        )
        # Deposit earns more, not idle
        assert result == Decimal("0")

    def test_idle_cash_is_idle(self):
        """Test when loan rate exceeds deposit rate by >300bps."""
        # Loan rate 12% - Deposit rate 4% = 800bps > 300bps threshold
        result = compute_idle_cash_amount(
            cash_balance_paise=500000,
            loan_interest_rate_bps=1200,  # 12%
            deposit_interest_rate_bps=400,  # 4%
        )
        # Rate diff = 800bps > 300bps threshold, entire balance is idle
        assert result == Decimal("500000")

    def test_idle_cash_exactly_at_threshold(self):
        """Test when rate differential equals threshold (not idle)."""
        # Loan rate 7% - Deposit rate 4% = 300bps = threshold
        result = compute_idle_cash_amount(
            cash_balance_paise=500000,
            loan_interest_rate_bps=700,  # 7%
            deposit_interest_rate_bps=400,  # 4%
            threshold_bps=300,
        )
        # Rate diff = 300bps, not > threshold, so not idle
        assert result == Decimal("0")

    def test_idle_cash_zero_balance(self):
        """Test zero cash balance returns 0."""
        result = compute_idle_cash_amount(
            cash_balance_paise=0,
            loan_interest_rate_bps=1200,
            deposit_interest_rate_bps=400,
        )
        assert result == Decimal("0")

    def test_idle_cash_custom_threshold(self):
        """Test custom threshold parameter."""
        # Rate diff = 200bps < default 300bps, but < custom 500bps
        result = compute_idle_cash_amount(
            cash_balance_paise=300000,
            loan_interest_rate_bps=1000,  # 10%
            deposit_interest_rate_bps=800,  # 8%
            threshold_bps=500,
        )
        # Rate diff = 200bps < 500bps threshold, not idle
        assert result == Decimal("0")

    def test_idle_cash_large_balance(self):
        """Test with large cash balance."""
        result = compute_idle_cash_amount(
            cash_balance_paise=10000000,  # ₹1L
            loan_interest_rate_bps=1500,  # 15%
            deposit_interest_rate_bps=300,  # 3%
        )
        assert result == Decimal("10000000")

    def test_idle_cash_deterministic(self):
        """Test that same inputs produce same outputs."""
        r1 = compute_idle_cash_amount(500000, 1200, 400)
        r2 = compute_idle_cash_amount(500000, 1200, 400)
        assert r1 == r2


# ============================================================
# Balance Volatility Tests (from test_behaviour_engine_account.py)
# ============================================================


class TestBalanceVolatility:
    """Tests for detect_balance_volatility function."""

    def test_volatility_stable(self):
        """Test stable balances (all equal) returns 0."""
        result = detect_balance_volatility([5000000, 5000000, 5000000, 5000000])
        # All equal = no variance
        assert result == Decimal("0")

    def test_volatility_variable(self):
        """Test variable balances returns positive volatility."""
        result = detect_balance_volatility([1000000, 2000000, 1500000, 3000000])
        # Variable values should produce coefficient of variation
        assert result > Decimal("0")

    def test_volatility_high(self):
        """Test highly volatile balances."""
        # Large swings: 50L to 90L (in paise)
        result = detect_balance_volatility([500000, 700000, 900000, 500000])
        # Coefficient of variation: sqrt(variance)/mean
        # Actual value is ~0.255, checking it's meaningfully volatile
        assert result > Decimal("0.2")

    def test_volatility_empty(self):
        """Test empty list returns 0."""
        result = detect_balance_volatility([])
        assert result == Decimal("0")

    def test_volatility_single_month(self):
        """Test single month returns 0 (no meaningful volatility)."""
        result = detect_balance_volatility([5000000])
        assert result == Decimal("0")

    def test_volatility_two_months_equal(self):
        """Test two equal months returns 0."""
        result = detect_balance_volatility([4000000, 4000000])
        assert result == Decimal("0")

    def test_volatility_all_zeros(self):
        """Test all zeros returns 0 (mean is zero)."""
        result = detect_balance_volatility([0, 0, 0, 0])
        assert result == Decimal("0")

    def test_volatility_deterministic(self):
        """Test that same inputs produce same outputs."""
        data = [1000000, 2000000, 1500000, 3000000]
        r1 = detect_balance_volatility(data)
        r2 = detect_balance_volatility(data)
        assert r1 == r2


# ============================================================
# Low Balance Risk Tests (from test_behaviour_engine_account.py)
# ============================================================


class TestLowBalanceRisk:
    """Tests for detect_low_balance_risk function."""

    def test_low_balance_no_risk(self):
        """Test balance >= essential expenses returns 0 risk."""
        result = detect_low_balance_risk(
            current_balance_paise=1500000,  # ₹15L
            essential_monthly_expenses_paise=1000000,  # ₹10L
        )
        assert result == Decimal("0")

    def test_low_balance_partial_risk(self):
        """Test balance < essential expenses returns partial risk."""
        result = detect_low_balance_risk(
            current_balance_paise=500000,  # ₹5L
            essential_monthly_expenses_paise=1000000,  # ₹10L
        )
        # Risk = (10L - 5L) / 10L = 0.5
        assert result == Decimal("0.5")

    def test_low_balance_high_risk(self):
        """Test very low balance returns high risk."""
        result = detect_low_balance_risk(
            current_balance_paise=100000,  # ₹1L (only 10% of essential)
            essential_monthly_expenses_paise=1000000,  # ₹10L
        )
        # Risk = (10L - 1L) / 10L = 0.9
        assert result == Decimal("0.9")

    def test_low_balance_zero_essential(self):
        """Test zero essential expenses returns 0 risk."""
        result = detect_low_balance_risk(
            current_balance_paise=500000,
            essential_monthly_expenses_paise=0,
        )
        # No essential expenses = no risk
        assert result == Decimal("0")

    def test_low_balance_zero_balance(self):
        """Test zero balance with essential expenses returns 1 (max risk)."""
        result = detect_low_balance_risk(
            current_balance_paise=0,
            essential_monthly_expenses_paise=1000000,
        )
        # Risk = (10L - 0) / 10L = 1.0
        assert result == Decimal("1")

    def test_low_balance_equals_essential(self):
        """Test balance equals essential expenses returns 0 risk."""
        result = detect_low_balance_risk(
            current_balance_paise=1000000,
            essential_monthly_expenses_paise=1000000,
        )
        assert result == Decimal("0")

    def test_low_balance_deterministic(self):
        """Test that same inputs produce same outputs."""
        r1 = detect_low_balance_risk(500000, 1000000)
        r2 = detect_low_balance_risk(500000, 1000000)
        assert r1 == r2


# ============================================================
# Account Intelligence Edge Cases (from test_behaviour_engine_account.py)
# ============================================================


class TestAccountIntelligenceEdgeCases:
    """Tests for edge cases and integration scenarios."""

    def test_multiple_savings_accounts_concentration(self):
        """Test concentration with multiple savings accounts."""
        # Scenario: User has 5 savings accounts
        balances = [2000000, 2000000, 1500000, 1500000, 1000000]  # Total: 8L
        result = compute_account_concentration(balances)
        # Max (2L) / Total (8L) = 0.25
        assert result == Decimal("0.25")

    def test_idle_funds_no_loan(self):
        """Test idle cash when no loan exists (high deposit rate)."""
        result = compute_idle_cash_amount(
            cash_balance_paise=500000,
            loan_interest_rate_bps=0,  # No loan
            deposit_interest_rate_bps=400,  # 4% deposit rate
        )
        # Deposit rate should be > loan rate (0), so no idle cash
        assert result == Decimal("0")

    def test_uneven_balances_volatility(self):
        """Test volatility with uneven monthly balances."""
        # Monthly balances vary significantly
        result = detect_balance_volatility([1000000, 2000000, 1500000, 3000000])
        # Should have some volatility
        assert Decimal("0") < result < Decimal("1")

    def test_combined_risk_scenario(self):
        """Test combined scenario: high concentration + idle cash + volatility."""
        # Set up a scenario where user has concentrated, volatile, idle cash
        balances = [5000000, 500000, 500000, 500000]  # High concentration (5M/6.5M)
        # 5000000 / 6500000 = ~0.77 (high but not > 0.8)
        assert compute_account_concentration(balances) > Decimal("0.7")

        # Idle cash because loan rate >> deposit rate
        assert compute_idle_cash_amount(
            cash_balance_paise=5000000,
            loan_interest_rate_bps=1500,
            deposit_interest_rate_bps=300,
        ) == Decimal("5000000")


# ============================================================
# Credit Dependency Ratio Tests (from test_behaviour_engine_debt.py)
# ============================================================


class TestCreditDependencyRatio:
    """Tests for compute_credit_dependency_ratio."""

    def test_no_credit_dependency(self):
        """No credit-funded expenses should return 0 ratio."""
        result = compute_credit_dependency_ratio(0, 100000)
        assert result == Decimal("0")

    def test_full_credit_dependency(self):
        """All expenses credit-funded should return 1.0 ratio."""
        result = compute_credit_dependency_ratio(100000, 100000)
        assert result == Decimal("1.0")

    def test_partial_credit_dependency(self):
        """Partial credit dependency returns appropriate ratio."""
        result = compute_credit_dependency_ratio(25000, 100000)
        assert result == Decimal("0.25")

    def test_credit_exceeds_expenses(self):
        """Credit-funded exceeding total expenses returns > 1 ratio."""
        result = compute_credit_dependency_ratio(150000, 100000)
        assert result == Decimal("1.5")


# ============================================================
# Debt Cycle Score Tests (from test_behaviour_engine_debt.py)
# ============================================================


class TestDebtCycleScore:
    """Tests for compute_debt_cycle_score."""

    def test_no_debt_cycle(self):
        """No credit advances, no revolving, negative trend -> score 0."""
        result = compute_debt_cycle_score(0, 0, Decimal("-0.5"))
        assert result == 0

    def test_increasing_debt_low_advances(self):
        """Low advances but rising trend -> elevated score."""
        result = compute_debt_cycle_score(1, 1, Decimal("0.7"))
        # advance=10, revolve=20, trend=80 -> 0.3*10 + 0.3*20 + 0.4*80 = 3+6+32 = 41
        assert result == 41

    def test_high_credit_advances(self):
        """Multiple credit advances -> high score."""
        result = compute_debt_cycle_score(4, 0, Decimal("0"))
        # advance=60, revolve=0, trend=5 -> 0.3*60 + 0.3*0 + 0.4*5 = 18+0+2 = 20
        assert result == 20

    def test_revolving_behavior(self):
        """Heavy revolving -> elevated score."""
        result = compute_debt_cycle_score(0, 5, Decimal("0.2"))
        # advance=0, revolve=80, trend=20 -> 0.3*0 + 0.3*80 + 0.4*20 = 0+24+8 = 32
        assert result == 32

    def test_max_debt_cycle(self):
        """Maximum debt cycle behavior -> high score near 100."""
        result = compute_debt_cycle_score(6, 6, Decimal("0.9"))
        # advance=90, revolve=80, trend=80 -> 0.3*90 + 0.3*80 + 0.4*80 = 27+24+32 = 83
        assert result == 83


# ============================================================
# FOIR Tests (from test_behaviour_engine_debt.py)
# ============================================================


class TestFOIR:
    """Tests for compute_foir."""

    def test_no_obligations(self):
        """No obligations and no income -> healthy with 0 ratio."""
        ratio, band = compute_foir(0, 0, 0)
        assert ratio == Decimal("0")
        assert band == "HEALTHY"

    def test_healthy_foir(self):
        """FOIR under 30% -> healthy band."""
        ratio, band = compute_foir(2000000, 500000, 10000000)  # 25%
        assert ratio == Decimal("0.25")
        assert band == "HEALTHY"

    def test_moderate_foir(self):
        """FOIR 30-50% -> moderate band."""
        ratio, band = compute_foir(3500000, 1500000, 10000000)  # 50%
        assert ratio == Decimal("0.50")
        assert band == "MODERATE"

    def test_warning_foir(self):
        """FOIR 50-60% -> warning band."""
        ratio, band = compute_foir(5500000, 0, 10000000)  # 55% - in warning range
        assert ratio == Decimal("0.55")
        assert band == "WARNING"

    def test_critical_foir(self):
        """FOIR over 60% -> critical band."""
        ratio, band = compute_foir(7000000, 0, 10000000)  # 70% - in critical range
        assert ratio == Decimal("0.70")
        assert band == "CRITICAL"

    def test_foir_exactly_30(self):
        """FOIR exactly 30% -> healthy band is inclusive at 30%."""
        ratio, band = compute_foir(3000000, 0, 10000000)
        assert ratio == Decimal("0.30")
        assert band == "HEALTHY"

    def test_foir_above_30(self):
        """FOIR just above 30% -> moderate band."""
        ratio, band = compute_foir(3100000, 0, 10000000)  # 31%
        assert ratio == Decimal("0.31")
        assert band == "MODERATE"

    def test_emi_heavy_user(self):
        """EMI-heavy user with high FOIR -> critical band."""
        # Income ₹1L, EMI ₹70K, min due ₹5K = 75% FOIR
        ratio, band = compute_foir(7000000, 500000, 10000000)
        assert ratio == Decimal("0.75")
        assert band == "CRITICAL"


# ============================================================
# Credit Revolver Ratio Tests (from test_behaviour_engine_debt.py)
# ============================================================


class TestCreditRevolverRatio:
    """Tests for compute_credit_revolver_ratio."""

    def test_no_credit_activity(self):
        """No credit activity -> 0 ratio."""
        result = compute_credit_revolver_ratio(0, 0)
        assert result == Decimal("0")

    def test_full_revolver(self):
        """All active months with partial payment -> 1.0 ratio."""
        result = compute_credit_revolver_ratio(6, 6)
        assert result == Decimal("1.0")

    def test_partial_revolver(self):
        """Some revolving months -> partial ratio."""
        result = compute_credit_revolver_ratio(3, 6)
        assert result == Decimal("0.5")

    def test_no_revolving(self):
        """No partial payments -> 0 ratio."""
        result = compute_credit_revolver_ratio(0, 6)
        assert result == Decimal("0")


# ============================================================
# Determinism Tests (from test_behaviour_engine_debt.py)
# ============================================================


class TestDebtDeterminism:
    """Tests to ensure deterministic behavior."""

    def test_foir_deterministic(self):
        """Same inputs should produce same outputs."""
        for _ in range(10):
            ratio, band = compute_foir(
                4000000, 1500000, 10000000
            )  # 55% - warning range
            assert ratio == Decimal("0.55")
            assert band == "WARNING"

    def test_debt_cycle_deterministic(self):
        """Debt cycle score should be deterministic."""
        result = compute_debt_cycle_score(3, 2, Decimal("0.25"))
        # advance=30, revolve=20, trend=20 -> 0.3*30 + 0.3*20 + 0.4*20 = 9+6+8 = 23
        assert result == 23


# ============================================================
# Income Source Classification Tests (from test_behaviour_engine_income.py)
# ============================================================


class TestClassifyIncomeSource:
    """Tests for income source classification."""

    def test_salary_classification(self):
        """Test SALARY classification."""
        txn = {"description": "Salary credit for April"}
        category, confidence = classify_income_source(txn)
        assert category == "salary"
        assert confidence >= 0.8

    def test_salary_salaried_match(self):
        """Test SALARY classification for salaried."""
        txn = {"description": "Salaried employee payment"}
        category, confidence = classify_income_source(txn)
        assert category == "salary"

    def test_business_classification(self):
        """Test BUSINESS classification."""
        txn = {"description": "Freelance consulting payment"}
        category, confidence = classify_income_source(txn)
        assert category == "business"

    def test_business_commission(self):
        """Test BUSINESS classification for commission."""
        txn = {"description": "Sales commission received"}
        category, confidence = classify_income_source(txn)
        assert category == "business"

    def test_investment_classification(self):
        """Test INVESTMENT classification."""
        txn = {"description": "Dividend from stocks"}
        category, confidence = classify_income_source(txn)
        assert category == "investment"

    def test_investment_interest(self):
        """Test INVESTMENT classification for interest income."""
        txn = {"description": "Fixed deposit interest income"}
        category, confidence = classify_income_source(txn)
        assert category == "investment"

    def test_investment_mutual_fund(self):
        """Test INVESTMENT classification for mutual fund."""
        txn = {"description": "Mutual fund returns"}
        category, confidence = classify_income_source(txn)
        assert category == "investment"

    def test_transfer_classification(self):
        """Test TRANSFER classification."""
        txn = {"description": "Transfer to own account"}
        category, confidence = classify_income_source(txn)
        assert category == "transfer"

    def test_refund_classification(self):
        """Test REFUND classification."""
        txn = {"description": "Refund from Amazon purchase"}
        category, confidence = classify_income_source(txn)
        assert category == "refund"

    def test_refund_cashback(self):
        """Test REFUND classification for cashback."""
        txn = {"description": "Cashback reward credited"}
        category, confidence = classify_income_source(txn)
        assert category == "refund"

    def test_borrowing_classification(self):
        """Test BORROWING classification."""
        txn = {"description": "Loan from bank credited"}
        category, confidence = classify_income_source(txn)
        assert category == "borrowing"

    def test_unknown_classification(self):
        """Test UNKNOWN classification for no matching keywords."""
        txn = {"description": "XYZ Corporation payment"}
        category, confidence = classify_income_source(txn)
        assert category == "unknown"

    def test_empty_description(self):
        """Test UNKNOWN classification for empty description."""
        txn = {"description": ""}
        category, confidence = classify_income_source(txn)
        assert category == "unknown"
        assert confidence == 0.0

    def test_whole_word_confidence(self):
        """Test that whole-word match gets confidence 1.0."""
        txn = {"description": "Salary credit"}
        category, confidence = classify_income_source(txn)
        assert category == "salary"
        assert confidence == 1.0  # "salary" is a whole word

    def test_partial_word_confidence(self):
        """Test that partial match gets confidence 0.8."""
        txn = {"description": "Salarycredited"}  # No space
        category, confidence = classify_income_source(txn)
        assert category == "salary"
        assert confidence == 0.8  # Partial match (substring in larger word)

    def test_classify_deterministic(self):
        """Test that classification is deterministic."""
        txn = {"description": "Salary credit"}
        for _ in range(10):
            category, confidence = classify_income_source(txn)
            assert category == "salary"
            assert confidence == 1.0


# ============================================================
# Salary Dependence Ratio Tests (from test_behaviour_engine_income.py)
# ============================================================


class TestSalaryDependenceRatio:
    """Tests for salary dependence ratio calculation."""

    def test_full_dependence(self):
        """Test 100% salary dependence."""
        result = compute_salary_dependence_ratio(5000000, 5000000)
        assert result == Decimal("1.0")

    def test_partial_dependence(self):
        """Test partial salary dependence."""
        result = compute_salary_dependence_ratio(2500000, 5000000)
        assert result == Decimal("0.5")

    def test_low_dependence(self):
        """Test low salary dependence (diversified income)."""
        result = compute_salary_dependence_ratio(1000000, 5000000)
        assert result == Decimal("0.2")

    def test_zero_salary(self):
        """Test zero salary dependence."""
        result = compute_salary_dependence_ratio(0, 5000000)
        assert result == Decimal("0")

    def test_zero_true_income(self):
        """Test with zero true income returns 0."""
        result = compute_salary_dependence_ratio(5000000, 0)
        assert result == Decimal("0")

    def test_both_zero(self):
        """Test with both zero returns 0."""
        result = compute_salary_dependence_ratio(0, 0)
        assert result == Decimal("0")

    def test_salary_exceeds_true_income(self):
        """Test when salary exceeds true income (shouldn't happen, but handle gracefully)."""
        result = compute_salary_dependence_ratio(6000000, 5000000)
        assert result == Decimal("1.2")

    def test_salary_dependence_deterministic(self):
        """Test determinism of salary dependence ratio."""
        for _ in range(10):
            result = compute_salary_dependence_ratio(3000000, 4000000)
            assert result == Decimal("0.75")


# ============================================================
# Income Diversification Score Tests (from test_behaviour_engine_income.py)
# ============================================================


class TestIncomeDiversificationScore:
    """Tests for income diversification score."""

    def test_no_transactions(self):
        """Test empty transactions returns 0."""
        result = compute_income_diversification_score([])
        assert result == Decimal("0")

    def test_single_source_salary_only(self, salary_transactions):
        """Test single source (salary only) returns ~0.33."""
        result = compute_income_diversification_score(salary_transactions)
        assert result == Decimal("0.3333")  # Only "salary" category, 1/3

    def test_two_sources_salary_investment(self, diversified_transactions):
        """Test two sources (salary + investment) returns ~0.67."""
        result = compute_income_diversification_score(diversified_transactions)
        # "salary" and "investment" categories
        assert result == Decimal("0.6667")

    def test_three_sources(self):
        """Test three sources returns 1.0 (capped)."""
        txns = [
            {"description": "Salary credit", "amount_paise": 5000000},
            {"description": "Business income", "amount_paise": 200000},
            {"description": "Dividend from stocks"},
        ]
        result = compute_income_diversification_score(txns)
        assert result == Decimal("1.0")  # All 3 categories = max

    def test_excludes_transfers(self, mixed_transactions):
        """Test that TRANSFER transactions are excluded from diversification."""
        result = compute_income_diversification_score(mixed_transactions)
        # Only salary + business + investment (transfer, loan, refund excluded)
        assert result == Decimal("1.0")  # All 3 categories = max

    def test_excludes_loans(self):
        """Test that BORROWING transactions are excluded from diversification."""
        txns = [
            {"description": "Salary credit"},
            {"description": "Loan from bank credited"},
            {"description": "Investment dividend"},
        ]
        result = compute_income_diversification_score(txns)
        # Only salary + investment (loan excluded) = 2/3
        assert result == Decimal("0.6667")

    def test_excludes_refunds(self):
        """Test that REFUND transactions are excluded from diversification."""
        txns = [
            {"description": "Salary credit"},
            {"description": "Refund from merchant"},
            {"description": "Consulting income"},
        ]
        result = compute_income_diversification_score(txns)
        # Only salary + business (refund excluded) = 2/3
        assert result == Decimal("0.6667")

    def test_diversification_deterministic(self, diversified_transactions):
        """Test that diversification score is deterministic."""
        for _ in range(10):
            result = compute_income_diversification_score(diversified_transactions)
            assert result == Decimal("0.6667")


# ============================================================
# True Income Helpers Tests (from test_behaviour_engine_income.py)
# ============================================================


class TestTrueIncomeHelpers:
    """Tests for true income helper functions."""

    def test_filter_true_income(self, mixed_transactions):
        """Test filtering excludes non-true income."""
        filtered = filter_true_income(mixed_transactions)
        assert len(filtered) == 3  # Only salary, business, investment (3 items)
        # Verify each filtered transaction is a true income category
        for txn in filtered:
            category, _ = classify_income_source(txn)
            assert category in {"salary", "business", "investment"}

    def test_compute_true_income_total(self, mixed_transactions):
        """Test true income total excludes non-true income."""
        total = compute_true_income_total(mixed_transactions)
        # Salary + Business + Investment = 5000000 + 200000 + 50000 = 5250000
        assert total == 5250000

    def test_compute_true_income_total_empty(self):
        """Test true income total with empty list."""
        total = compute_true_income_total([])
        assert total == 0

    def test_true_income_total_deterministic(self, mixed_transactions):
        """Test determinism of true income total."""
        for _ in range(10):
            total = compute_true_income_total(mixed_transactions)
            assert total == 5250000


# ============================================================
# Edge Cases Tests (from test_behaviour_engine_income.py)
# ============================================================


class TestIncomeEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_missing_amount_key(self):
        """Test transactions without amount_paise key."""
        txns = [
            {"description": "Salary credit"},  # No amount
            {"description": "Business payment", "amount_paise": 500000},
        ]
        result = compute_income_diversification_score(txns)
        assert result == Decimal("0.6667")

    def test_missing_description_key(self):
        """Test transactions without description key."""
        txns = [
            {"amount_paise": 500000},  # No description
            {"description": "Dividend income"},
        ]
        result = compute_income_diversification_score(txns)
        assert result == Decimal("0.3333")  # Only investment

    def test_all_non_income_sources(self):
        """Test when all transactions are non-income sources."""
        txns = [
            {"description": "Transfer to own account"},
            {"description": "Loan from bank"},
            {"description": "Cashback reward"},
        ]
        result = compute_income_diversification_score(txns)
        assert result == Decimal("0")

    def test_case_insensitivity(self):
        """Test that classification is case-insensitive."""
        txns = [
            {"description": "SALARY CREDIT"},
            {"description": "Business Payment"},
            {"description": "DIVIDEND Income"},
        ]
        result = compute_income_diversification_score(txns)
        assert result == Decimal("1.0")  # All three categories


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
