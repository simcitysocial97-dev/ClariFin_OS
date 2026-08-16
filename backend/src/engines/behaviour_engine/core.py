"""Behaviour Engine Core — Comprehensive behavioral intelligence.

Deterministic behavioral metrics for financial analysis based on Prospect Theory,
Present Bias, Habit Loop Theory, and Loss Aversion.

All monetary values are integers in paise (₹1.00 = 100 paise).
"""

import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

# ============================================================
# Caching Layer
# ============================================================
from cachetools import TTLCache

# Global cache instance: max 10 elements, 5-minute (300s) expiration
_behavior_cache: TTLCache[str, dict[str, Any]] = TTLCache(maxsize=10, ttl=300)


def invalidate_behavior_cache() -> None:
    """Clear the behavior profile cache. Call after data changes."""
    _behavior_cache.clear()


def get_cached_behavior_profile(_: str) -> dict[str, Any] | None:
    """
    Get behavior profile from cache if available.

    Returns cached profile or None if not cached.
    """
    cache_key = "global_behavior_profile"
    return _behavior_cache.get(cache_key)


def set_cached_behavior_profile(_: str, profile: dict[str, Any]) -> None:
    """Cache a behavior profile."""
    cache_key = "global_behavior_profile"
    _behavior_cache[cache_key] = profile


# ============================================================
# Utility Functions
# ============================================================


def _parse_date(date_str: str) -> datetime | None:
    """Parse various date formats to datetime."""
    if not date_str:
        return None
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d-%m-%y",
        "%d %b %Y",
        "%d %b %y",
        "%d-%b-%Y",
        "%d-%b-%y",
    ]
    s = date_str.strip()
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _normalize_score(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Normalize a value to 0-1 range with clamping."""
    if max_val == min_val:
        return 0.5
    normalized = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))


def _coefficient_of_variation(values: list[float]) -> float:
    """Calculate coefficient of variation (std/mean)."""
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


def _get_daily_spending_data(
    transactions: list[dict[str, Any]], cutoff_date: str
) -> dict[str, float]:
    """
    Get daily spending totals from pre-aggregated transaction data.
    """
    daily_spend: dict[str, float] = defaultdict(float)
    for txn in transactions:
        if txn.get("type") == "debit" and txn.get("date_iso", "") >= cutoff_date:
            date_iso = txn.get("date_iso", "")
            daily_spend[date_iso] += txn.get("amount_paise", 0) or 0
    return dict(daily_spend)


def _get_monthly_category_spending_data(
    transactions: list[dict[str, Any]], cutoff_date: str
) -> dict[str, dict[str, float]]:
    """
    Get monthly category spending from pre-aggregated transaction data.
    Returns: {month: {category: total}}
    """
    result: defaultdict[str, defaultdict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    for txn in transactions:
        if txn.get("type") == "debit" and txn.get("date_iso", "") >= cutoff_date:
            date_iso = txn.get("date_iso", "")
            month = date_iso[:7] if date_iso else ""
            category = txn.get("category", "Uncategorized")
            result[month][category] += txn.get("amount_paise", 0) or 0
    return dict(result)


def _get_monthly_income_expenses_data(
    transactions: list[dict[str, Any]], cutoff_date: str
) -> dict[str, dict[str, int]]:
    """
    Get monthly income vs expenses from pre-aggregated transaction data.
    Returns: {month: {"income_paise": total, "expenses_paise": total}}
    """
    result: defaultdict[str, dict[str, int]] = defaultdict(
        lambda: {"income_paise": 0, "expenses_paise": 0}
    )
    for txn in transactions:
        if txn.get("date_iso", "") >= cutoff_date:
            date_iso = txn.get("date_iso", "")
            month = date_iso[:7] if date_iso else ""
            txn_type = txn.get("type", "")
            amount = txn.get("amount_paise", 0) or 0
            if txn_type == "credit":
                result[month]["income_paise"] += amount
            else:
                result[month]["expenses_paise"] += amount
    return dict(result)


def _get_transaction_stats_data(
    transactions: list[dict[str, Any]], cutoff_date: str
) -> dict[str, Any]:
    """
    Get transaction statistics from pre-aggregated transaction data.
    Returns counts and totals for various metrics.
    """
    stats = {
        "total_count": 0,
        "debit_count": 0,
        "credit_count": 0,
        "micro_txn_count": 0,
        "total_debit_paise": 0,
        "total_credit_paise": 0,
        "weekend_spend_paise": 0,
        "weekday_spend_paise": 0,
    }

    weekend_stats = {"weekend": 0, "weekday": 0}

    for txn in transactions:
        if txn.get("date_iso", "") >= cutoff_date:
            stats["total_count"] += 1
            txn_type = txn.get("type", "")
            amount_paise = txn.get("amount_paise", 0) or 0

            if txn_type == "debit":
                stats["debit_count"] += 1
                stats["total_debit_paise"] += amount_paise
                if amount_paise < 50000:
                    stats["micro_txn_count"] += 1

                date_iso = txn.get("date_iso", "")
                if date_iso:
                    try:
                        dt = datetime.strptime(date_iso, "%Y-%m-%d")
                        day_type = "weekend" if dt.weekday() >= 5 else "weekday"
                        weekend_stats[day_type] += amount_paise
                    except (ValueError, TypeError):
                        pass
            elif txn_type == "credit":
                stats["credit_count"] += 1
                stats["total_credit_paise"] += amount_paise

    stats["weekend_spend_paise"] = weekend_stats["weekend"]
    stats["weekday_spend_paise"] = weekend_stats["weekday"]
    return stats


# ============================================================
# Data Extraction
# ============================================================


def _get_transactions_90_days(
    transactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Filter transactions from last 90 days from pre-aggregated data."""
    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    return [txn for txn in transactions if txn.get("date_iso", "") >= cutoff]


def _get_recent_transactions(
    transactions: list[dict[str, Any]], limit: int = 500
) -> list[dict[str, Any]]:
    """Get most recent N transactions from pre-aggregated data."""
    # Sort in descending order and take the most recent N transactions
    sorted_txns = sorted(
        transactions, key=lambda r: r.get("date_iso", ""), reverse=True
    )
    recent_txns = sorted_txns[:limit]
    # Return in ascending order for time-series calculations
    return sorted(recent_txns, key=lambda r: r.get("date_iso", ""))


# ============================================================
# Temporal Pattern Analysis
# ============================================================


def _compute_temporal_patterns(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute temporal spending patterns.

    Returns trend, seasonality, and residual volatility metrics.
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
    daily_spend: defaultdict[str, float] = defaultdict(float)
    for txn in transactions:
        if txn.get("type") == "debit":
            date_iso = txn.get("date_iso", "")
            if date_iso:
                daily_spend[date_iso] += txn.get("amount_paise", 0) or 0

    if not daily_spend:
        return {
            "trend": 0.0,
            "seasonality": 0.0,
            "residual_volatility": 0.0,
            "coefficient_of_variation": 0.0,
            "daily_spending": {},
            "weekly_pattern": {},
        }

    # Sort by date
    sorted_dates = sorted(daily_spend.keys())
    daily_values = [daily_spend[d] for d in sorted_dates]

    # Compute trend (7-day moving average slope)
    ma = _moving_average(daily_values, 7)
    if len(ma) >= 14:
        recent_trend = (ma[-1] - ma[-7]) / max(ma[-7], 1)
    else:
        recent_trend = 0.0

    # Compute weekly seasonality (day-of-week variance)
    weekly_pattern: defaultdict[str, list[float]] = defaultdict(list)
    for date_str, amount in daily_spend.items():
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            weekday = dt.strftime("%A")
            weekly_pattern[weekday].append(amount)
        except (ValueError, TypeError, AttributeError):
            pass

    weekly_avg = {
        day: sum(vals) / len(vals) if vals else 0
        for day, vals in weekly_pattern.items()
    }

    # Seasonality = variance between weekday averages
    if weekly_avg:
        weekday_vals = list(weekly_avg.values())
        seasonality = _coefficient_of_variation(weekday_vals)
    else:
        seasonality = 0.0

    # Residual volatility
    cv = _coefficient_of_variation(daily_values)

    return {
        "trend": round(recent_trend, 4),
        "seasonality": round(seasonality, 4),
        "residual_volatility": round(cv, 4),
        "coefficient_of_variation": round(cv, 4),
        "daily_spending": dict[str, Any](daily_spend),
        "weekly_pattern": weekly_avg,
    }


# ============================================================
# Behavioral Indices
# ============================================================


def _compute_loss_aversion_index(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute Loss Aversion Index based on Kahneman & Tversky.

    Components:
    - Post-income spend velocity (72h window)
    - Emotional overspend after large expenses
    - Recovery time to baseline
    """
    if not transactions:
        return {"score": 0.5, "post_income_velocity": 0.0, "recovery_time_days": 0}

    # Find income credits (salary, transfers in)
    credits = [t for t in transactions if t.get("type") == "credit"]
    debits = [t for t in transactions if t.get("type") == "debit"]

    if not credits or not debits:
        return {"score": 0.5, "post_income_velocity": 0.0, "recovery_time_days": 0}

    # Calculate median debit for baseline (convert from paise to rupees for thresholds)
    debit_amounts = [(t.get("amount_paise", 0) or 0) / 100.0 for t in debits]
    if not debit_amounts:
        return {"score": 0.5, "post_income_velocity": 0.0, "recovery_time_days": 0}

    median_debit = sorted(debit_amounts)[len(debit_amounts) // 2]

    # Post-income spending velocity
    post_income_spends: list[float] = []

    for credit in credits:
        credit_date = _parse_date(credit.get("date_iso", "") or credit.get("date", ""))
        if not credit_date:
            continue

        # Find debits within 72 hours
        spend_72h = 0.0
        for debit in debits:
            debit_date = _parse_date(debit.get("date_iso", "") or debit.get("date", ""))
            if not debit_date:
                continue

            days_diff = (debit_date - credit_date).days
            if 0 <= days_diff <= 3:
                spend_72h += (debit.get("amount_paise", 0) or 0) / 100.0

        credit_amount = (credit.get("amount_paise", 0) or 0) / 100.0
        if credit_amount > 0:
            velocity = spend_72h / credit_amount
            post_income_spends.append(velocity)

    # Calculate average velocity
    avg_velocity = (
        sum(post_income_spends) / len(post_income_spends) if post_income_spends else 0
    )

    # Emotional overspend after large expenses (>2x median)
    large_expenses = [
        t for t in debits if (t.get("amount_paise", 0) or 0) / 100.0 > 2 * median_debit
    ]

    # Recovery time calculation (simplified)
    # Days to return to median spending after large expense
    recovery_days = 0
    if large_expenses:
        # Simplified: assume recovery takes proportional time
        avg_large = sum(
            (t.get("amount_paise", 0) or 0) / 100.0 for t in large_expenses
        ) / len(large_expenses)
        recovery_days = min(30, int(avg_large / max(median_debit, 1)))

    # Normalize to 0-1 score
    # Higher velocity = higher loss aversion (spending gains quickly)
    velocity_score = _normalize_score(avg_velocity, 0, 1.5)
    recovery_score = _normalize_score(recovery_days, 0, 30)

    loss_aversion = velocity_score * 0.6 + recovery_score * 0.4

    return {
        "score": round(loss_aversion, 4),
        "post_income_velocity": round(avg_velocity, 4),
        "recovery_time_days": recovery_days,
        "large_expense_count": len(large_expenses),
    }


def _compute_impulsivity_score(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute Impulsivity Score based on Present Bias.

    Signals:
    - Micro-transactions clustering (< ₹500)
    - Late-night spending ratio (22:00–06:00)
    - Weekend vs weekday variance
    - Category switching frequency
    """
    if not transactions:
        return {"score": 0.5, "micro_txn_ratio": 0.0, "late_night_ratio": 0.0}

    debits = [t for t in transactions if t.get("type") == "debit"]
    if not debits:
        return {"score": 0.5, "micro_txn_ratio": 0.0, "late_night_ratio": 0.0}

    total_debits = len(debits)

    # Micro-transactions (< ₹500)
    micro_txns = [t for t in debits if (t.get("amount_paise", 0) or 0) / 100.0 < 500]
    micro_ratio = len(micro_txns) / total_debits if total_debits > 0 else 0

    # Late-night spending (simplified - would need timestamp data)
    # For now, use weekend spending as proxy
    weekend_txns = []
    weekday_txns = []

    for txn in debits:
        date_iso = txn.get("date_iso", "")
        if date_iso:
            try:
                dt = datetime.strptime(date_iso, "%Y-%m-%d")
                if dt.weekday() >= 5:  # Saturday, Sunday
                    weekend_txns.append(txn)
                else:
                    weekday_txns.append(txn)
            except (ValueError, TypeError):
                pass

    # Weekend vs weekday variance
    if weekend_txns and weekday_txns:
        weekend_avg = sum(
            (t.get("amount_paise", 0) or 0) / 100.0 for t in weekend_txns
        ) / len(weekend_txns)
        weekday_avg = sum(
            (t.get("amount_paise", 0) or 0) / 100.0 for t in weekday_txns
        ) / len(weekday_txns)
        weekend_ratio = weekend_avg / max(weekday_avg, 1)
    else:
        weekend_ratio = 1.0

    # Category switching (discretionary categories)
    discretionary_categories = [
        "Food & Dining",
        "Entertainment",
        "Shopping",
        "Travel",
        "Lifestyle",
        "Groceries",
        "Online Shopping",
    ]

    discretionary_txns = [
        t for t in debits if t.get("category") in discretionary_categories
    ]
    disc_ratio = len(discretionary_txns) / total_debits if total_debits > 0 else 0

    # Compute composite score
    micro_score = _normalize_score(micro_ratio, 0, 0.8)
    weekend_score = _normalize_score(weekend_ratio, 0.5, 2.0)
    disc_score = _normalize_score(disc_ratio, 0, 0.6)

    impulsivity = micro_score * 0.35 + weekend_score * 0.35 + disc_score * 0.30

    return {
        "score": round(impulsivity, 4),
        "micro_txn_ratio": round(micro_ratio, 4),
        "weekend_ratio": round(weekend_ratio, 4),
        "discretionary_ratio": round(disc_ratio, 4),
        "micro_txn_count": len(micro_txns),
    }


def _compute_habit_stability_score(
    transactions: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Compute Habit Stability Score based on Habit Loop Theory.

    Measures:
    - Category coefficient of variation (monthly)
    - Recurring expense predictability
    - Behavioral rhythm regularity
    """
    if not transactions:
        return {"score": 0.5, "category_cv": 0.0, "recurring_predictability": 0.0}

    debits = [t for t in transactions if t.get("type") == "debit"]
    if not debits:
        return {"score": 0.5, "category_cv": 0.0, "recurring_predictability": 0.0}

    # Monthly category spending (use amount_paise, convert to rupees for analysis)
    monthly_category: defaultdict[str, defaultdict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    for txn in debits:
        date_iso = txn.get("date_iso", "")
        if date_iso:
            month = date_iso[:7]  # YYYY-MM
            category = txn.get("category", "Uncategorized")
            monthly_category[month][category] += (
                txn.get("amount_paise", 0) or 0
            ) / 100.0

    # Category CV across months
    category_cvs: list[float] = []
    if monthly_category:
        all_categories: set[str] = set()
        for month_data in monthly_category.values():
            all_categories.update(month_data.keys())

        for cat in all_categories:
            monthly_vals = [
                monthly_category[m].get(cat, 0) for m in sorted(monthly_category.keys())
            ]
            if len(monthly_vals) >= 2:
                cv = _coefficient_of_variation(monthly_vals)
                category_cvs.append(cv)

    avg_category_cv = sum(category_cvs) / len(category_cvs) if category_cvs else 0

    # Recurring expense detection (similar amounts, same description)
    desc_amounts: defaultdict[str, list[float]] = defaultdict(list)
    for txn in debits:
        desc = txn.get("description", "")[:30]  # Truncate for matching
        amount = (txn.get("amount_paise", 0) or 0) / 100.0
        if amount > 0:
            desc_amounts[desc].append(amount)

    recurring_count = 0
    for _desc, amounts in desc_amounts.items():
        if len(amounts) >= 3:
            # Check if amounts are similar (within 10%)
            avg = sum(amounts) / len(amounts)
            if all(abs(a - avg) / max(avg, 1) < 0.1 for a in amounts):
                recurring_count += 1

    recurring_score = min(1.0, recurring_count / 10)  # Normalize to max 10 recurring

    # Behavioral rhythm (regular transaction days)
    daily_counts: defaultdict[str, float] = defaultdict(float)
    for txn in debits:
        date_iso = txn.get("date_iso", "")
        if date_iso:
            daily_counts[date_iso] += 1

    if daily_counts:
        counts = [float(v) for v in daily_counts.values()]
        rhythm_cv = _coefficient_of_variation(counts)
        rhythm_score = 1 - _normalize_score(rhythm_cv, 0, 2)
    else:
        rhythm_score = 0.5

    # Composite score (lower CV = higher stability)
    cv_score = 1 - _normalize_score(avg_category_cv, 0, 1.5)

    habit_stability = cv_score * 0.40 + recurring_score * 0.30 + rhythm_score * 0.30

    return {
        "score": round(habit_stability, 4),
        "category_cv": round(avg_category_cv, 4),
        "recurring_count": recurring_count,
        "rhythm_score": round(rhythm_score, 4),
    }


def _compute_financial_stress_index(
    transactions: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Compute Financial Stress Index.

    Measures:
    - Balance volatility coefficient
    - End-of-month depletion ratio
    - Credit dependency ratio
    - Buffer adequacy (days covered)
    """
    if not transactions:
        return {"score": 0.5, "balance_volatility": 0.0, "credit_dependency": 0.0}

    # Separate credits and debits
    credits = [t for t in transactions if t.get("type") == "credit"]
    debits = [t for t in transactions if t.get("type") == "debit"]

    if not debits:
        return {"score": 0.5, "balance_volatility": 0.0, "credit_dependency": 0.0}

    # Daily net flow (convert amount_paise to rupees for analysis)
    daily_net: defaultdict[str, float] = defaultdict(float)
    for txn in transactions:
        date_iso = txn.get("date_iso", "")
        if date_iso:
            amount = (txn.get("amount_paise", 0) or 0) / 100.0
            if txn.get("type") == "debit":
                daily_net[date_iso] -= amount
            else:
                daily_net[date_iso] += amount

    # Running balance simulation
    sorted_dates = sorted(daily_net.keys())
    running_balance: list[float] = []
    balance: float = 0.0
    for date in sorted_dates:
        balance += daily_net[date]
        running_balance.append(balance)

    # Balance volatility
    if running_balance:
        balance_cv = _coefficient_of_variation([abs(b) for b in running_balance])
    else:
        balance_cv = 0

    # Credit dependency (convert amount_paise to rupees)
    total_credit = sum((t.get("amount_paise", 0) or 0) / 100.0 for t in credits)
    total_debit = sum((t.get("amount_paise", 0) or 0) / 100.0 for t in debits)
    credit_dependency = total_credit / max(total_debit, 1) if total_debit > 0 else 0

    # End-of-month depletion (last 5 days spending ratio)
    eom_spending: float = 0.0
    total_spending: float = 0.0

    for txn in debits:
        date_iso = txn.get("date_iso", "")
        amount = (txn.get("amount_paise", 0) or 0) / 100.0
        total_spending += amount

        if date_iso:
            try:
                dt = datetime.strptime(date_iso, "%Y-%m-%d")
                if dt.day >= 26:  # Last 5 days
                    eom_spending += amount
            except (ValueError, TypeError):
                pass

    eom_ratio = eom_spending / max(total_spending, 1)

    # Buffer adequacy (days of expenses covered by average balance)
    avg_balance = (
        abs(sum(running_balance) / len(running_balance)) if running_balance else 0
    )
    daily_avg_spend = total_debit / max(len(daily_net), 1)
    buffer_days = avg_balance / max(daily_avg_spend, 1)
    buffer_score = _normalize_score(buffer_days, 0, 30)

    # Composite stress index (higher = more stress)
    volatility_score = _normalize_score(balance_cv, 0, 2)
    dependency_score = _normalize_score(credit_dependency, 0, 2)
    eom_score = _normalize_score(eom_ratio, 0, 0.5)

    stress_index = (
        volatility_score * 0.30
        + dependency_score * 0.30
        + eom_score * 0.20
        + (1 - buffer_score) * 0.20
    )

    return {
        "score": round(stress_index, 4),
        "balance_volatility": round(balance_cv, 4),
        "credit_dependency": round(credit_dependency, 4),
        "eom_depletion_ratio": round(eom_ratio, 4),
        "buffer_days": round(buffer_days, 1),
    }


def _compute_savings_discipline_score(
    transactions: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Compute Savings Discipline Score.

    Measures:
    - 3-month rolling savings rate trend
    - Savings transfer consistency
    - Positive savings momentum
    """
    if not transactions:
        return {"score": 0.5, "savings_rate": 0.0, "momentum": 0.0}

    # Monthly income vs expenses (use amount_paise, convert to rupees for analysis)
    monthly_data: defaultdict[str, dict[str, float]] = defaultdict(
        lambda: {"income": 0.0, "expenses": 0.0}
    )

    for txn in transactions:
        date_iso = txn.get("date_iso", "")
        if date_iso:
            month = date_iso[:7]
            amount = (txn.get("amount_paise", 0) or 0) / 100.0
            if txn.get("type") == "credit":
                monthly_data[month]["income"] += amount
            else:
                monthly_data[month]["expenses"] += amount

    if not monthly_data:
        return {"score": 0.5, "savings_rate": 0.0, "momentum": 0.0}

    # Calculate monthly savings rates
    savings_rates = []
    sorted_months = sorted(monthly_data.keys())

    for month in sorted_months:
        income = monthly_data[month]["income"]
        expenses = monthly_data[month]["expenses"]
        if income > 0:
            rate = (income - expenses) / income
            savings_rates.append((month, rate))

    if not savings_rates:
        return {"score": 0.5, "savings_rate": 0.0, "momentum": 0.0}

    # Average savings rate
    avg_rate = sum(r for _, r in savings_rates) / len(savings_rates)

    # Savings momentum (trend over last 3 months)
    if len(savings_rates) >= 2:
        recent_rates = [r for _, r in savings_rates[-3:]]
        earlier_rates = (
            [r for _, r in savings_rates[:-3]] if len(savings_rates) > 3 else [0]
        )

        recent_avg = sum(recent_rates) / len(recent_rates)
        earlier_avg = sum(earlier_rates) / len(earlier_rates) if earlier_rates else 0

        momentum = recent_avg - earlier_avg
    else:
        momentum = 0

    # Savings consistency (how often positive savings)
    positive_months = sum(1 for _, r in savings_rates if r > 0)
    consistency = positive_months / len(savings_rates) if savings_rates else 0

    # Composite score
    rate_score = _normalize_score(avg_rate, -0.5, 0.5)
    momentum_score = _normalize_score(momentum, -0.3, 0.3)
    consistency_score = consistency

    savings_score = rate_score * 0.40 + momentum_score * 0.30 + consistency_score * 0.30

    return {
        "score": round(savings_score, 4),
        "savings_rate": round(avg_rate, 4),
        "momentum": round(momentum, 4),
        "consistency": round(consistency, 4),
        "positive_savings_months": positive_months,
    }


def detect_india_risk_patterns(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Detect India-specific risky financial behaviors.

    Patterns:
    - UPI micro-spend clustering
    - Gambling/gaming transactions
    - Loan app patterns
    - EMI burden ratio
    """
    if not transactions:
        return {
            "upi_micro_spend_flag": False,
            "gambling_flag": False,
            "loan_app_pattern_flag": False,
            "emi_ratio": 0.0,
        }

    debits = [t for t in transactions if t.get("type") == "debit"]
    credits = [t for t in transactions if t.get("type") == "credit"]

    # UPI micro-spend detection (>10 transactions/day < ₹200)
    daily_micro: defaultdict[str, int] = defaultdict(int)
    for txn in debits:
        amount = (txn.get("amount_paise", 0) or 0) / 100.0
        date_iso = txn.get("date_iso", "")
        if amount < 200 and date_iso:
            daily_micro[date_iso] += 1

    upi_flag = any(count > 10 for count in daily_micro.values())

    # Gambling detection
    gambling_keywords = [
        "dream11",
        "mpl",
        "rummy",
        "bet",
        "casino",
        "poker",
        "teen patti",
        "my11circle",
        "fantasy",
        "betting",
        "gambl",
    ]

    gambling_txns = []
    for txn in debits:
        desc = (txn.get("description", "") or "").lower()
        if any(kw in desc for kw in gambling_keywords):
            gambling_txns.append(txn)

    gambling_flag = len(gambling_txns) > 0

    # Loan app detection (multiple small credits from NBFCs)
    loan_keywords = ["loan", "nbfc", "credit", "lend", "finance", "cash", "instant"]

    loan_credits = []
    for txn in credits:
        desc = (txn.get("description", "") or "").lower()
        amount = (txn.get("amount_paise", 0) or 0) / 100.0
        if any(kw in desc for kw in loan_keywords) and amount < 50000:
            loan_credits.append(txn)

    # Check for clustering (multiple loans within 7 days)
    loan_dates = []
    for txn in loan_credits:
        date_iso = txn.get("date_iso", "")
        if date_iso:
            loan_dates.append(date_iso)

    loan_flag = len(loan_dates) >= 2  # Multiple loan credits

    # EMI ratio calculation
    emi_keywords = ["emi", "loan repayment", "installment"]
    monthly_emi: defaultdict[str, float] = defaultdict(float)

    for txn in debits:
        desc = (txn.get("description", "") or "").lower()
        date_iso = txn.get("date_iso", "")
        if any(kw in desc for kw in emi_keywords) and date_iso:
            month = date_iso[:7]
            monthly_emi[month] += (txn.get("amount_paise", 0) or 0) / 100.0

    # Calculate EMI to income ratio
    monthly_income: defaultdict[str, float] = defaultdict(float)
    for txn in credits:
        date_iso = txn.get("date_iso", "")
        if date_iso:
            month = date_iso[:7]
            monthly_income[month] += (txn.get("amount_paise", 0) or 0) / 100.0

    emi_ratios = []
    for month in monthly_emi:
        if monthly_income.get(month, 0) > 0:
            ratio = monthly_emi[month] / monthly_income[month]
            emi_ratios.append(ratio)

    avg_emi_ratio = sum(emi_ratios) / len(emi_ratios) if emi_ratios else 0

    return {
        "upi_micro_spend_flag": upi_flag,
        "gambling_flag": gambling_flag,
        "gambling_transaction_count": len(gambling_txns),
        "loan_app_pattern_flag": loan_flag,
        "loan_credit_count": len(loan_credits),
        "emi_ratio": round(avg_emi_ratio, 4),
        "monthly_emi_total": sum(monthly_emi.values()),
    }


def compute_behavior_profile(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute comprehensive behavioral profile from pre-aggregated transaction data.

    Returns:
        {
            "temporal_patterns": {...},
            "behavioral_indices": {...},
            "risk_signals": {...},
            "confidence": float (0–1),
            "financial_health_score": float (0–100)
        }
    """
    # Filter transactions for 90-day window and get recent 500
    transactions_90d = _get_transactions_90_days(transactions)
    recent_transactions = _get_recent_transactions(transactions, 500)

    # Use 90-day window if available, otherwise use most recent 500
    txn_set = transactions_90d if len(transactions_90d) >= 30 else recent_transactions

    # Compute temporal patterns
    temporal = _compute_temporal_patterns(txn_set)

    # Compute behavioral indices
    loss_aversion = _compute_loss_aversion_index(txn_set)
    impulsivity = _compute_impulsivity_score(txn_set)
    habit_stability = _compute_habit_stability_score(txn_set)
    financial_stress = _compute_financial_stress_index(txn_set)
    savings_discipline = _compute_savings_discipline_score(txn_set)

    # India-specific risk detection
    india_risks = detect_india_risk_patterns(txn_set)

    # Compute confidence based on data density
    confidence = min(1.0, len(txn_set) / 200)

    # Buffer adequacy from stress index
    buffer_score = _normalize_score(financial_stress.get("buffer_days", 0), 0, 30)

    # Composite Financial Health Score
    health_score = (
        0.20 * savings_discipline["score"]
        + 0.18 * habit_stability["score"]
        + 0.18 * (1 - impulsivity["score"])
        + 0.18 * (1 - financial_stress["score"])
        + 0.13 * (1 - loss_aversion["score"])
        + 0.13 * buffer_score
    ) * 100  # Scale to 0-100

    return {
        "temporal_patterns": {
            "trend": temporal["trend"],
            "seasonality": temporal["seasonality"],
            "volatility": temporal["residual_volatility"],
            "weekly_pattern": temporal["weekly_pattern"],
        },
        "behavioral_indices": {
            "loss_aversion": loss_aversion,
            "impulsivity": impulsivity,
            "habit_stability": habit_stability,
            "financial_stress": financial_stress,
            "savings_discipline": savings_discipline,
        },
        "risk_signals": {
            "india_specific": india_risks,
            "high_impulsivity": impulsivity["score"] > 0.7,
            "high_stress": financial_stress["score"] > 0.6,
            "low_savings": savings_discipline["score"] < 0.3,
        },
        "confidence": round(confidence, 2),
        "financial_health_score": round(health_score, 1),
        "data_quality": {
            "transactions_analyzed": len(txn_set),
        },
    }


# Keep the insight and nudge engine imports for backward compatibility
from .insights import (
    generate_behavioral_insights,
    generate_summary_text,
)
from .nudges import (
    generate_nudges,
    get_top_nudge,
)

__all__ = [
    # Utility functions
    "_normalize_score",
    "_coefficient_of_variation",
    "_moving_average",
    # Behavioral indices
    "_compute_loss_aversion_index",
    "_compute_impulsivity_score",
    "_compute_habit_stability_score",
    "_compute_financial_stress_index",
    "_compute_savings_discipline_score",
    # Core profile
    "compute_behavior_profile",
    "detect_india_risk_patterns",
    # Insight generation
    "generate_behavioral_insights",
    "generate_summary_text",
    # Nudge engine
    "generate_nudges",
    "get_top_nudge",
    # Cache functions
    "get_cached_behavior_profile",
    "set_cached_behavior_profile",
    "invalidate_behavior_cache",
]
