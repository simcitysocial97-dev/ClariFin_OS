"""Tests for Behaviour Engine — Temporal pattern analysis.

Direct unit tests for src/engines/behaviour_engine/temporal.py.
These tests exercise the previously-0%-coverage module so that mutation
testing can measure behavioral effectiveness instead of reporting no_tests.

All monetary values are integers in paise (₹1.00 = 100 paise).
"""


from src.engines.behaviour_engine.temporal import (
    _coefficient_of_variation,
    _moving_average,
    compute_daily_spending,
    compute_residual_volatility,
    compute_seasonality,
    compute_temporal_patterns,
    compute_trend,
    compute_weekly_pattern,
)

# ============================================================
# _coefficient_of_variation
# ============================================================


def test_cov_empty():
    assert _coefficient_of_variation([]) == 0.0


def test_cov_single():
    assert _coefficient_of_variation([5.0]) == 0.0


def test_cov_zero_mean():
    assert _coefficient_of_variation([0.0, 0.0, 0.0]) == 0.0


def test_cov_normal():
    # values [1, 2, 3, 4] mean=2.5 var=1.25 std=1.118 cv=0.4472
    result = _coefficient_of_variation([1.0, 2.0, 3.0, 4.0])
    assert abs(result - 0.4472) < 0.001


# ============================================================
# _moving_average
# ============================================================


def test_moving_average_empty():
    assert _moving_average([]) == []


def test_moving_average_zero_window():
    assert _moving_average([1.0, 2.0], window=0) == []


def test_moving_average_normal():
    result = _moving_average([1.0, 2.0, 3.0, 4.0], window=2)
    assert result == [1.0, 1.5, 2.5, 3.5]


# ============================================================
# compute_daily_spending
# ============================================================


def test_daily_spending_debits_only():
    transactions = [
        {"date_iso": "2025-01-01", "amount_paise": 10000, "type": "debit"},
        {"date_iso": "2025-01-01", "amount_paise": 5000, "type": "debit"},
        {"date_iso": "2025-01-02", "amount_paise": 20000, "type": "debit"},
    ]
    result = compute_daily_spending(transactions)
    assert result == {"2025-01-01": 15000.0, "2025-01-02": 20000.0}


def test_daily_spending_ignores_credits():
    transactions = [
        {"date_iso": "2025-01-01", "amount_paise": 10000, "type": "credit"},
    ]
    result = compute_daily_spending(transactions)
    assert result == {}


def test_daily_spending_missing_date():
    transactions = [
        {"amount_paise": 10000, "type": "debit"},
    ]
    result = compute_daily_spending(transactions)
    assert result == {}


def test_daily_spending_empty():
    assert compute_daily_spending([]) == {}


# ============================================================
# compute_weekly_pattern
# ============================================================


def test_weekly_pattern_normal():
    daily = {
        "2025-01-04": 100.0,  # Saturday
        "2025-01-05": 200.0,  # Sunday
        "2025-01-11": 100.0,  # Saturday
    }
    result = compute_weekly_pattern(daily)
    assert result["Saturday"] == 100.0
    assert result["Sunday"] == 200.0


def test_weekly_pattern_invalid_date():
    daily = {"not-a-date": 100.0}
    result = compute_weekly_pattern(daily)
    assert result == {}


def test_weekly_pattern_empty():
    assert compute_weekly_pattern({}) == {}


# ============================================================
# compute_trend
# ============================================================


def test_trend_empty():
    assert compute_trend({}) == 0.0


def test_trend_insufficient_points():
    daily = {f"2025-01-0{i}": float(i) for i in range(1, 6)}
    assert compute_trend(daily) == 0.0


def test_trend_positive():
    daily = {f"2025-01-{i:02d}": float(i) for i in range(1, 21)}
    result = compute_trend(daily)
    assert result > 0.0


# ============================================================
# compute_seasonality
# ============================================================


def test_seasonality_empty():
    assert compute_seasonality({}) == 0.0


def test_seasonality_normal():
    weekly = {"Monday": 100.0, "Tuesday": 200.0, "Wednesday": 100.0}
    result = compute_seasonality(weekly)
    assert result > 0.0


# ============================================================
# compute_residual_volatility
# ============================================================


def test_residual_volatility_empty():
    assert compute_residual_volatility({}) == 0.0


def test_residual_volatility_normal():
    daily = {f"2025-01-{i:02d}": float(i * 100) for i in range(1, 11)}
    result = compute_residual_volatility(daily)
    assert result > 0.0


# ============================================================
# compute_temporal_patterns
# ============================================================


def test_temporal_patterns_empty():
    result = compute_temporal_patterns([])
    assert result["trend"] == 0.0
    assert result["seasonality"] == 0.0
    assert result["residual_volatility"] == 0.0
    assert result["daily_spending"] == {}
    assert result["weekly_pattern"] == {}


def test_temporal_patterns_no_debits():
    transactions = [
        {"date_iso": "2025-01-01", "amount_paise": 10000, "type": "credit"},
    ]
    result = compute_temporal_patterns(transactions)
    assert result["daily_spending"] == {}


def test_temporal_patterns_normal():
    transactions = [
        {"date_iso": "2025-01-04", "amount_paise": 10000, "type": "debit"},
        {"date_iso": "2025-01-05", "amount_paise": 20000, "type": "debit"},
        {"date_iso": "2025-01-11", "amount_paise": 15000, "type": "debit"},
    ]
    result = compute_temporal_patterns(transactions)
    assert result["residual_volatility"] > 0.0
    assert "Saturday" in result["weekly_pattern"]
    assert result["coefficient_of_variation"] == result["residual_volatility"]
