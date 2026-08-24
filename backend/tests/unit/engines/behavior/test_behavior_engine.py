"""Unit tests for the main behavior_engine.py file.

This test ensures the core behavior engine file is included in coverage
and exercises its key utility functions.
"""

import pytest
from src.engines.behaviour_engine.core import (
    _coefficient_of_variation,
    _moving_average,
    _normalize_score,
    get_cached_behavior_profile,
    invalidate_behavior_cache,
    set_cached_behavior_profile,
)


class TestBehaviorEngineCore:
    """Test the core behavior engine functions."""

    def test_normalize_score_bounds(self) -> None:
        """Test _normalize_score with various inputs."""
        # Test default bounds (0.0 to 1.0)
        assert _normalize_score(0.5) == 0.5
        assert _normalize_score(0.0) == 0.0
        assert _normalize_score(1.0) == 1.0

        # Test custom bounds
        assert _normalize_score(50, 0, 100) == 0.5
        assert _normalize_score(25, 0, 100) == 0.25
        assert _normalize_score(75, 0, 100) == 0.75

        # Test clamping
        assert _normalize_score(-10, 0, 100) == 0.0
        assert _normalize_score(110, 0, 100) == 1.0

        # Test equal min/max
        assert _normalize_score(50, 50, 50) == 0.5

    def test_coefficient_of_variation(self) -> None:
        """Test _coefficient_of_variation with various inputs."""
        # Test basic case
        assert _coefficient_of_variation([10, 20, 30]) == pytest.approx(
            0.408248, rel=1e-5
        )

        # Test single value
        assert _coefficient_of_variation([10]) == 0.0

        # Test empty list
        assert _coefficient_of_variation([]) == 0.0

        # Test zero mean
        assert _coefficient_of_variation([0, 0, 0]) == 0.0

    def test_moving_average(self) -> None:
        """Test _moving_average with various inputs."""
        # Test basic case
        assert _moving_average([1, 2, 3, 4, 5], 2) == [1.0, 1.5, 2.5, 3.5, 4.5]

        # Test empty list
        assert _moving_average([], 2) == []

        # Test window larger than list
        assert _moving_average([1, 2, 3], 5) == [1.0, 1.5, 2.0]

        # Test window size 1
        assert _moving_average([1, 2, 3], 1) == [1.0, 2.0, 3.0]

    def test_cache_functions(self) -> None:
        """Test the cache functions."""
        # Test cache operations
        invalidate_behavior_cache()

        # Test get/set cache
        test_profile = {"test": "data"}
        set_cached_behavior_profile("test_db", test_profile)
        cached_profile = get_cached_behavior_profile("test_db")
        assert cached_profile == test_profile

        # Test cache invalidation
        invalidate_behavior_cache()
        assert get_cached_behavior_profile("test_db") is None

    def test_date_parsing(self) -> None:
        """Test the _parse_date function."""
        from src.engines.behaviour_engine.core import _parse_date

        # Test various date formats
        assert _parse_date("2023-01-15") is not None
        assert _parse_date("15/01/2023") is not None
        assert _parse_date("15-01-2023") is not None
        assert _parse_date("15/01/23") is not None
        assert _parse_date("15 01 2023") is None  # Not supported format

        # Test empty string
        assert _parse_date("") is None
        assert _parse_date(None) is None

    def test_normalize_score_edge_cases(self) -> None:
        """Test _normalize_score with boundary and edge cases."""
        from src.engines.behaviour_engine.core import _normalize_score

        # Negative values clamp to 0
        assert _normalize_score(-100, 0, 100) == 0.0
        assert _normalize_score(-1, 0, 10) == 0.0

        # Values above max clamp to 1
        assert _normalize_score(200, 0, 100) == 1.0
        assert _normalize_score(11, 0, 10) == 1.0

        # Exact boundaries
        assert _normalize_score(0, 0, 100) == 0.0
        assert _normalize_score(100, 0, 100) == 1.0

        # Custom bounds
        assert _normalize_score(50, -50, 150) == 0.5
        assert _normalize_score(-50, -50, 150) == 0.0
        assert _normalize_score(150, -50, 150) == 1.0

        # Equal min/max returns midpoint
        assert _normalize_score(42, 7, 7) == 0.5

    def test_coefficient_of_variation_edge_cases(self) -> None:
        """Test _coefficient_of_variation with edge cases."""
        from src.engines.behaviour_engine.core import _coefficient_of_variation

        # Empty list
        assert _coefficient_of_variation([]) == 0.0

        # Single value
        assert _coefficient_of_variation([42]) == 0.0

        # All zeros
        assert _coefficient_of_variation([0, 0, 0, 0]) == 0.0

        # Two identical values (zero variance)
        assert _coefficient_of_variation([10, 10]) == 0.0

        # Two different values
        result = _coefficient_of_variation([10, 30])
        # std = 10, mean = 20, CV = 0.5
        assert result == pytest.approx(0.5, rel=1e-5)

        # Large spread - manual calculation
        # values = [1, 100], mean = 50.5, variance = ((1-50.5)^2 + (100-50.5)^2)/2 = 2450.25
        # std = sqrt(2450.25) = 49.5, CV = 49.5/50.5 = 0.9802
        result = _coefficient_of_variation([1, 100])
        assert result == pytest.approx(0.9802, rel=1e-4)

    def test_moving_average_edge_cases(self) -> None:
        """Test _moving_average with edge cases."""
        from src.engines.behaviour_engine.core import _moving_average

        # Empty list
        assert _moving_average([], 5) == []

        # Window larger than data
        assert _moving_average([10, 20], 5) == [10.0, 15.0]

        # Window of 1 (no smoothing)
        assert _moving_average([1, 2, 3, 4], 1) == [1.0, 2.0, 3.0, 4.0]

        # Single element
        assert _moving_average([42], 7) == [42.0]

        # Negative window treated as empty
        assert _moving_average([1, 2, 3], -1) == []

    def test_get_daily_spending_data(self) -> None:
        """Test daily spending aggregation."""
        from src.engines.behaviour_engine.core import _get_daily_spending_data

        transactions = [
            {"type": "debit", "date_iso": "2025-01-15", "amount_paise": 100000},
            {"type": "debit", "date_iso": "2025-01-15", "amount_paise": 50000},
            {"type": "debit", "date_iso": "2025-01-16", "amount_paise": 75000},
            {
                "type": "credit",
                "date_iso": "2025-01-15",
                "amount_paise": 500000,
            },  # Should be ignored
            {
                "type": "debit",
                "date_iso": "2025-01-14",
                "amount_paise": 10000,
            },  # Before cutoff
        ]

        result = _get_daily_spending_data(transactions, "2025-01-15")
        assert result["2025-01-15"] == 150000.0
        assert result["2025-01-16"] == 75000.0
        assert "2025-01-14" not in result

    def test_get_monthly_category_spending(self) -> None:
        """Test monthly category spending aggregation."""
        from src.engines.behaviour_engine.core import (
            _get_monthly_category_spending_data,
        )

        transactions = [
            {
                "type": "debit",
                "date_iso": "2025-01-15",
                "category": "Food",
                "amount_paise": 100000,
            },
            {
                "type": "debit",
                "date_iso": "2025-01-16",
                "category": "Transport",
                "amount_paise": 50000,
            },
            {
                "type": "debit",
                "date_iso": "2025-02-01",
                "category": "Food",
                "amount_paise": 80000,
            },
            {
                "type": "credit",
                "date_iso": "2025-01-15",
                "category": "Salary",
                "amount_paise": 500000,
            },
        ]

        result = _get_monthly_category_spending_data(transactions, "2025-01-01")
        assert result["2025-01"]["Food"] == 100000.0
        assert result["2025-01"]["Transport"] == 50000.0
        assert result["2025-02"]["Food"] == 80000.0

    def test_get_transaction_stats(self) -> None:
        """Test transaction statistics computation."""
        from src.engines.behaviour_engine.core import _get_transaction_stats_data

        transactions = [
            {"type": "debit", "date_iso": "2025-01-15", "amount_paise": 100000},
            {
                "type": "debit",
                "date_iso": "2025-01-16",
                "amount_paise": 5000,
            },  # micro txn
            {"type": "credit", "date_iso": "2025-01-15", "amount_paise": 500000},
            {
                "type": "debit",
                "date_iso": "2025-01-14",
                "amount_paise": 50000,
            },  # Before cutoff
        ]

        result = _get_transaction_stats_data(transactions, "2025-01-15")
        assert result["total_count"] == 3
        assert result["debit_count"] == 2
        assert result["credit_count"] == 1
        assert result["micro_txn_count"] == 1  # 5000 < 50000
        assert result["total_debit_paise"] == 105000
        assert result["total_credit_paise"] == 500000

    def test_get_transactions_90_days(self) -> None:
        """Test 90-day transaction filtering."""
        from datetime import datetime, timedelta

        from src.engines.behaviour_engine.core import _get_transactions_90_days

        now = datetime.now()
        recent = now - timedelta(days=30)
        old = now - timedelta(days=120)

        transactions = [
            {"date_iso": recent.strftime("%Y-%m-%d"), "amount_paise": 100000},
            {"date_iso": old.strftime("%Y-%m-%d"), "amount_paise": 50000},
        ]

        result = _get_transactions_90_days(transactions)
        assert len(result) == 1
        assert result[0]["amount_paise"] == 100000

    def test_get_recent_transactions(self) -> None:
        """Test recent transaction selection and ordering."""
        from src.engines.behaviour_engine.core import _get_recent_transactions

        transactions = [
            {"date_iso": "2025-01-10", "amount_paise": 100000},
            {"date_iso": "2025-01-08", "amount_paise": 200000},
            {"date_iso": "2025-01-05", "amount_paise": 300000},
            {"date_iso": "2025-01-01", "amount_paise": 400000},
        ]

        # Get 2 most recent
        result = _get_recent_transactions(transactions, limit=2)
        assert len(result) == 2
        # Should be sorted ascending
        assert result[0]["date_iso"] == "2025-01-08"
        assert result[1]["date_iso"] == "2025-01-10"

    def test_compute_temporal_patterns_empty(self) -> None:
        """Test temporal patterns with empty input."""
        from src.engines.behaviour_engine.core import _compute_temporal_patterns

        result = _compute_temporal_patterns([])
        assert result["trend"] == 0.0
        assert result["seasonality"] == 0.0
        assert result["daily_spending"] == {}

    def test_compute_temporal_patterns_single_day(self) -> None:
        """Test temporal patterns with single day of data."""
        from src.engines.behaviour_engine.core import _compute_temporal_patterns

        transactions = [
            {"type": "debit", "date_iso": "2025-01-15", "amount_paise": 100000},
        ]

        result = _compute_temporal_patterns(transactions)
        assert result["trend"] == 0.0  # Not enough data for trend
        assert isinstance(result["daily_spending"], dict)

    def test_compute_loss_aversion_empty(self) -> None:
        """Test loss aversion with empty transactions."""
        from src.engines.behaviour_engine.core import _compute_loss_aversion_index

        result = _compute_loss_aversion_index([])
        assert result["score"] == 0.5
        assert result["post_income_velocity"] == 0.0

    def test_compute_loss_aversion_no_credits(self) -> None:
        """Test loss aversion with only debits."""
        from src.engines.behaviour_engine.core import _compute_loss_aversion_index

        transactions = [
            {"type": "debit", "date_iso": "2025-01-15", "amount_paise": 100000},
        ]

        result = _compute_loss_aversion_index(transactions)
        assert result["score"] == 0.5

    def test_compute_impulsivity_empty(self) -> None:
        """Test impulsivity with empty transactions."""
        from src.engines.behaviour_engine.core import _compute_impulsivity_score

        result = _compute_impulsivity_score([])
        assert result["score"] == 0.5

    def test_compute_impulsivity_only_credits(self) -> None:
        """Test impulsivity with only credits."""
        from src.engines.behaviour_engine.core import _compute_impulsivity_score

        transactions = [
            {"type": "credit", "date_iso": "2025-01-15", "amount_paise": 500000},
        ]

        result = _compute_impulsivity_score(transactions)
        assert result["score"] == 0.5

    def test_compute_habit_stability_empty(self) -> None:
        """Test habit stability with empty transactions."""
        from src.engines.behaviour_engine.core import _compute_habit_stability_score

        result = _compute_habit_stability_score([])
        assert result["score"] == 0.5
        assert result["category_cv"] == 0.0

    def test_compute_financial_stress_empty(self) -> None:
        """Test financial stress index with empty transactions."""
        from src.engines.behaviour_engine.core import _compute_financial_stress_index

        result = _compute_financial_stress_index([])
        assert isinstance(result, dict)
        assert "score" in result
