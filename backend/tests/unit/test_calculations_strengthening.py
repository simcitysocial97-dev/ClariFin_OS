"""Behavioral strengthening tests for common_calculations (M9-C42.23 Batch 4).

The existing suite covers parsing and the main thresholds. These tests pin the
exact boundary behavior of compute_behavioral_insights: category-drift and
spending-trend insights trigger only for *strictly* beyond the 30% / 15%
thresholds, which were untested boundary points in the C42.21 survivor set.
"""

from __future__ import annotations

from typing import Any

from src.common.calculations import compute_behavioral_insights


def _drift_txns(
    other_paise: int, this_paise: int, cat: str = "food"
) -> list[dict[str, Any]]:
    return [
        {
            "type": "debit",
            "month_key": "2025-01",
            "amount_paise": other_paise,
            "category": cat,
        },
        {
            "type": "debit",
            "month_key": "2025-02",
            "amount_paise": other_paise,
            "category": cat,
        },
        {
            "type": "debit",
            "month_key": "2025-03",
            "amount_paise": this_paise,
            "category": cat,
        },
    ]


def test_category_drift_exactly_30_percent_not_flagged() -> None:
    """pct_change == 30.0 must NOT trigger (threshold is strictly > 30)."""
    # other avg = 1000, this = 1300 -> exactly 30% increase
    result = compute_behavioral_insights(_drift_txns(100000, 130000))
    assert not any("Spending Up" in r["title"] for r in result)


def test_category_drift_just_above_30_percent_flagged() -> None:
    """pct_change == 31.0 must trigger the warning insight."""
    result = compute_behavioral_insights(_drift_txns(100000, 131000))
    assert any("Spending Up" in r["title"] for r in result)


def test_spending_trend_exactly_15_percent_not_flagged() -> None:
    """Overall trend == 15.0 must NOT trigger (threshold is strictly > 15)."""
    result = compute_behavioral_insights(_drift_txns(100000, 115000, cat="food"))
    assert not any("Spending Trending Up" in r["title"] for r in result)


def test_spending_trend_just_above_15_percent_flagged() -> None:
    result = compute_behavioral_insights(_drift_txns(100000, 116000, cat="food"))
    assert any("Spending Trending Up" in r["title"] for r in result)
