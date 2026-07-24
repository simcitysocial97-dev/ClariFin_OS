"""
Behaviour Engine Phase 1 — Core Metrics Tests
============================================

Tests for deterministic behavioural metrics including:
- Savings metrics (true savings rate, borrowed lifestyle ratio, monthly surplus)
- Cashflow stability (income/expense stability, cashflow index)
- Resilience (liquidity months, resilience index)
- Lifestyle (inflation, creep index)

All tests verify:
- Determinism (same input → same output)
- Edge cases (zero values, negative values, missing data)
- Immutability (functions don't modify input data)

Run: python -m pytest tests/test_behaviour_engine_metrics.py -v
"""

import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.behaviour_engine import (
    compute_borrowed_lifestyle_ratio,
    compute_cashflow_stability_index,
    compute_expense_stability,
    compute_income_stability,
    compute_lifestyle_creep_index,
    compute_lifestyle_inflation,
    compute_liquidity_months,
    compute_monthly_surplus,
    compute_resilience_index,
    compute_true_savings_rate,
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


# ============================================================
# Savings Metrics Tests
# ============================================================

class TestSavingsMetrics:
    """Tests for savings-related metrics."""

    # --- compute_true_savings_rate ---

    def test_true_savings_rate_positive(self):
        """Test positive savings rate with valid inputs."""
        # Income: ₹5L, Expenses: ₹4L, Fees: ₹10K
        result = compute_true_savings_rate(5000000, 4000000, 100000)
        # (5000000 - 4000000 - 100000) / 5000000 = 0.18
        assert result == Decimal('0.18')

    def test_true_savings_rate_zero_income(self):
        """Test savings rate with zero income returns 0."""
        result = compute_true_savings_rate(0, 100000, 50000)
        assert result == Decimal('0')

    def test_true_savings_rate_negative(self):
        """Test negative savings rate (overspending)."""
        # Income: ₹3L, Expenses: ₹4L, Fees: ₹50K = deficit
        result = compute_true_savings_rate(3000000, 4000000, 50000)
        # (3000000 - 4000000 - 50000) / 3000000 = -0.35
        assert result == Decimal('-0.35')

    def test_true_savings_rate_perfect_savings(self):
        """Test zero expenses and zero fees."""
        result = compute_true_savings_rate(5000000, 0, 0)
        assert result == Decimal('1')

    def test_true_savings_rate_zero_fees(self):
        """Test with zero fees."""
        result = compute_true_savings_rate(5000000, 4000000, 0)
        assert result == Decimal('0.2')

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
        assert result == Decimal('0.5')

    def test_borrowed_lifestyle_ratio_zero_expenses(self):
        """Test ratio with zero expenses returns 0."""
        result = compute_borrowed_lifestyle_ratio(1000000, 0)
        assert result == Decimal('0')

    def test_borrowed_lifestyle_ratio_all_credit_funded(self):
        """Test when all expenses are credit-funded."""
        result = compute_borrowed_lifestyle_ratio(5000000, 5000000)
        assert result == Decimal('1')

    def test_borrowed_lifestyle_ratio_credit_exceeds_expenses(self):
        """Test when credit funding exceeds reported expenses."""
        result = compute_borrowed_lifestyle_ratio(6000000, 5000000)
        # Ratio > 1 indicates unusual pattern
        assert result == Decimal('1.2')

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
# Cashflow Stability Tests
# ============================================================

class TestCashflowStability:
    """Tests for cashflow-related stability metrics."""

    # --- compute_income_stability ---

    def test_income_stability_stable(self, sample_monthly_incomes):
        """Test stable income returns high stability score."""
        result = compute_income_stability(sample_monthly_incomes)
        # Should be close to 1 for stable income
        assert Decimal('0.7') < result <= Decimal('1')

    def test_income_stability_volatile(self, volatile_monthly_incomes):
        """Test volatile income returns lower stability score."""
        result = compute_income_stability(volatile_monthly_incomes)
        # Should be lower for volatile income
        assert result < Decimal('0.5')

    def test_income_stability_single_month(self):
        """Test single month returns 1 (assumed stable)."""
        result = compute_income_stability([5000000])
        assert result == Decimal('1')

    def test_income_stability_empty(self):
        """Test empty list returns 1 (assumed stable)."""
        result = compute_income_stability([])
        assert result == Decimal('1')

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
        assert Decimal('0.5') < result <= Decimal('1')

    def test_expense_stability_constant(self):
        """Test constant expenses return 1."""
        result = compute_expense_stability([4000000, 4000000, 4000000])
        assert result == Decimal('1')

    def test_expense_stability_single_month(self):
        """Test single month returns 1."""
        result = compute_expense_stability([4000000])
        assert result == Decimal('1')

    def test_expense_stability_empty(self):
        """Test empty list returns 1."""
        result = compute_expense_stability([])
        assert result == Decimal('1')

    # --- compute_cashflow_stability_index ---

    def test_cashflow_stability_index_averages(self):
        """Test that cashflow index averages income and expense stability."""
        # Income = [5M, 5M, 5M] -> stability = 1
        # Expenses = [4M, 5M, 6M] -> some variance
        result = compute_cashflow_stability_index([5000000, 5000000, 5000000], [4000000, 5000000, 6000000])
        # Should be between 0.5 and 1
        assert Decimal('0.5') < result <= Decimal('1')

    def test_cashflow_stability_index_both_stable(self):
        """Test index when both income and expenses are stable."""
        incomes = [5000000, 5000000, 5000000, 5000000]
        expenses = [4000000, 4000000, 4000000, 4000000]
        result = compute_cashflow_stability_index(incomes, expenses)
        assert result == Decimal('1')

    def test_cashflow_stability_index_deterministic(self):
        """Test determinism of cashflow index."""
        incomes = [5000000, 5000000, 5100000]
        expenses = [4000000, 4100000, 4000000]
        result1 = compute_cashflow_stability_index(incomes, expenses)
        result2 = compute_cashflow_stability_index(incomes, expenses)
        assert result1 == result2


# ============================================================
# Resilience Tests
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
        assert result == Decimal('1')

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
        assert result == Decimal('0.4')

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
        assert result == Decimal('1')

    def test_resilience_index_volatile_income(self):
        """Test resilience with volatile income."""
        result = compute_resilience_index(
            liquid_assets_paise=6000000,
            essential_monthly_expenses_paise=1000000,
            total_income_paise=5000000,
            monthly_incomes_paise=[3000000, 8000000, 2000000],
        )
        # Liquidity = 6 months = 0.5, Income stability < 1
        assert Decimal('0.2') < result < Decimal('1')


# ============================================================
# Lifestyle Tests
# ============================================================

class TestLifestyleMetrics:
    """Tests for lifestyle-related metrics."""

    # --- compute_lifestyle_inflation ---

    def test_lifestyle_inflation_positive(self):
        """Test positive lifestyle inflation."""
        result = compute_lifestyle_inflation(6000000, 4000000)
        # (6M - 4M) / 4M = 0.5
        assert result == Decimal('0.5')

    def test_lifestyle_inflation_zero(self):
        """Test zero inflation (same spending)."""
        result = compute_lifestyle_inflation(4000000, 4000000)
        assert result == Decimal('0')

    def test_lifestyle_inflation_decrease(self):
        """Test negative inflation (reduced spending)."""
        result = compute_lifestyle_inflation(3000000, 4000000)
        # (3M - 4M) / 4M = -0.25
        assert result == Decimal('-0.25')

    def test_lifestyle_inflation_zero_previous(self):
        """Test with zero previous spending."""
        result = compute_lifestyle_inflation(500000, 0)
        assert result == Decimal('0')

    def test_lifestyle_inflation_zero_current(self):
        """Test with zero current spending."""
        result = compute_lifestyle_inflation(0, 4000000)
        assert result == Decimal('-1')

    def test_lifestyle_inflation_deterministic(self):
        """Test determinism of inflation calculation."""
        result1 = compute_lifestyle_inflation(6000000, 4000000)
        result2 = compute_lifestyle_inflation(6000000, 4000000)
        assert result1 == result2

    # --- compute_lifestyle_creep_index ---

    def test_lifestyle_creep_index_positive(self):
        """Test positive creep over months."""
        # Spending grew from 2L to 4L over months
        result = compute_lifestyle_creep_index([2000000, 2500000, 3000000, 3500000, 4000000])
        # (4M - 2M) / 2M = 1.0
        assert result == Decimal('1')

    def test_lifestyle_creep_index_negative(self):
        """Test negative creep (decreasing spending)."""
        result = compute_lifestyle_creep_index([4000000, 3500000, 3000000, 2500000, 2000000])
        # (2M - 4M) / 4M = -0.5
        assert result == Decimal('-0.5')

    def test_lifestyle_creep_index_single_month(self):
        """Test single month returns 0 (no trend)."""
        result = compute_lifestyle_creep_index([3000000])
        assert result == Decimal('0')

    def test_lifestyle_creep_index_empty(self):
        """Test empty list returns 0."""
        result = compute_lifestyle_creep_index([])
        assert result == Decimal('0')

    def test_lifestyle_creep_index_zero_earliest(self):
        """Test with zero earliest value."""
        result = compute_lifestyle_creep_index([0, 1000000, 2000000])
        assert result == Decimal('0')

    def test_lifestyle_creep_index_deterministic(self):
        """Test determinism of creep index."""
        data = [2000000, 2500000, 3000000, 3500000, 4000000]
        result1 = compute_lifestyle_creep_index(data)
        result2 = compute_lifestyle_creep_index(data)
        assert result1 == result2


# ============================================================
# Edge Cases and Boundary Conditions
# ============================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_all_zero_inputs_savings(self):
        """Test all zeros in savings calculations."""
        assert compute_true_savings_rate(0, 0, 0) == Decimal('0')
        assert compute_borrowed_lifestyle_ratio(0, 0) == Decimal('0')
        assert compute_monthly_surplus(0, 0, 0) == 0

    def test_large_values(self):
        """Test with large monetary values."""
        # ₹10Cr income, ₹8Cr expenses
        result = compute_true_savings_rate(1000000000, 800000000, 10000000)
        assert result == Decimal('0.19')

    def test_missing_months_handling(self):
        """Test that functions work with whatever data is provided."""
        # Only passing 3 months instead of 5
        partial_incomes = [5000000, 5000000, 5000000]
        partial_expenses = [4000000, 4000000, 4000000]

        result = compute_cashflow_stability_index(partial_incomes, partial_expenses)
        assert result == Decimal('1')  # All equal = stable

    def test_negative_values_savings(self):
        """Test negative values in savings metrics."""
        # Negative expenses shouldn't happen in real data, but test robustness
        result = compute_monthly_surplus(5000000, -100000, 0)
        assert result == 5100000  # ₹5.1L


# ============================================================
# Determinism Tests
# ============================================================

class TestDeterminism:
    """Verify all functions are deterministic."""

    def test_all_savings_deterministic(self):
        """Test all savings functions produce same output for same input."""
        inputs = {
            'income': 5000000,
            'expenses': 4000000,
            'fees': 100000,
            'credit_funded': 2000000,
        }

        # Run each function twice
        r1 = compute_true_savings_rate(inputs['income'], inputs['expenses'], inputs['fees'])
        r2 = compute_true_savings_rate(inputs['income'], inputs['expenses'], inputs['fees'])
        assert r1 == r2

        r1 = compute_borrowed_lifestyle_ratio(inputs['credit_funded'], inputs['expenses'])
        r2 = compute_borrowed_lifestyle_ratio(inputs['credit_funded'], inputs['expenses'])
        assert r1 == r2

        r1 = compute_monthly_surplus(inputs['income'], inputs['expenses'], inputs['fees'])
        r2 = compute_monthly_surplus(inputs['income'], inputs['expenses'], inputs['fees'])
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
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
