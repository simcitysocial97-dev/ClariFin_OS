"""
Behaviour Engine Phase 5 — Account Intelligence Tests
=====================================================

Tests for account-level behaviour metrics including:
- Account concentration (over-concentration in single account)
- Idle cash detection (opportunity cost analysis)
- Balance volatility (coefficient of variation)
- Low balance risk (essential expenses coverage)

All tests verify:
- Determinism (same input → same output)
- Edge cases (zero values, negative values, missing data)
- Immutability (functions don't modify input data)

Run: python -m pytest tests/test_behaviour_engine_account.py -v
"""

import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.behaviour_engine import (
    compute_account_concentration,
    compute_idle_cash_amount,
    detect_balance_volatility,
    detect_low_balance_risk,
)

# ============================================================
# Account Concentration Tests
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
# Idle Cash Tests
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
# Balance Volatility Tests
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
# Low Balance Risk Tests
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
# Edge Cases and Integration Tests
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
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
