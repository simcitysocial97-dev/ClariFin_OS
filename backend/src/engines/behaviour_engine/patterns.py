"""Pattern detection for behaviour engine.

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.

Transactions are expected as dicts with optional keys:
- date_iso: str (required) - YYYY-MM-DD format
- time_iso: str (optional) - HH:MM format
- description: str - merchant/description
- amount_paise: int - transaction amount
- category: str - transaction category
"""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any

from .utils import round_decimal

_IMPULSE_CATEGORIES = {"shopping", "food", "entertainment"}


def _parse_hour(time_iso: str | None) -> int | None:
    """Parse hour from time_iso string (HH:MM format)."""
    if not time_iso:
        return None
    try:
        time_str = time_iso.strip()
        if ":" in time_str:
            hour = int(time_str.split(":")[0])
            return hour
        return None
    except (ValueError, IndexError):
        return None


def _is_weekend(date_iso: str) -> bool:
    """Check if date_iso falls on Friday (5), Saturday (6), or Sunday (7)."""
    try:
        dt = datetime.strptime(date_iso, "%Y-%m-%d")
        # Python weekday: Monday=0, Sunday=6
        # Friday=4, Saturday=5, Sunday=6
        return dt.weekday() in (4, 5, 6)
    except (ValueError, TypeError):
        return False


def _is_night_time(hour: int | None) -> bool:
    """Check if hour falls within 20:00-02:00 night window."""
    if hour is None:
        return False
    # Night window: 20:00-23:59 or 00:00-02:00
    return hour >= 20 or hour <= 2


def detect_impulse_transactions(
    transactions: list[dict[str, Any]],
    min_amount_paise: int = 50000,  # ₹500 default
) -> list[dict[str, Any]]:
    """
    Detect potential impulse purchase transactions.

    Rules (when time_iso is available):
    - Time: 20:00-02:00 (night hours)
    - Days: Friday-Sunday (weekend)
    - Amount: > min_amount_paise
    - Categories: shopping, food, entertainment

    When time_iso is missing:
    - Applies only weekend + amount + category rules

    Parameters:
        transactions: List of transaction dicts with date_iso, time_iso (optional),
                    description, amount_paise, category keys.
        min_amount_paise: Minimum amount threshold in paise (default ₹500).

    Returns:
        List of transaction dicts that match impulse purchase criteria.
    """
    impulse_txns = []

    for txn in transactions:
        # Check amount threshold
        amount_paise = txn.get("amount_paise", 0)
        if amount_paise <= min_amount_paise:
            continue

        category = txn.get("category", "").lower()
        if category not in _IMPULSE_CATEGORIES:
            continue

        date_iso = txn.get("date_iso", "")
        time_iso = txn.get("time_iso")

        # Check weekend OR night time (if available)
        is_weekend_txn = _is_weekend(date_iso)
        is_night_txn = _is_night_time(_parse_hour(time_iso))

        # Include if weekend OR (time available AND night time)
        if is_weekend_txn or (time_iso is not None and is_night_txn):
            impulse_txns.append(txn)

    return impulse_txns


def compute_weekend_spend_ratio(transactions: list[dict[str, Any]]) -> Decimal:
    """
    Compute ratio of weekend spending to total spending.

    Formula: weekend_spend_amount / total_spend_amount

    Parameters:
        transactions: List of transaction dicts with date_iso, amount_paise, type.

    Returns:
        Decimal ratio between 0 and 1+. Returns Decimal('0') for empty/zero transactions.
    """
    total_spend = 0
    weekend_spend = 0

    for txn in transactions:
        amount = txn.get("amount_paise", 0)
        txn_type = txn.get("type", "").lower()

        if txn_type != "debit":
            continue

        total_spend += amount
        date_iso = txn.get("date_iso", "")
        if _is_weekend(date_iso):
            weekend_spend += amount

    if total_spend == 0:
        return Decimal('0')

    return round_decimal(Decimal(str(weekend_spend)) / Decimal(str(total_spend)))


def compute_night_spend_ratio(transactions: list[dict[str, Any]]) -> Decimal:
    """
    Compute ratio of night-time spending to total spending.

    Formula: night_spend_amount / total_spend_amount

    Night time: 20:00-02:00 (handles wrap-around midnight).

    Note:
        If time_iso is not available for any transaction, returns Decimal('0')
        as night spending cannot be determined.

    Parameters:
        transactions: List of transaction dicts with time_iso (optional), amount_paise, type.

    Returns:
        Decimal ratio between 0 and 1+. Returns Decimal('0') if no time data available.
    """
    total_spend = 0
    night_spend = 0
    has_time_data = False

    for txn in transactions:
        amount = txn.get("amount_paise", 0)
        txn_type = txn.get("type", "").lower()

        if txn_type != "debit":
            continue

        total_spend += amount
        time_iso = txn.get("time_iso")

        if time_iso is not None:
            has_time_data = True
            hour = _parse_hour(time_iso)
            if hour is not None and _is_night_time(hour):
                night_spend += amount

    # If no time data available, return 0
    if not has_time_data or total_spend == 0:
        return Decimal('0')

    return round_decimal(Decimal(str(night_spend)) / Decimal(str(total_spend)))


def _get_month_year(date_iso: str) -> tuple[int, int] | None:
    """Extract (month, year) from date_iso for grouping."""
    try:
        dt = datetime.strptime(date_iso, "%Y-%m-%d")
        return (dt.year, dt.month)
    except (ValueError, TypeError):
        return None


def detect_recurring_merchants(
    transactions: list[dict[str, Any]],
    min_occurrences: int = 3,
    amount_tolerance_bps: int = 1000,  # 10% default
) -> list[dict[str, Any]]:
    """
    Detect merchants with recurring spending patterns.

    Logic:
    - Same merchant (description)
    - Similar amount (within tolerance, default ±10%)
    - Monthly frequency >= min_occurrences (default 3)

    Parameters:
        transactions: List of transaction dicts with description, amount_paise, date_iso.
        min_occurrences: Minimum occurrences in a month to qualify as recurring.
        amount_tolerance_bps: Basis points tolerance for amount variation (default 10% = 1000bps).

    Returns:
        List of merchant pattern dicts with: merchant, count, months, avg_amount, months_covered.
    """
    # Group by merchant
    merchant_txns: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for txn in transactions:
        merchant = txn.get("description", "").strip().upper()
        if merchant:
            merchant_txns[merchant].append(txn)

    recurring_patterns = []

    for merchant, txns in merchant_txns.items():
        # Group by month
        months: dict[tuple[int, int], list[int]] = defaultdict(list)
        for txn in txns:
            date_iso = txn.get("date_iso", "")
            month_year = _get_month_year(date_iso)
            if month_year:
                months[month_year].append(txn.get("amount_paise", 0))

        # Check if merchant appears in enough months with similar amounts
        if len(months) < 1:
            continue

        # Calculate average amount per month
        avg_amounts = []
        months_with_sufficient = 0

        for _month_year, amounts in months.items():
            if len(amounts) >= min_occurrences:
                months_with_sufficient += 1
                avg_amounts.append(sum(amounts) // len(amounts))

        # Must have at least 2 months of recurring activity
        if months_with_sufficient >= 2:
            avg_amount = sum(avg_amounts) // len(avg_amounts) if avg_amounts else 0
            recurring_patterns.append({
                "merchant": merchant,
                "total_transactions": len(txns),
                "months_covered": months_with_sufficient,
                "avg_amount_paise": avg_amount,
                "first_seen": min(t.get("date_iso", "") for t in txns),
                "last_seen": max(t.get("date_iso", "") for t in txns),
            })

    return recurring_patterns


def detect_subscription_patterns(
    transactions: list[dict[str, Any]],
    amount_tolerance_bps: int = 1000,  # 10% default
) -> list[dict[str, Any]]:
    """
    Detect subscription payment patterns.

    Logic:
    - Same merchant (description)
    - Same amount (within tolerance)
    - Same day-of-month
    - Recurring monthly (across multiple months)

    Parameters:
        transactions: List of transaction dicts with description, amount_paise, date_iso.
        amount_tolerance_bps: Basis points tolerance for amount variation (default 10%).

    Returns:
        List of subscription pattern dicts with: merchant, day_of_month, amount_paise, months.
    """
    # Group by merchant
    merchant_txns: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for txn in transactions:
        merchant = txn.get("description", "").strip().upper()
        if merchant:
            merchant_txns[merchant].append(txn)

    subscriptions = []
    tolerance = amount_tolerance_bps / 10000  # Convert to decimal

    for merchant, txns in merchant_txns.items():
        # Group by day-of-month
        day_amounts: dict[int, list[tuple[int, tuple[int, int]]]] = defaultdict(list)  # day -> [(amount, (year, month))]

        for txn in txns:
            date_iso = txn.get("date_iso", "")
            amount = txn.get("amount_paise", 0)
            try:
                dt = datetime.strptime(date_iso, "%Y-%m-%d")
                day_of_month = dt.day
                month_year = (dt.year, dt.month)
                day_amounts[day_of_month].append((amount, month_year))
            except (ValueError, TypeError):
                continue

        # Check for subscription pattern (same day, same amount across months)
        for day, amount_months in day_amounts.items():
            if len(amount_months) < 2:
                continue

            # Get unique months
            unique_months = {month for _, month in amount_months}
            if len(unique_months) < 2:
                continue

            # Get amounts and check if they're similar
            amounts = [amt for amt, _ in amount_months]
            avg_amount = sum(amounts) // len(amounts)

            # Check if all amounts are within tolerance
            is_subscription = all(
                abs(amt - avg_amount) / avg_amount <= tolerance if avg_amount > 0 else False
                for amt in amounts
            )

            if is_subscription:
                subscriptions.append({
                    "merchant": merchant,
                    "day_of_month": day,
                    "avg_amount_paise": avg_amount,
                    "months_active": len(unique_months),
                    "total_transactions": len(amounts),
                    "first_seen": min(t.get("date_iso", "") for t in txns),
                    "last_seen": max(t.get("date_iso", "") for t in txns),
                })

    return subscriptions
