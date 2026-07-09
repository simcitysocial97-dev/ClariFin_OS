"""Calculation utilities."""
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from .formatting import format_inr


from typing import Any, Union


def _parse_amount_paise(amount_str: Union[str, int, float]) -> int:
    """
    Parse amount to integer paise (1 rupee = 100 paise).
    Raises ValueError on invalid input (no silent failures).

    Accepts:
        - String amounts: "Rs 1,234.56", "₹1234.56", "1234"
        - Numeric amounts: 1234, 1234.56, 1234.0

    Examples:
        "Rs 1,234.56" -> 123456
        "₹1234.56"    -> 123456
        "1234"        -> 123400
        1234          -> 123400
        1234.56       -> 123456
    """
    # Convert to string if numeric
    if isinstance(amount_str, (int, float)):
        # For integers, treat as rupees
        if isinstance(amount_str, int):
            return amount_str * 100
        # For floats, use Decimal to avoid precision loss
        paise = Decimal(str(amount_str)) * Decimal('100')
        return int(paise.quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    # Handle string input
    cleaned = (str(amount_str)
               .replace("Rs", "")
               .replace("₹", "")
               .replace(",", "")
               .strip())

    if not cleaned:
        raise ValueError(f"Empty amount string: {amount_str!r}")

    try:
        rupees = Decimal(cleaned)
        # Financial Standard: Use quantization to guarantee safe integer conversion
        paise = (rupees * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return int(paise)
    except (ValueError, InvalidOperation) as e:
        raise ValueError(f"Invalid amount format '{amount_str}': {e}") from e


def percentage_change(current: float, previous: float) -> str:
    """Calculate percentage change, return formatted string."""
    if previous == 0:
        return "+100%" if current > 0 else "0%"
    change = ((current - previous) / previous) * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}%"


def compute_is_large(transactions: list[Any]) -> list:
    """Flag transactions that are >2.5x average debit."""
    debit_txns = [t for t in transactions if t.get("type") == "debit"]
    if not debit_txns:
        return transactions

    avg_debit = sum((t.get("amount_paise", 0) or 0) for t in debit_txns) / len(debit_txns)
    threshold = avg_debit * 250000  # 2.5x in paise

    for t in transactions:
        t["is_large"] = bool(t.get("type") == "debit" and (t.get("amount_paise", 0) or 0) > threshold)

    return transactions


def compute_behavioral_insights(transactions: list[Any]) -> list:
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

    # Category drift (use amount_paise, convert to rupees for percentage)
    cat_monthly: dict[str, Any] = defaultdict(lambda: defaultdict(float))
    for t in debit_txns:
        mk = t.get("month_key", "")
        cat = t.get("category", "Uncategorized")
        if mk:
            cat_monthly[cat][mk] += ((t.get("amount_paise", 0) or 0) / 100.0)

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
    monthly_totals: dict[str, Any] = defaultdict(float)
    for t in debit_txns:
        mk = t.get("month_key", "")
        if mk:
            monthly_totals[mk] += ((t.get("amount_paise", 0) or 0) / 100.0)

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
        largest = max(this_month_txns, key=lambda t: (t.get("amount_paise", 0) or 0))
        desc = (largest.get("description_display") or largest.get("description", ""))[:30]
        amt = format_inr((largest.get("amount_paise", 0) or 0) / 100.0)
        insights.append({
            "title": "Largest Expense",
            "description": f"Your biggest: {desc} at {amt}",
            "severity": "info",
            "icon": "zap",
        })

    return insights[:6]
