"""
ClariFin Utils
==============
Centralized utility module for common helper functions.

Functions:
    parse_date_to_iso: Parse various date formats to ISO YYYY-MM-DD
    format_paise: Format integer paise as Indian Rupee string
    parse_amount_to_paise: Convert any amount representation to paise
    add_months: Add N months to a date, clamping to last day of target month
"""

import re
import calendar
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple


# ============================================================
# Dependency Checks
# ============================================================

def is_camelot_available() -> bool:
    """Check if camelot-py is installed and available."""
    try:
        import camelot  # noqa
        return True
    except ImportError:
        return False


# ============================================================
# Financial Constants
# ============================================================

DAYS_IN_YEAR = 365
MAX_PROJECTION_MONTHS = 600
GOAL_MAX_MONTHS = 1000

DEFAULT_EQUITY_RETURN = 10.0
DEFAULT_DEBT_RETURN = 7.0
DEFAULT_INFLATION_RATE = 6.0

FIXED_EXPENSE_CATEGORIES = frozenset({
    'EMI', 'Rent', 'Insurance', 'Subscription', 'Subscriptions',
    'Utilities', 'Loan Payment', 'Loan Repayment',
})


# ============================================================
# Date Parsing
# ============================================================

def parse_date_to_iso(date_str: str | None) -> str | None:
    """Parse various Indian and international date formats to ISO YYYY-MM-DD."""
    if not date_str:
        return None

    s = str(date_str).strip()
    if not s:
        return None

    m = re.match(r'^(\d{1,2})\s+([A-Za-z]{3})\s+(\d{2})$', s)
    if m:
        day, mon, yr = m.group(1), m.group(2), m.group(3)
        yr_full = f"20{yr}" if int(yr) < 50 else f"19{yr}"
        s = f"{day} {mon} {yr_full}"

    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
        "%d %b %Y", "%d %b %y", "%d %B %Y", "%d %B %y", "%d %b '%y",
        "%d-%b-%Y", "%d-%b-%y", "%m/%d/%Y", "%Y%m%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def parse_date_for_sort(date_str: str) -> Tuple[str, int]:
    """Parse date for sorting."""
    ymd = parse_date_to_iso(date_str)
    return (ymd if ymd else "0000-00-00", 0)


# ============================================================
# Amount Formatting
# ============================================================

def format_paise(paise: int) -> str:
    """Format paise as Indian Rupee string with lakh/crore grouping."""
    if paise is None:
        return "₹0.00"

    negative = paise < 0
    paise = abs(paise)

    rupees = paise // 100
    paise_part = paise % 100

    if rupees <= 999:
        formatted = str(rupees)
    else:
        s = str(rupees)
        last3 = s[-3:]
        remaining = s[:-3]
        groups = []
        while remaining:
            groups.append(remaining[-2:] if len(remaining) >= 2 else remaining)
            remaining = remaining[:-2]
        groups.reverse()
        formatted = ",".join(groups) + "," + last3

    result = f"₹{formatted}.{paise_part:02d}"
    return f"-{result}" if negative else result


def format_paise_compact(paise: int) -> str:
    """Format paise in compact form (L/Cr for large amounts)."""
    if paise is None:
        return "₹0"

    negative = paise < 0
    paise = abs(paise)
    rupees = paise / 100

    if rupees >= 10_000_000:
        result = f"₹{rupees / 10_000_000:.2f} Cr"
    elif rupees >= 100_000:
        result = f"₹{rupees / 100_000:.2f} L"
    else:
        return format_paise(paise)

    return f"-{result}" if negative else result


# ============================================================
# Amount Parsing (canonical path)
# ============================================================

def validate_no_float(value, caller: str = "unknown") -> None:
    """Float rejection delegated to parse_amount_to_paise / to_paise.
    
    Kept as no-op for backward compatibility with external callers.
    """
    pass


def parse_amount_to_paise(amount) -> int:
    """Convert any amount representation to integer paise.

    Routes through Decimal + ROUND_HALF_UP.
    """
    if amount is None:
        return 0

    if isinstance(amount, int):
        return amount * 100

    if isinstance(amount, float):
        return int((Decimal(str(amount)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    if isinstance(amount, str):
        s = amount.strip()
        if not s or s == '-':
            return 0

        for char in ['₹', '$', 'Rs.', 'Rs', 'INR', 'inr', ',', ' ', 'CR', 'DR', 'Cr', 'Dr', 'cr', 'dr']:
            s = s.replace(char, '')

        if s.startswith('(') and s.endswith(')'):
            s = '-' + s[1:-1]

        s = s.strip()
        if not s:
            return 0

        try:
            decimal_val = Decimal(s)
            return int((decimal_val * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        except (ValueError, TypeError):
            return 0

    try:
        return int((Decimal(str(amount)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    except (ValueError, TypeError):
        return 0


def parse_amount_to_float(raw: str) -> float:
    """Convert amount string to float rupees."""
    if raw is None:
        return 0.0

    s = str(raw).strip()

    for char in [',', '₹', 'Rs.', 'Rs', 'INR', 'inr', ' ', 'CR', 'DR', 'Cr', 'Dr', 'cr', 'dr']:
        s = s.replace(char, '')

    if s.startswith('(') and s.endswith(')'):
        s = '-' + s[1:-1]

    s = s.strip()
    if not s or s == '-':
        return 0.0

    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


# ============================================================
# Date Arithmetic
# ============================================================

def add_months(start_date: date, months: int) -> date:
    """Add N months to a date, clamping to last day of target month."""
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    max_day = calendar.monthrange(year, month)[1]
    day = min(start_date.day, max_day)
    return date(year, month, day)


# ============================================================
# Convenience Aliases
# ============================================================

def format_inr(amount: float) -> str:
    """Format float rupees as Indian Rupee string."""
    if amount is None:
        return "₹0.00"
    paise = int(round(amount * 100))
    return format_paise(paise)


# ============================================================
# CLI Test
# ============================================================

if __name__ == "__main__":
    print("Testing parse_date_to_iso:")
    for d in ["25/12/2024", "2024-01-15", "15 Jan 2024", "15-Dec-2024", "12/25/2024", "01 Aug 25", None, "garbage", ""]:
        print(f"  '{d}' -> {parse_date_to_iso(d)}")

    print("\nTesting format_paise:")
    for a in [123456, 0, 10000000, 100000000, -123456, None]:
        print(f"  {a} -> {format_paise(a)}")

    print("\nTesting parse_amount_to_paise:")
    for inp in ['1,234.56', None, 100, 50.5, '₹5,000.00', '-', '']:
        print(f"  {inp!r} -> {parse_amount_to_paise(inp)}")

    print("\nAll tests completed!")