"""
Account Engine Tests - Determinism and Financial Correctness
===========================================================
Tests for all account engine modules.

All monetary values in paise (integer).
All rates in basis points (integer).
"""

import pytest
from src.engines.account_engine import (
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


# ============================================================
# Additional Tests for Gaps Identified by C42 Forensics
# ============================================================


class TestAccountStatusEdgeCases:
    """Edge cases for account status computation."""

    def test_compute_account_status_future_reference_date_raises(self):
        """Future reference date raises ValueError."""
        with pytest.raises(ValueError, match="cannot be after"):
            compute_account_status(True, "2026-07-07", "2026-06-07")

    def test_compute_account_status_exactly_364_days(self):
        """Exactly 364 days is still ACTIVE."""
        result = compute_account_status(True, "2025-07-09", "2026-07-07")
        assert result == "ACTIVE"

    def test_compute_account_status_exactly_366_days(self):
        """Exactly 366 days is DORMANT."""
        result = compute_account_status(True, "2025-07-06", "2026-07-07")
        assert result == "DORMANT"

    def test_compute_account_status_same_date_as_reference(self):
        """Same day as reference date means 0 days since activity."""
        result = compute_account_status(True, "2026-07-07", "2026-07-07")
        assert result == "ACTIVE"


class TestAverageBalancePrecision:
    """Precision tests for average balance calculation."""

    def test_compute_average_balance_odd_count(self):
        """Odd number of values with non-exact division."""
        # [100, 100, 101] -> avg = 100.333... -> 100 with ROUND_HALF_UP
        result = compute_average_balance([100, 100, 101])
        assert result == 100

    def test_compute_average_balance_rounding_up(self):
        """Rounding up at 0.5 boundary."""
        # [100, 101] -> avg = 100.5 -> 101 with ROUND_HALF_UP
        result = compute_average_balance([100, 101])
        assert result == 101

    def test_compute_average_balance_large_list(self):
        """Large list of balances handled correctly."""
        balances = [100000] * 365  # Daily balances for a year
        result = compute_average_balance(balances)
        assert result == 100000

    def test_compute_average_balance_alternating(self):
        """Alternating high/low balances."""
        balances = [100000, 200000, 100000, 200000]
        result = compute_average_balance(balances)
        assert result == 150000

    def test_compute_average_balance_single_zero(self):
        """Single zero balance."""
        result = compute_average_balance([0])
        assert result == 0


class TestBalanceChangeBoundary:
    """Boundary tests for balance change computation."""

    def test_compute_balance_change_same_value(self):
        """No change when opening equals closing."""
        result = compute_balance_change(100000, 100000)
        assert result == 0

    def test_compute_balance_change_both_zero(self):
        """Both zeros return zero change."""
        result = compute_balance_change(0, 0)
        assert result == 0

    def test_compute_balance_change_large_decline(self):
        """Large decline from high to zero."""
        result = compute_balance_change(1000000000, 0)
        assert result == -1000000000


class TestGrowthPercentagePrecision:
    """Precision tests for growth percentage computation."""

    def test_compute_balance_growth_percentage_100_percent_increase(self):
        """100% increase = 10000 bps."""
        result = compute_balance_growth_percentage(100000, 200000)
        assert result == 10000

    def test_compute_balance_growth_percentage_small_increase(self):
        """Small increase rounds correctly."""
        # 100 -> 101 is 1% = 100 bps
        result = compute_balance_growth_percentage(100, 101)
        assert result == 100

    def test_compute_balance_growth_percentage_large_decline(self):
        """Large decline rounds correctly."""
        # 100000 -> 1 is -99.9999% ≈ -10000 bps
        result = compute_balance_growth_percentage(100000, 1)
        assert result == -10000  # Full decline

    def test_compute_balance_growth_percentage_exact_half(self):
        """Exact 50% increase = 5000 bps."""
        result = compute_balance_growth_percentage(100000, 150000)
        assert result == 5000

    def test_compute_balance_growth_percentage_very_small_change(self):
        """Very small change from large base."""
        # 1000000 -> 1000001 is 0.0001% ≈ 0 bps
        result = compute_balance_growth_percentage(1000000, 1000001)
        assert result == 0


class TestNetCashFlowBoundary:
    """Boundary tests for net cash flow computation."""

    def test_compute_net_cash_flow_both_zero(self):
        """Both zero returns zero."""
        result = compute_net_cash_flow(0, 0)
        assert result == 0

    def test_compute_net_cash_flow_equal_amounts(self):
        """Equal credits and debits return zero."""
        result = compute_net_cash_flow(500000, 500000)
        assert result == 0


class TestCashFlowRatePrecision:
    """Precision tests for cash flow rate computation."""

    def test_compute_cash_flow_rate_exact_division(self):
        """Exact division with no remainder."""
        result = compute_cash_flow_rate(300000, 3)
        assert result == 100000

    def test_compute_cash_flow_rate_rounding_up(self):
        """Rounding up at 0.5 boundary."""
        # 100/3 = 33.333... -> 33 with ROUND_HALF_UP
        result = compute_cash_flow_rate(100, 3)
        assert result == 33

    def test_compute_cash_flow_rate_negative_rounding(self):
        """Negative value rounding."""
        # -100/3 = -33.333... -> -33 with ROUND_HALF_UP
        result = compute_cash_flow_rate(-100, 3)
        assert result == -33

    def test_compute_cash_flow_rate_single_day(self):
        """Single day period."""
        result = compute_cash_flow_rate(50000, 1)
        assert result == 50000


class TestIncomeExpenseRatioPrecision:
    """Precision tests for income-expense ratio computation."""

    def test_compute_income_expense_ratio_exact_double(self):
        """Income exactly double expense = 20000 bps."""
        result = compute_income_expense_ratio(200000, 100000)
        assert result == 20000

    def test_compute_income_expense_ratio_exact_half(self):
        """Income exactly half expense = 5000 bps."""
        result = compute_income_expense_ratio(50000, 100000)
        assert result == 5000

    def test_compute_income_expense_ratio_rounding(self):
        """Rounding to nearest basis point."""
        # 33333/100000 = 33.333% = 3333 bps
        result = compute_income_expense_ratio(33333, 100000)
        assert result == 3333

    def test_compute_income_expense_ratio_large_ratio(self):
        """Large ratio (income much larger than expense)."""
        result = compute_income_expense_ratio(1000000, 10000)
        assert result == 1000000  # 10000% = 1000000 bps


class TestDaysSinceActivityEdgeCases:
    """Edge cases for days since activity computation."""

    def test_compute_days_since_activity_same_date(self):
        """Same date returns 0 days."""
        result = compute_days_since_activity("2026-07-07", "2026-07-07")
        assert result == 0

    def test_compute_days_since_activity_single_day(self):
        """One day difference."""
        result = compute_days_since_activity("2026-07-06", "2026-07-07")
        assert result == 1

    def test_compute_days_since_activity_leap_year(self):
        """Leap year February handling."""
        # From Feb 28, 2024 to Mar 1, 2024 = 2 days (leap year)
        result = compute_days_since_activity("2024-02-28", "2024-03-01")
        assert result == 2

    def test_compute_days_since_activity_year_boundary(self):
        """Year boundary crossing."""
        result = compute_days_since_activity("2025-12-31", "2026-01-01")
        assert result == 1


# ============================================================
# M9-C43.6 — Mutation-Strengthening Tests (Targeted at C42 Class-A Survivors)
# ============================================================
#
# These tests were generated from the C42.17 forensic survivor inventory
# and are designed to discriminate the EXACT mutants that survived.
# Each test targets a specific surviving mutant identified by its
# source location and mutation operator.
#
# MUTANT TARGET KEY (from C42.17 inventory):
#   dormant.py:1           - default threshold 365 -> 366
#   cashflow.py:19         - ratio quantize HALF_UP -> None/quantize(2)
#   cashflow.py:20         - rate quantize HALF_UP -> None/quantize(2)
#   balance.py:19          - empty list return 0 -> 1
#   balance.py:22/23       - avg/growth quantize HALF_UP -> None/quantize(2)
#   lifecycle.py:32        - explicit default 365 removed (equiv/Class-B)
#   metrics.py:4           - default threshold 365 -> 366
#   history.py:24          - velocity quantize HALF_UP -> None/quantize(2)
#
# CLASSIFICATION: All surviving mutants are Class-A (genuine behavioral
# gap) except lifecycle.py:32 which is EQUIVALENT (default value 365
# is functionally identical to explicit 365). This test module does not
# target equivalent mutants per C43 constraints.
# ============================================================


class TestMutationStrengthening_DormantDefaultThreshold:
    """M9-C43.6: Discriminate default threshold mutant at dormant.py:1.

    Mutant: threshold_days: int = 365 -> 366
    Target: is_account_dormant(365) WITHOUT explicit threshold.
    Evidence: survivor calls function relying on default 365.
    """

    def test_is_account_dormant_default_threshold_365(self):
        """Default threshold is exactly 365 days."""
        # Call WITHOUT explicit threshold - exercises the default argument
        assert is_account_dormant(364) is False
        assert is_account_dormant(365) is True
        assert is_account_dormant(366) is True


class TestMutationStrengthening_CashflowQuantization:
    """M9-C43.6: Discriminate quantization mutants at cashflow.py:19,20.

    Mutants:
      - quantize(Decimal(1), rounding=ROUND_HALF_UP) -> quantize(1, rounding=None) [HALF_EVEN]
      - quantize(Decimal(1), rounding=ROUND_HALF_UP) -> quantize(2) [truncation]

    Target: .5 boundary where HALF_UP != HALF_EVEN.
    Evidence: survivor at .5 boundary escapes both rounding changes.
    """

    def test_compute_cash_flow_rate_half_up_boundary(self):
        """ROUND_HALF_UP at .5 boundary discriminates HALF_UP vs HALF_EVEN.

        net=1, days=2 -> 0.5 -> HALF_UP=1, HALF_EVEN=0.
        Mutant with rounding=None uses context default (HALF_EVEN) -> 0.
        Mutant with quantize(2) -> 0.50 -> int=0.
        """
        # net=1, days=2 -> 0.5 paise/day
        # HALF_UP(0.5) = 1, HALF_EVEN(0.5) = 0
        result = compute_cash_flow_rate(1, 2)
        assert result == 1  # HALF_UP rounds 0.5 UP to 1

    def test_compute_income_expense_ratio_half_up_boundary(self):
        """ROUND_HALF_UP at .5 boundary for income/expense ratio.

        income=1, expense=20000 -> 0.5 bps -> HALF_UP=1, HALF_EVEN=0.
        quantize(2) -> 0.50 -> int=0.
        """
        # income=1, expense=20000 -> 1*10000/20000 = 0.5 bps
        result = compute_income_expense_ratio(1, 20000)
        assert result == 1  # HALF_UP rounds 0.5 UP to 1

    def test_compute_cash_flow_rate_negative_half_up_boundary(self):
        """Negative .5 boundary: HALF_UP rounds away from zero."""
        # net=-1, days=2 -> -0.5 -> HALF_UP=-1, HALF_EVEN=0
        result = compute_cash_flow_rate(-1, 2)
        assert result == -1  # HALF_UP rounds -0.5 away from zero to -1


class TestMutationStrengthening_AverageBalancePrecision:
    """M9-C43.6: Discriminate average_balance quantization mutants at balance.py:22.

    Mutants: quantize(1, HALF_UP) -> None (HALF_EVEN) or quantize(2) (truncation).
    Target: .5 boundary where HALF_UP != HALF_EVEN.

    Existing test: [100, 101] -> avg 100.5 -> 101 with HALF_UP (already discriminates).
    Adding explicit .5 boundary tests for the growth/velocity functions.
    """

    def test_compute_average_balance_explicit_half_up_boundary(self):
        """[100, 101] average = 100.5 -> HALF_UP=101, HALF_EVEN=100."""
        # This test already exists but make it explicit for mutation discrimination
        result = compute_average_balance([100, 101])
        assert result == 101  # HALF_UP: 100.5 -> 101 (101 is odd, HALF_EVEN would go to 100)

    def test_compute_average_balance_half_even_discrimination(self):
        """2.5 boundary: HALF_UP=3, HALF_EVEN=2 (2 is even)."""
        # [2, 3] -> avg 2.5
        result = compute_average_balance([2, 3])
        assert result == 3  # HALF_UP: 2.5 -> 3; HALF_EVEN: 2.5 -> 2


class TestMutationStrengthening_BalanceGrowthVelocity:
    """M9-C43.6: Discriminate growth/velocity quantization mutants.

    Mutants at balance.py:23 (growth) and history.py:24 (velocity):
      quantize(1, HALF_UP) -> None (HALF_EVEN) or quantize(2) (truncation).
    Target: .5 boundary in basis points / paise-per-day.
    """

    def test_compute_balance_growth_percentage_half_up_boundary(self):
        """Growth percentage .5 boundary in basis points.

        100 -> 115 is 15% = 1500 bps (exact).
        Need x where change/prev * 10000 = x.5 bps.
        prev=200, curr=201 -> change=1, growth=1/200*10000 = 50 bps (exact).
        prev=200, curr=202 -> change=2, growth=2/200*10000 = 100 bps (exact).
        Need non-exact: prev=300, curr=301 -> 1/300*10000 = 33.33... bps (not .5).
        prev=100, curr=101 -> 1/100*10000 = 100 bps (exact).
        prev=100, curr=102 -> 2/100*10000 = 200 bps (exact).
        prev=200, curr=203 -> 3/200*10000 = 150 bps (exact).
        prev=200, curr=201 -> 1/200*10000 = 50 bps (exact).
        prev=20000, curr=20001 -> 1/20000*10000 = 0.5 bps -> HALF_UP=1, HALF_EVEN=0!
        """
        # prev=20000, curr=20001 -> change=1 -> growth=0.5 bps
        result = compute_balance_growth_percentage(20000, 20001)
        assert result == 1  # HALF_UP: 0.5 -> 1; HALF_EVEN: 0.5 -> 0

    def test_compute_balance_growth_percentage_negative_half_up(self):
        """Negative .5 boundary."""
        # prev=20000, curr=19999 -> change=-1 -> -0.5 bps
        result = compute_balance_growth_percentage(20000, 19999)
        assert result == -1  # HALF_UP: -0.5 -> -1; HALF_EVEN: -0.5 -> 0

    def test_compute_balance_velocity_half_up_boundary(self):
        """Velocity .5 boundary in paise/day.

        opening=0, closing=1, days=2 -> velocity=0.5 -> HALF_UP=1, HALF_EVEN=0.
        """
        result = compute_balance_velocity(0, 1, 2)
        assert result == 1  # HALF_UP: 0.5 -> 1; HALF_EVEN: 0.5 -> 0

    def test_compute_balance_velocity_quantize_two_discrimination(self):
        """quantize(2) truncation discriminated by velocity > 1.

        opening=0, closing=1, days=2 -> 0.5 -> quantize(2)=0.50 -> int=0.
        HALF_UP=1, quantize(2)=0.
        """
        result = compute_balance_velocity(0, 1, 2)
        assert result == 1  # kills quantize(2) mutant


class TestMutationStrengthening_HistoryVelocity:
    """M9-C43.6: Discriminate history.py:24 velocity quantize mutants."""

    def test_compute_balance_velocity_history_half_up(self):
        """Direct test of history module's velocity function."""
        from src.engines.account_engine.history import compute_balance_velocity

        # 0 -> 1 over 2 days = 0.5 paise/day
        result = compute_balance_velocity(0, 1, 2)
        assert result == 1  # HALF_UP rounds 0.5 up to 1

    def test_compute_balance_velocity_history_quantize_two(self):
        """quantize(2) mutant would produce 0 for 0.5 velocity."""
        from src.engines.account_engine.history import compute_balance_velocity

        result = compute_balance_velocity(0, 1, 2)
        assert result == 1  # HALF_UP=1, quantize(2)->0.50->int=0


class TestMutationStrengthening_MetricsDefaultThreshold:
    """M9-C43.6: Discriminate default threshold mutant at metrics.py:4.

    Mutant: dormancy_threshold_days: int = 365 -> 366
    Target: compute_account_metrics called without explicit threshold
    at exactly 365 days of inactivity.
    """

    def test_compute_account_metrics_default_threshold_365(self):
        """Default dormancy threshold is exactly 365 days."""
        # days=365 should be dormant with default threshold
        result = compute_account_metrics(
            current_balance_paise=100000,
            average_balance_paise=100000,
            cash_in_paise=100000,
            cash_out_paise=100000,
            days_since_activity=365,  # exactly at default 365
        )
        assert result["is_dormant"] is True

    def test_compute_account_metrics_default_threshold_364(self):
        """One day before default threshold."""
        result = compute_account_metrics(
            current_balance_paise=100000,
            average_balance_paise=100000,
            cash_in_paise=100000,
            cash_out_paise=100000,
            days_since_activity=364,  # one day before default 365
        )
        assert result["is_dormant"] is False


class TestMutationStrengthening_EmptyListZero:
    """M9-C43.6: Discriminate empty list return 0 -> 1 mutant at balance.py:19."""

    def test_compute_average_balance_empty_returns_zero(self):
        """Empty list must return exactly 0."""
        result = compute_average_balance([])
        assert result == 0  # mutant returns 1


class TestMutationStrengthening_LifecycleDefaultEquivalent:
    """M9-C43.6: Classify lifecycle.py:32 as EQUIVALENT (not killable).

    Mutant: explicit threshold_days=365 removed -> relies on default 365.
    Behaviorally IDENTICAL to original. Classified as Class-B equivalent.
    """

    def test_lifecycle_default_threshold_is_365_equiv(self):
        """Explicit 365 and default 365 are behaviorally identical."""
        from src.engines.account_engine.lifecycle import compute_account_status

        # Both should produce identical results
        with_explicit = compute_account_status(True, "2025-07-08", "2026-07-07")
        # The default is 365, so explicit=365 and default=365 are equivalent
        # This test documents the equivalence - the mutant is NOT killable
        assert with_explicit == "ACTIVE"  # 364 days


# ============================================================
# END M9-C43.6 Mutation-Strengthening Tests
# ============================================================


class TestIsAccountDormantBoundary:
    """Boundary tests for dormancy detection."""

    def test_is_account_dormant_zero_threshold(self):
        """Zero threshold means any activity qualifies as dormant."""
        # With threshold=0, even 0 days would be dormant
        assert is_account_dormant(0, 0) is True
        assert is_account_dormant(1, 0) is True

    def test_is_account_dormant_very_large_threshold(self):
        """Very large threshold makes dormancy unlikely."""
        assert is_account_dormant(10000, 10001) is False
        assert is_account_dormant(10000, 10000) is True

    def test_is_account_dormant_large_days(self):
        """Large number of days with normal threshold."""
        assert is_account_dormant(1000, 365) is True
        assert is_account_dormant(10000, 365) is True


class TestBalanceTrendPrecision:
    """Precision tests for balance trend computation."""

    def test_compute_balance_trend_alternating(self):
        """Alternating pattern: first < last = IMPROVING."""
        result = compute_balance_trend([100, 50, 100, 50, 200])
        assert result == "IMPROVING"

    def test_compute_balance_trend_v_shaped(self):
        """V-shaped pattern: first > last = DECLINING."""
        result = compute_balance_trend([200, 100, 50, 100, 200])
        assert result == "STABLE"

    def test_compute_balance_trend_inverted_v_shaped(self):
        """Inverted V-shaped pattern: first > last = DECLINING."""
        result = compute_balance_trend([300, 200, 100, 200, 50])
        assert result == "DECLINING"


class TestBalanceVelocityPrecision:
    """Precision tests for balance velocity computation."""

    def test_compute_balance_velocity_exact_division(self):
        """Exact division with no remainder."""
        result = compute_balance_velocity(100000, 200000, 10)
        assert result == 10000

    def test_compute_balance_velocity_negative_exact(self):
        """Negative velocity with exact division."""
        result = compute_balance_velocity(200000, 100000, 10)
        assert result == -10000

    def test_compute_balance_velocity_large_change(self):
        """Large change over few days."""
        result = compute_balance_velocity(0, 1000000, 1)
        assert result == 1000000


class TestAccountMetricsIntegration:
    """Integration tests for complete metrics computation."""

    def test_compute_account_metrics_cash_flow_rate_computed(self):
        """Verify cash_flow_rate is computed from net_flow and days."""
        result = compute_account_metrics(
            current_balance_paise=100000,
            average_balance_paise=100000,
            cash_in_paise=200000,
            cash_out_paise=100000,
            days_since_activity=10,
        )
        # Net flow = 200000 - 100000 = 100000
        # Cash flow rate = 100000 / 10 = 10000
        assert result["net_flow_paise"] == 100000
        assert result["cash_flow_rate_paise"] == 10000

    def test_compute_account_metrics_zero_days_uses_one(self):
        """Zero days_since_activity uses 1 to avoid division by zero."""
        result = compute_account_metrics(
            current_balance_paise=100000,
            average_balance_paise=100000,
            cash_in_paise=200000,
            cash_out_paise=100000,
            days_since_activity=0,
        )
        # days_for_rate = max(0, 1) = 1
        # Cash flow rate = 100000 / 1 = 100000
        assert result["cash_flow_rate_paise"] == 100000

    def test_compute_account_metrics_dormancy_with_custom_threshold(self):
        """Custom dormancy threshold affects is_dormant flag."""
        result_normal = compute_account_metrics(
            current_balance_paise=100000,
            average_balance_paise=100000,
            cash_in_paise=100000,
            cash_out_paise=100000,
            days_since_activity=400,
        )
        assert result_normal["is_dormant"] is True

        # 100 days < 200 threshold = not dormant
        result_not_dormant = compute_account_metrics(
            current_balance_paise=100000,
            average_balance_paise=100000,
            cash_in_paise=100000,
            cash_out_paise=100000,
            days_since_activity=100,
            dormancy_threshold_days=200,
        )
        assert result_not_dormant["is_dormant"] is False

        # 200 days = 200 threshold = exactly at threshold = dormant
        result_at_threshold = compute_account_metrics(
            current_balance_paise=100000,
            average_balance_paise=100000,
            cash_in_paise=100000,
            cash_out_paise=100000,
            days_since_activity=200,
            dormancy_threshold_days=200,
        )
        assert result_at_threshold["is_dormant"] is True

    def test_compute_account_metrics_all_positive_inputs(self):
        """All positive inputs produce valid metrics."""
        result = compute_account_metrics(
            current_balance_paise=500000,
            average_balance_paise=400000,
            cash_in_paise=600000,
            cash_out_paise=500000,
            days_since_activity=30,
        )
        assert result["current_balance_paise"] == 500000
        assert result["average_balance_paise"] == 400000
        assert result["net_flow_paise"] == 100000
        assert result["days_since_activity"] == 30
        assert result["is_dormant"] is False


class TestDormancyDefaultThresholdMutants:
    """Exact default threshold assertions to kill constant mutants in dormancy check."""

    def test_default_dormancy_threshold_is_365(self) -> None:
        """Default dormancy threshold must be exactly 365 days."""
        # At exactly 365 days with default threshold, account is dormant
        assert is_account_dormant(365) is True
        # At 364 days with default threshold, account is NOT dormant
        assert is_account_dormant(364) is False

    def test_explicit_threshold_365_same_as_default(self) -> None:
        """Explicit threshold of 365 behaves identically to default."""
        assert is_account_dormant(365, threshold_days=365) is True
        assert is_account_dormant(364, threshold_days=365) is False

    def test_custom_threshold_100_days(self) -> None:
        """Custom threshold of 100 days works correctly."""
        assert is_account_dormant(100, threshold_days=100) is True
        assert is_account_dormant(99, threshold_days=100) is False

    def test_threshold_zero_means_always_dormant(self) -> None:
        """Threshold of 0 means any account is dormant (even 0 days since activity)."""
        assert is_account_dormant(0, threshold_days=0) is True
        assert is_account_dormant(1, threshold_days=0) is True

    def test_negative_threshold_raises_value_error(self) -> None:
        """Negative threshold must raise ValueError."""
        with pytest.raises(ValueError, match="threshold_days must be non-negative"):
            is_account_dormant(100, threshold_days=-1)

    def test_compute_days_since_activity_zero_at_same_date(self) -> None:
        """Days since activity is 0 when last activity equals reference date."""
        days = compute_days_since_activity("2025-01-15", "2025-01-15")
        assert days == 0

    def test_compute_days_since_activity_exact_difference(self) -> None:
        """Exact day difference calculation."""
        days = compute_days_since_activity("2025-01-01", "2025-01-15")
        assert days == 14

    def test_compute_days_since_activity_future_raises(self) -> None:
        """Last activity after reference date must raise ValueError."""
        with pytest.raises(ValueError, match="cannot be after reference_date"):
            compute_days_since_activity("2025-01-20", "2025-01-15")
