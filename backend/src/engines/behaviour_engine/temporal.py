"""Temporal pattern analysis for behaviour engine.

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.

Transactions are expected as dicts with keys:
- date_iso: str - YYYY-MM-DD format
- amount_paise: int - transaction amount
- type: str - "debit" or "credit"
"""

import math
from collections import defaultdict
from datetime import datetime
from typing import Any


def _coefficient_of_variation(values: list[float]) -> float:
    """Calculate coefficient of variation (std/mean).

    Used for temporal volatility calculations.
    """
    if not values or len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std = math.sqrt(variance)
    return std / mean


def _moving_average(values: list[float], window: int = 7) -> list[float]:
    """Calculate simple moving average."""
    if not values or window <= 0:
        return []
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        window_vals = values[start : i + 1]
        result.append(sum(window_vals) / len(window_vals))
    return result


def compute_daily_spending(transactions: list[dict[str, Any]]) -> dict[str, float]:
    """Aggregate daily spending totals from transactions.

    Parameters:
        transactions: List of transaction dicts with date_iso, amount_paise, type.

    Returns:
        Dict mapping date_iso to total spending in paise.
    """
    daily_spend: defaultdict[str, float] = defaultdict(float)
    for txn in transactions:
        if txn.get("type") == "debit":
            date_iso = txn.get("date_iso", "")
            if date_iso:
                daily_spend[date_iso] += txn.get("amount_paise", 0) or 0

    return dict(daily_spend)


def compute_weekly_pattern(daily_spending: dict[str, float]) -> dict[str, float]:
    """Compute day-of-week spending averages.

    Parameters:
        daily_spending: Dict mapping date_iso to spending amount.

    Returns:
        Dict mapping day name to average spending.
    """
    weekly_pattern: defaultdict[str, list[float]] = defaultdict(list)

    for date_str, amount in daily_spending.items():
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            weekday = dt.strftime("%A")
            weekly_pattern[weekday].append(amount)
        except (ValueError, TypeError):
            pass

    return {
        day: sum(vals) / len(vals) if vals else 0.0
        for day, vals in weekly_pattern.items()
    }


def compute_trend(daily_spending: dict[str, float], window: int = 7) -> float:
    """Compute trend (7-day moving average slope).

    Parameters:
        daily_spending: Dict mapping date_iso to spending amount.
        window: Moving average window size.

    Returns:
        Trend value (slope of recent MA vs earlier MA).
    """
    if not daily_spending:
        return 0.0

    sorted_dates = sorted(daily_spending.keys())
    daily_values = [daily_spending[d] for d in sorted_dates]

    ma = _moving_average(daily_values, window)
    if len(ma) >= 14:
        recent_trend = (ma[-1] - ma[-7]) / max(ma[-7], 1)
    else:
        recent_trend = 0.0

    return round(recent_trend, 4)


def compute_seasonality(weekly_pattern: dict[str, float]) -> float:
    """Compute seasonality as variance between weekday averages.

    Parameters:
        weekly_pattern: Dict mapping day name to average spending.

    Returns:
        Coefficient of variation between weekday averages.
    """
    if not weekly_pattern:
        return 0.0

    weekday_vals = list(weekly_pattern.values())
    return round(_coefficient_of_variation(weekday_vals), 4)


def compute_residual_volatility(daily_spending: dict[str, float]) -> float:
    """Compute residual volatility (coefficient of variation of daily spending).

    Parameters:
        daily_spending: Dict mapping date_iso to spending amount.

    Returns:
        Volatility score.
    """
    if not daily_spending:
        return 0.0

    daily_values = list(daily_spending.values())
    return round(_coefficient_of_variation(daily_values), 4)


def compute_temporal_patterns(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute temporal spending patterns.

    Returns trend, seasonality, and residual volatility metrics.

    Parameters:
        transactions: List of transaction dicts with date_iso, amount_paise, type.

    Returns:
        Dict with:
        - trend: float - spending trend slope
        - seasonality: float - day-of-week variance
        - residual_volatility: float - daily spending volatility
        - coefficient_of_variation: float - same as residual_volatility
        - daily_spending: dict - date->amount mapping
        - weekly_pattern: dict - day_name->average spending mapping
    """
    if not transactions:
        return {
            "trend": 0.0,
            "seasonality": 0.0,
            "residual_volatility": 0.0,
            "coefficient_of_variation": 0.0,
            "daily_spending": {},
            "weekly_pattern": {},
        }

    # Aggregate daily spending
    daily_spend = compute_daily_spending(transactions)

    if not daily_spend:
        return {
            "trend": 0.0,
            "seasonality": 0.0,
            "residual_volatility": 0.0,
            "coefficient_of_variation": 0.0,
            "daily_spending": {},
            "weekly_pattern": {},
        }

    # Compute components
    trend = compute_trend(daily_spend)
    weekly_pattern = compute_weekly_pattern(daily_spend)
    seasonality = compute_seasonality(weekly_pattern)
    volatility = compute_residual_volatility(daily_spend)

    return {
        "trend": trend,
        "seasonality": seasonality,
        "residual_volatility": volatility,
        "coefficient_of_variation": volatility,
        "daily_spending": {k: float(v) for k, v in daily_spend.items()},
        "weekly_pattern": weekly_pattern,
    }
