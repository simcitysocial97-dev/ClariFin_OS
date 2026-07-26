"""
Account Engine Tests - Determinism and Financial Correctness
===========================================================
Tests for all account engine modules.

All monetary values in paise (integer).
All rates in basis points (integer).
"""

import pytest

from engines.account_engine import (
    compute_account_metrics,
    compute_account_status,
    compute_average_balance,
    compute_balance_change,
    compute_balance_growth_percentage,
    compute_balance_trend,
    compute_balance_velocity,
    compute_cash_flow_rate,
    compute_days_since_activity,
    compute_income_expense_ratio,
    compute_net_cash_flow,
    is_account_closed,
    is_account_dormant,
)

# ============================================================
# Lifecycle Tests
# ============================================================


class TestComputeAccountStatus:
    """Tests for compute_account_status function."""

    def test_compute_account_status_active_account(self):
        """Active account with recent transaction."""
        # Account active, transaction 30 days ago
        result = compute_account_status(True, "2026-06-07", "2026-07-07")
        assert result == "ACTIVE"

    def test_compute_account_status_dormant_account(self):
        """Dormant account with old transaction."""
        # Account active, transaction 400 days ago (beyond 365 threshold)
        result = compute_account_status(True, "2025-06-01", "2026-07-07")
        assert result == "DORMANT"

    def test_compute_account_status_closed_account_is_active_false(self):
        """Closed account due to admin closure."""
        result = compute_account_status(False, "2026-06-01", "2026-07-07")
        assert result == "CLOSED"

    def test_compute_account_status_closed_account_no_history(self):
        """Closed account due to no transaction history."""
        result = compute_account_status(True, None, "2026-07-07")
        assert result == "CLOSED"

    def test_compute_account_status_exactly_at_threshold(self):
        """Status at exact dormancy threshold (365 days)."""
        # 365 days since last transaction
        result = compute_account_status(True, "2025-07-07", "2026-07-07")
        assert result == "DORMANT"

    def test_compute_account_status_one_day_before_threshold(self):
        """Status one day before dormancy threshold."""
        # 364 days since last transaction
        result = compute_account_status(True, "2025-07-08", "2026-07-07")
        assert result == "ACTIVE"

    def test_compute_account_status_reactivation(self):
        """Reactivated dormant account."""
        # After being dormant, new transaction within threshold
        result = compute_account_status(True, "2026-06-01", "2026-07-07")
        assert result == "ACTIVE"


class TestIsAccountClosed:
    """Tests for is_account_closed helper function."""

    def test_is_account_closed_false_active(self):
        """Active account returns False."""
        assert is_account_closed(True, "2026-06-01") is False

    def test_is_account_closed_true_inactive(self):
        """Inactive account returns True."""
        assert is_account_closed(False, "2026-06-01") is True

    def test_is_account_closed_true_no_history(self):
        """No transaction history returns True."""
        assert is_account_closed(True, None) is True


# ============================================================
# Balance Tests
# ============================================================


class TestComputeAverageBalance:
    """Tests for compute_average_balance function."""

    def test_compute_average_balance_basic(self):
        """Basic average calculation."""
        # [100000, 200000, 300000] paise
        balances = [100000, 200000, 300000]
        result = compute_average_balance(balances)
        assert result == 200000

    def test_compute_average_balance_single_value(self):
        """Single value returns itself."""
        result = compute_average_balance([150000])
        assert result == 150000

    def test_compute_average_balance_empty_list(self):
        """Empty list returns 0."""
        result = compute_average_balance([])
        assert result == 0

    def test_compute_average_balance_zero_values(self):
        """List of zeros returns 0."""
        result = compute_average_balance([0, 0, 0])
        assert result == 0

    def test_compute_average_balance_large_values(self):
        """Large balance values handled correctly."""
        # ₹1,00,00,000 (1 crore) in paise
        balances = [10000000000, 10000000000, 10000000000]
        result = compute_average_balance(balances)
        assert result == 10000000000

    def test_compute_average_balance_rounding(self):
        """Rounding with ROUND_HALF_UP."""
        # [100, 101, 102] -> average 101
        result = compute_average_balance([100, 101, 102])
        assert result == 101


class TestComputeBalanceChange:
    """Tests for compute_balance_change function."""

    def test_compute_balance_change_positive(self):
        """Positive change (balance increased)."""
        result = compute_balance_change(100000, 150000)
        assert result == 50000

    def test_compute_balance_change_negative(self):
        """Negative change (balance decreased)."""
        result = compute_balance_change(150000, 100000)
        assert result == -50000

    def test_compute_balance_change_zero(self):
        """No change returns 0."""
        result = compute_balance_change(100000, 100000)
        assert result == 0

    def test_compute_balance_change_to_zero(self):
        """Change to zero."""
        result = compute_balance_change(100000, 0)
        assert result == -100000

    def test_compute_balance_change_from_zero(self):
        """Change from zero."""
        result = compute_balance_change(0, 100000)
        assert result == 100000


class TestComputeBalanceGrowthPercentage:
    """Tests for compute_balance_growth_percentage function."""

    def test_compute_balance_growth_percentage_positive(self):
        """10% growth returns 1000 bps."""
        # 100000 -> 110000 is 10% growth
        result = compute_balance_growth_percentage(100000, 110000)
        assert result == 1000

    def test_compute_balance_growth_percentage_negative(self):
        """Decline returns negative bps (ROUND_HALF_UP)."""
        result = compute_balance_growth_percentage(110000, 100000)
        assert result == -909  # -10000/110000 * 10000 = -909.09... -> -909

    def test_compute_balance_growth_percentage_zero(self):
        """No change returns 0 bps."""
        result = compute_balance_growth_percentage(100000, 100000)
        assert result == 0

    def test_compute_balance_growth_percentage_zero_previous(self):
        """Zero previous balance returns 0 bps (avoid division by zero)."""
        result = compute_balance_growth_percentage(0, 100000)
        assert result == 0

    def test_compute_balance_growth_percentage_rounding(self):
        """Rounding to nearest basis point."""
        # 100 -> 115 is 15% which is 1500 bps
        result = compute_balance_growth_percentage(100, 115)
        assert result == 1500


# ============================================================
# Cashflow Tests
# ============================================================


class TestComputeNetCashFlow:
    """Tests for compute_net_cash_flow function."""

    def test_compute_net_cash_flow_positive(self):
        """Positive net flow (more credits than debits)."""
        result = compute_net_cash_flow(500000, 300000)
        assert result == 200000

    def test_compute_net_cash_flow_negative(self):
        """Negative net flow (more debits than credits)."""
        result = compute_net_cash_flow(300000, 500000)
        assert result == -200000

    def test_compute_net_cash_flow_zero(self):
        """Zero net flow (equal credits and debits)."""
        result = compute_net_cash_flow(500000, 500000)
        assert result == 0

    def test_compute_net_cash_flow_all_credits(self):
        """All credits, no debits."""
        result = compute_net_cash_flow(500000, 0)
        assert result == 500000

    def test_compute_net_cash_flow_all_debits(self):
        """No credits, all debits."""
        result = compute_net_cash_flow(0, 500000)
        assert result == -500000


class TestComputeCashFlowRate:
    """Tests for compute_cash_flow_rate function."""

    def test_compute_cash_flow_rate_basic(self):
        """Basic daily rate calculation."""
        result = compute_cash_flow_rate(3000000, 30)  # 30000 paise over 30 days
        assert result == 100000

    def test_compute_cash_flow_rate_negative_flow(self):
        """Negative flow rate (net outflow)."""
        result = compute_cash_flow_rate(-300000, 10)
        assert result == -30000

    def test_compute_cash_flow_rate_zero_flow(self):
        """Zero flow returns zero rate."""
        result = compute_cash_flow_rate(0, 30)
        assert result == 0

    def test_compute_cash_flow_rate_zero_days_raises(self):
        """Zero days raises ValueError."""
        with pytest.raises(ValueError, match="days must be positive"):
            compute_cash_flow_rate(100000, 0)

    def test_compute_cash_flow_rate_negative_days_raises(self):
        """Negative days raises ValueError."""
        with pytest.raises(ValueError, match="days must be positive"):
            compute_cash_flow_rate(100000, -1)

    def test_compute_cash_flow_rate_rounding(self):
        """Rounding with ROUND_HALF_UP."""
        # 100/3 = 33.333... rounds to 33
        result = compute_cash_flow_rate(100, 3)
        assert result == 33


class TestComputeIncomeExpenseRatio:
    """Tests for compute_income_expense_ratio function."""

    def test_compute_income_expense_ratio_equal(self):
        """Income equals expense (100% ratio = 10000 bps)."""
        result = compute_income_expense_ratio(100000, 100000)
        assert result == 10000

    def test_compute_income_expense_ratio_higher_income(self):
        """Higher income (200% ratio = 20000 bps)."""
        result = compute_income_expense_ratio(200000, 100000)
        assert result == 20000

    def test_compute_income_expense_ratio_lower_income(self):
        """Lower income (50% ratio = 5000 bps)."""
        result = compute_income_expense_ratio(50000, 100000)
        assert result == 5000

    def test_compute_income_expense_ratio_zero_income(self):
        """Zero income returns 0 bps."""
        result = compute_income_expense_ratio(0, 100000)
        assert result == 0

    def test_compute_income_expense_ratio_zero_expense(self):
        """Zero expense returns 0 bps (avoid division by zero)."""
        result = compute_income_expense_ratio(100000, 0)
        assert result == 0

    def test_compute_income_expense_ratio_rounding(self):
        """Rounding to nearest basis point."""
        # 33333/100000 = 33.333% = 3333 bps
        result = compute_income_expense_ratio(33333, 100000)
        assert result == 3333


# ============================================================
# Dormancy Tests
# ============================================================


class TestComputeDaysSinceActivity:
    """Tests for compute_days_since_activity function."""

    def test_compute_days_since_activity_basic(self):
        """Basic day calculation."""
        result = compute_days_since_activity("2026-06-01", "2026-07-01")
        assert result == 30

    def test_compute_days_since_activity_one_year(self):
        """One year difference."""
        result = compute_days_since_activity("2025-07-07", "2026-07-07")
        assert result == 365

    def test_compute_days_since_activity_same_day(self):
        """Same day returns 0."""
        result = compute_days_since_activity("2026-07-07", "2026-07-07")
        assert result == 0

    def test_compute_days_since_activity_future_date_raises(self):
        """Future date raises ValueError."""
        with pytest.raises(ValueError, match="cannot be after"):
            compute_days_since_activity("2026-07-08", "2026-07-07")


class TestIsAccountDormant:
    """Tests for is_account_dormant function."""

    def test_is_account_dormant_below_threshold(self):
        """Below threshold returns False."""
        assert is_account_dormant(364, 365) is False

    def test_is_account_dormant_at_threshold(self):
        """At threshold returns True."""
        assert is_account_dormant(365, 365) is True

    def test_is_account_dormant_above_threshold(self):
        """Above threshold returns True."""
        assert is_account_dormant(400, 365) is True

    def test_is_account_dormant_zero_days(self):
        """Zero days with default threshold returns False."""
        # 0 < 365, so not dormant
        assert is_account_dormant(0, 365) is False

    def test_is_account_dormant_custom_threshold(self):
        """Custom threshold works correctly."""
        # 30 days dormancy threshold
        assert is_account_dormant(30, 30) is True
        assert is_account_dormant(29, 30) is False

    def test_is_account_dormant_negative_threshold_raises(self):
        """Negative threshold raises ValueError."""
        with pytest.raises(ValueError, match="threshold_days must be non-negative"):
            is_account_dormant(100, -1)


# ============================================================
# History Tests
# ============================================================


class TestComputeBalanceTrend:
    """Tests for compute_balance_trend function."""

    def test_compute_balance_trend_improving(self):
        """Increasing balances return IMPROVING."""
        result = compute_balance_trend([100000, 150000, 200000])
        assert result == "IMPROVING"

    def test_compute_balance_trend_declining(self):
        """Decreasing balances return DECLINING."""
        result = compute_balance_trend([200000, 150000, 100000])
        assert result == "DECLINING"

    def test_compute_balance_trend_stable(self):
        """Flat balances return STABLE."""
        result = compute_balance_trend([100000, 100000, 100000])
        assert result == "STABLE"

    def test_compute_balance_trend_empty_list(self):
        """Empty list returns STABLE."""
        result = compute_balance_trend([])
        assert result == "STABLE"

    def test_compute_balance_trend_single_value(self):
        """Single value returns STABLE."""
        result = compute_balance_trend([100000])
        assert result == "STABLE"

    def test_compute_balance_trend_two_values(self):
        """Two values compared correctly."""
        assert compute_balance_trend([100000, 200000]) == "IMPROVING"
        assert compute_balance_trend([200000, 100000]) == "DECLINING"
        assert compute_balance_trend([100000, 100000]) == "STABLE"


class TestComputeBalanceVelocity:
    """Tests for compute_balance_velocity function."""

    def test_compute_balance_velocity_positive(self):
        """Positive velocity (growth)."""
        result = compute_balance_velocity(100000, 150000, 30)
        assert result == 1667  # 50000/30 = 1666.67 -> 1667 with ROUND_HALF_UP

    def test_compute_balance_velocity_negative(self):
        """Negative velocity (decline)."""
        result = compute_balance_velocity(150000, 100000, 30)
        assert result == -1667  # -50000/30 = -1666.67 -> -1667 with ROUND_HALF_UP

    def test_compute_balance_velocity_zero(self):
        """Zero change returns 0."""
        result = compute_balance_velocity(100000, 100000, 30)
        assert result == 0

    def test_compute_balance_velocity_zero_days_raises(self):
        """Zero days raises ValueError."""
        with pytest.raises(ValueError, match="days must be positive"):
            compute_balance_velocity(100000, 200000, 0)

    def test_compute_balance_velocity_negative_days_raises(self):
        """Negative days raises ValueError."""
        with pytest.raises(ValueError, match="days must be positive"):
            compute_balance_velocity(100000, 200000, -1)


# ============================================================
# Metrics Tests
# ============================================================


class TestComputeAccountMetrics:
    """Tests for compute_account_metrics function."""

    def test_compute_account_metrics_basic(self):
        """Basic metrics aggregation."""
        result = compute_account_metrics(
            current_balance_paise=150000,
            average_balance_paise=100000,
            cash_in_paise=200000,
            cash_out_paise=100000,
            days_since_activity=30,
        )

        assert result["current_balance_paise"] == 150000
        assert result["average_balance_paise"] == 100000
        assert result["net_flow_paise"] == 100000  # 200000 - 100000
        assert result["days_since_activity"] == 30
        assert result["is_dormant"] is False

    def test_compute_account_metrics_dormant(self):
        """Metrics with dormant account."""
        result = compute_account_metrics(
            current_balance_paise=100000,
            average_balance_paise=50000,
            cash_in_paise=100000,
            cash_out_paise=100000,
            days_since_activity=400,  # Beyond 365 threshold
        )

        assert result["is_dormant"] is True

    def test_compute_account_metrics_zero_balance(self):
        """Metrics with zero balance."""
        result = compute_account_metrics(
            current_balance_paise=0,
            average_balance_paise=0,
            cash_in_paise=0,
            cash_out_paise=0,
            days_since_activity=0,
        )

        assert result["current_balance_paise"] == 0
        assert result["average_balance_paise"] == 0
        assert result["net_flow_paise"] == 0
        assert result["is_dormant"] is False  # 0 days < 365 threshold

    def test_compute_account_metrics_negative_flow(self):
        """Metrics with negative net flow."""
        result = compute_account_metrics(
            current_balance_paise=50000,
            average_balance_paise=100000,
            cash_in_paise=50000,
            cash_out_paise=100000,
            days_since_activity=30,
        )

        assert result["net_flow_paise"] == -50000

    def test_compute_account_metrics_custom_threshold(self):
        """Metrics with custom dormancy threshold."""
        result = compute_account_metrics(
            current_balance_paise=100000,
            average_balance_paise=50000,
            cash_in_paise=100000,
            cash_out_paise=50000,
            days_since_activity=45,
            dormancy_threshold_days=30,  # Custom threshold
        )

        assert result["is_dormant"] is True

    def test_compute_account_metrics_all_keys_present(self):
        """All expected keys are present in result."""
        result = compute_account_metrics(
            current_balance_paise=100000,
            average_balance_paise=50000,
            cash_in_paise=100000,
            cash_out_paise=50000,
            days_since_activity=30,
        )

        expected_keys = [
            "current_balance_paise",
            "average_balance_paise",
            "net_flow_paise",
            "cash_flow_rate_paise",
            "days_since_activity",
            "is_dormant",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"


# ============================================================
# Integration Tests
# ============================================================


class TestAccountEngineIntegration:
    """Integration tests combining multiple functions."""

    def test_active_account_full_metrics(self):
        """Full metrics for active account."""
        # Simulate an active account with good metrics
        metrics = compute_account_metrics(
            current_balance_paise=500000,  # ₹5,000
            average_balance_paise=450000,
            cash_in_paise=600000,  # ₹6,000 credits
            cash_out_paise=500000,  # ₹5,000 debits
            days_since_activity=15,
        )

        assert metrics["is_dormant"] is False
        assert metrics["net_flow_paise"] == 100000  # ₹1,000 net inflow

    def test_dormant_account_full_metrics(self):
        """Full metrics for dormant account."""
        metrics = compute_account_metrics(
            current_balance_paise=100000,
            average_balance_paise=100000,
            cash_in_paise=100000,
            cash_out_paise=100000,
            days_since_activity=500,
        )

        assert metrics["is_dormant"] is True
        assert metrics["net_flow_paise"] == 0

    def test_workflow_balance_to_status(self):
        """Complete workflow: days calculation → status → metrics."""
        # Calculate days since activity
        days = compute_days_since_activity("2025-01-01", "2026-07-07")
        assert days > 365

        # Check dormancy
        assert is_account_dormant(days, 365) is True

        # Get status
        status = compute_account_status(True, "2025-01-01", "2026-07-07")
        assert status == "DORMANT"
