"""Direct unit tests for src/engines/financial_intelligence/utils.py.

M9-C42.25 — direct behavioral ownership of the shared forecasting utilities:
month arithmetic, statistics, trend classification, and balance projection.
All monetary values are integer paise.
"""

from decimal import Decimal

import pytest
from src.engines.financial_intelligence.utils import (
    ACTION_WEIGHTS,
    DEFAULT_DEBT_ALLOCATION_RATIO,
    DEFAULT_EMERGENCY_THRESHOLD_PAISE,
    DEFAULT_FORECAST_MONTHS,
    FOIR_SAFE_THRESHOLD,
    FOIR_WARNING_THRESHOLD,
    HIGH_INTEREST_THRESHOLD_BPS,
    LONG_TERM_GOAL_ALLOCATION_RATIO,
    MAX_FORECAST_MONTHS,
    compute_confidence_from_variance,
    compute_trend_direction,
    compute_utilization_ratio,
    compute_variance,
    compute_weighted_average,
    find_stress_month,
    generate_month_sequence,
    next_month,
    project_running_balance,
)

# ============================================================
# Constants (financial policy invariants)
# ============================================================


def test_policy_constants():
    assert DEFAULT_EMERGENCY_THRESHOLD_PAISE == 3_000_000
    assert DEFAULT_FORECAST_MONTHS == 3
    assert MAX_FORECAST_MONTHS == 12
    assert Decimal("0.40") == FOIR_SAFE_THRESHOLD
    assert Decimal("0.60") == FOIR_WARNING_THRESHOLD
    assert HIGH_INTEREST_THRESHOLD_BPS == 1800
    assert Decimal("0.60") == DEFAULT_DEBT_ALLOCATION_RATIO
    assert Decimal("0.40") == LONG_TERM_GOAL_ALLOCATION_RATIO
    assert sum(ACTION_WEIGHTS.values()) == Decimal("1.0")


# ============================================================
# Month arithmetic
# ============================================================


def test_next_month_simple():
    assert next_month("2025-01") == "2025-02"
    assert next_month("2025-09") == "2025-10"


def test_next_month_december_rolls_year():
    assert next_month("2025-12") == "2026-01"


def test_generate_month_sequence():
    assert generate_month_sequence("2025-11", 3) == ["2025-11", "2025-12", "2026-01"]


def test_generate_month_sequence_zero_count():
    assert generate_month_sequence("2025-01", 0) == []


# ============================================================
# Statistics
# ============================================================


def test_compute_variance_empty_and_single():
    assert compute_variance([]) == 0.0
    assert compute_variance([500]) == 0.0


def test_compute_variance_two_values():
    assert compute_variance([1, 3]) == pytest.approx(1.0)


def test_compute_variance_known_value():
    values = [10, 20, 30]
    # mean 20; ((10-20)^2 + 0 + (30-20)^2) / 3 = 200/3
    assert compute_variance(values) == pytest.approx(200.0 / 3.0)


def test_compute_weighted_average_empty():
    assert compute_weighted_average([]) == 0.0


def test_compute_weighted_average_linear_weights():
    # weights [1, 2]: (10*1 + 20*2) / 3
    assert compute_weighted_average([10, 20]) == pytest.approx(50.0 / 3.0)


def test_compute_weighted_average_recent_values_dominate():
    low_then_high = compute_weighted_average([0, 100])
    high_then_low = compute_weighted_average([100, 0])
    assert low_then_high > high_then_low


def test_compute_weighted_average_explicit_weights():
    assert compute_weighted_average([10, 20], weights=[2, 1]) == pytest.approx(
        40.0 / 3.0
    )


def test_compute_weighted_average_weight_length_mismatch_raises():
    with pytest.raises(ValueError):
        compute_weighted_average([1, 2], weights=[1.0])


def test_compute_weighted_average_zero_weights():
    assert compute_weighted_average([10, 20], weights=[0.0, 0.0]) == 0.0


def test_confidence_from_variance_constant_history_is_max():
    assert compute_confidence_from_variance([5000, 5000, 5000]) == Decimal("1")


def test_confidence_from_variance_decreases_with_variance():
    calm = compute_confidence_from_variance([100, 110, 105])
    volatile = compute_confidence_from_variance([100, 1_000_000, 10])
    assert calm > volatile


def test_confidence_from_variance_bounded_zero_one():
    assert Decimal("0") <= compute_confidence_from_variance([0, 10**12]) <= Decimal("1")


def test_confidence_from_variance_single_value():
    assert compute_confidence_from_variance([123]) == Decimal("1")


# ============================================================
# Credit utilization
# ============================================================


def test_compute_utilization_ratio_empty():
    assert compute_utilization_ratio([]) == Decimal("0")


def test_compute_utilization_ratio_average():
    history = [
        {"utilization_ratio": Decimal("0.2")},
        {"utilization_ratio": Decimal("0.4")},
    ]
    assert compute_utilization_ratio(history) == Decimal("0.3")


def test_compute_utilization_ratio_missing_values_default_zero():
    history = [{"utilization_ratio": None}, {"utilization_ratio": Decimal("0.5")}]
    assert compute_utilization_ratio(history) == Decimal("0.25")


def test_trend_direction_single_value_stable():
    assert compute_trend_direction([Decimal("0.5")]) == "stable"
    assert compute_trend_direction([]) == "stable"


def test_trend_direction_constant_is_stable():
    ratios = [Decimal("0.3")] * 4
    assert compute_trend_direction(ratios) == "stable"


def test_trend_direction_within_ten_percent_is_stable():
    ratios = [Decimal("0.30"), Decimal("0.31")]
    assert compute_trend_direction(ratios) == "stable"


def test_trend_direction_increasing_is_worsening():
    ratios = [Decimal("0.1"), Decimal("0.2")]
    assert compute_trend_direction(ratios) == "worsening"


def test_trend_direction_decreasing_is_improving():
    ratios = [Decimal("0.2"), Decimal("0.1")]
    assert compute_trend_direction(ratios) == "improving"


def test_trend_direction_first_half_zero_second_zero_stable():
    ratios = [Decimal("0"), Decimal("0")]
    assert compute_trend_direction(ratios) == "stable"


def test_trend_direction_first_half_zero_second_positive():
    ratios = [Decimal("0"), Decimal("0.2")]
    assert compute_trend_direction(ratios) == "worsening"


def test_trend_direction_first_half_zero_second_negative():
    # Known quirk pinned: with zero baseline, diff = second_half_avg (signed),
    # so a negative second half reads as 'stable'.
    ratios = [Decimal("0"), Decimal("-0.2")]
    assert compute_trend_direction(ratios) == "stable"


def test_trend_direction_odd_length_split():
    ratios = [
        Decimal("0.1"),
        Decimal("0.1"),
        Decimal("0.1"),
        Decimal("0.2"),
        Decimal("0.2"),
    ]
    # mid = 2: first avg 0.1, second avg 0.1666... -> +66% -> worsening
    assert compute_trend_direction(ratios) == "worsening"


# ============================================================
# Balance projection
# ============================================================


def test_project_running_balance_tracks_minimum():
    assert project_running_balance(100, [-30, 10, -50]) == 30


def test_project_running_balance_all_positive():
    assert project_running_balance(100, [10, 20]) == 100


def test_project_running_balance_goes_negative():
    assert project_running_balance(100, [-200]) == -100


def test_project_running_balance_empty_surpluses():
    assert project_running_balance(500, []) == 500


def test_find_stress_month_never_crossed():
    assert find_stress_month(100, [-10, -10], threshold_paise=0) is None


def test_find_stress_month_crossing_month():
    assert find_stress_month(100, [-10, -10], threshold_paise=85) == 2


def test_find_stress_month_exact_threshold_is_not_stress():
    assert find_stress_month(100, [-10], threshold_paise=90) is None


def test_find_stress_month_first_month():
    assert find_stress_month(100, [-50], threshold_paise=60) == 1


def test_find_stress_month_empty_surpluses():
    assert find_stress_month(100, [], threshold_paise=200) is None
