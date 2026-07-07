"""Calculation utilities."""
from collections import defaultdict

from .formatting import format_inr


def percentage_change(current: float, previous: float) -> str:
    """Calculate percentage change, return formatted string."""
    if previous == 0:
        return "+100%" if current > 0 else "0%"
    change = ((current - previous) / previous) * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}%"


def compute_is_large(transactions: list) -> list:
    """Flag transactions that are >2.5x average debit."""
    debit_txns = [t for t in transactions if t.get("type") == "debit"]
    if not debit_txns:
        return transactions

    avg_debit = sum(t.get("amount", 0) for t in debit_txns) / len(debit_txns)
    threshold = avg_debit * 2.5

    for t in transactions:
        t["is_large"] = bool(t.get("type") == "debit" and t.get("amount", 0) > threshold)

    return transactions


def compute_behavioral_insights(transactions: list) -> list:
    """Generate behavioral insights from transactions."""
    insights = []
    debit_txns = [t for t in transactions if t.get("type") == "debit"]

    if not debit_txns:
        return []

    # Get month keys
    month_keys = sorted({t.get("month_key", "") for t in debit_txns if t.get("month_key")})
    if len(month_keys) < 1:
        return []

    this_month = month_keys[-1]
    month_keys[:-1]

    # Category drift
    cat_monthly: dict = defaultdict(lambda: defaultdict(float))
    for t in debit_txns:
        mk = t.get("month_key", "")
        cat = t.get("category", "Uncategorized")
        if mk:
            cat_monthly[cat][mk] += t.get("amount", 0)

    for cat, monthly_data in cat_monthly.items():
        if len(monthly_data) >= 2:
            this_month_cat = monthly_data.get(this_month, 0)
            other_months = [v for k, v in monthly_data.items() if k != this_month]
            if other_months:
                avg_other = sum(other_months) / len(other_months)
                if avg_other > 0:
                    pct_change = ((this_month_cat - avg_other) / avg_other) * 100
                    if pct_change > 30:
                        insights.append({
                            "title": f"{cat} Spending Up",
                            "description": f"You spent {int(pct_change)}% more on {cat} this month",
                            "severity": "warning",
                            "icon": "trending-up",
                        })
                    elif pct_change < -30:
                        insights.append({
                            "title": f"{cat} Savings",
                            "description": f"You spent {int(abs(pct_change))}% less on {cat}",
                            "severity": "positive",
                            "icon": "trending-down",
                        })

    # Spending trend
    monthly_totals: dict = defaultdict(float)
    for t in debit_txns:
        mk = t.get("month_key", "")
        if mk:
            monthly_totals[mk] += t.get("amount", 0)

    if len(monthly_totals) >= 2:
        this_month_total = monthly_totals.get(this_month, 0)
        other_totals = [v for k, v in monthly_totals.items() if k != this_month]
        if other_totals:
            avg_other_total = sum(other_totals) / len(other_totals)
            if avg_other_total > 0:
                pct_change_total = ((this_month_total - avg_other_total) / avg_other_total) * 100
                if pct_change_total > 15:
                    insights.append({
                        "title": "Spending Trending Up",
                        "description": f"Overall spending is up {int(pct_change_total)}%",
                        "severity": "warning",
                        "icon": "alert-triangle",
                    })
                elif pct_change_total < -15:
                    insights.append({
                        "title": "Spending Down",
                        "description": f"Spending is down {int(abs(pct_change_total))}%",
                        "severity": "positive",
                        "icon": "check-circle",
                    })

    # Largest expense
    this_month_txns = [t for t in debit_txns if t.get("month_key") == this_month]
    if this_month_txns:
        largest = max(this_month_txns, key=lambda t: t.get("amount", 0))
        desc = (largest.get("description_display") or largest.get("description", ""))[:30]
        amt = format_inr(largest.get("amount", 0))
        insights.append({
            "title": "Largest Expense",
            "description": f"Your biggest: {desc} at {amt}",
            "severity": "info",
            "icon": "zap",
        })

    return insights[:6]