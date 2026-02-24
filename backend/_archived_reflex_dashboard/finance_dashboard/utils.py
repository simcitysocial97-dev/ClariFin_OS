from datetime import datetime
from typing import Optional


def format_inr(amount: float) -> str:
    """Format amount in Indian Rupee notation with lakh/crore grouping."""
    if amount is None:
        return "₹0.00"
    negative = amount < 0
    amount = abs(amount)
    integer_part = int(amount)
    decimal_part = f"{amount:.2f}".split(".")[1]
    s = str(integer_part)
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        remaining = s[:-3]
        groups = []
        while remaining:
            groups.append(remaining[-2:] if len(remaining) >= 2 else remaining)
            remaining = remaining[:-2]
        groups.reverse()
        formatted = ",".join(groups) + "," + last3
    result = f"₹{formatted}.{decimal_part}"
    return f"-{result}" if negative else result


def format_inr_compact(amount: float) -> str:
    """Compact format: 154000 → ₹1.5L, 5432 → ₹5.4K"""
    if amount is None:
        return "₹0"
    negative = amount < 0
    amount = abs(amount)
    if amount >= 10000000:
        result = f"₹{amount/10000000:.1f}Cr"
    elif amount >= 100000:
        result = f"₹{amount/100000:.1f}L"
    elif amount >= 1000:
        result = f"₹{amount/1000:.1f}K"
    else:
        result = f"₹{amount:.0f}"
    return f"-{result}" if negative else result


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse various Indian date formats to datetime."""
    if not date_str:
        return None
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
        "%d %b %Y", "%d %b %y", "%d-%b-%Y", "%d-%b-%y",
        "%d %b '%y", "%d %B %Y", "%d %B %y",
        "%Y-%m-%d",
    ]
    s = date_str.strip()
    # Handle "01 Aug 25" → "01 Aug 2025" (2-digit year without apostrophe)
    import re as _re
    m = _re.match(r'^(\d{1,2})\s+([A-Za-z]{3})\s+(\d{2})$', s)
    if m:
        day, mon, yr = m.group(1), m.group(2), m.group(3)
        yr_full = f"20{yr}" if int(yr) < 50 else f"19{yr}"
        s = f"{day} {mon} {yr_full}"
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def format_date_display(date_str: str) -> str:
    """Convert any date format to: 15 Jun 2025"""
    dt = parse_date(date_str)
    if dt:
        return dt.strftime("%d %b %Y")
    return date_str


def clean_description(desc: str) -> str:
    """
    Clean transaction descriptions for display.
    - Remove timestamp prefixes (HH:MM:SS from HDFC UPI)
    - Remove date+time combos
    - Collapse multiple spaces
    """
    if not desc:
        return ""
    import re as _re
    # Remove leading date+time (e.g., "25/04/2025 16:47:17 ")
    cleaned = _re.sub(r'^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s+', '', desc)
    # Remove leading timestamp (e.g., "16:47:17 ")
    cleaned = _re.sub(r'^\d{2}:\d{2}:\d{2}\s+', '', cleaned)
    # Collapse multiple spaces
    cleaned = _re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def truncate(text: str, length: int = 60) -> str:
    """Truncate text with ellipsis."""
    if not text or len(text) <= length:
        return text or ""
    return text[:length - 1] + "…"


def get_month_key(date_str: str) -> str:
    """Extract YYYY-MM from date string."""
    dt = parse_date(date_str)
    if dt:
        return dt.strftime("%Y-%m")
    return ""


def get_month_display(month_key: str) -> str:
    """YYYY-MM → Jun 2025"""
    try:
        dt = datetime.strptime(month_key, "%Y-%m")
        return dt.strftime("%b %Y")
    except ValueError:
        return month_key


def get_weekday(date_str: str) -> str:
    """Get day of week name from date string."""
    dt = parse_date(date_str)
    if dt:
        return dt.strftime("%A")
    return ""


def percentage_change(current: float, previous: float) -> str:
    """Calculate percentage change, return formatted string."""
    if previous == 0:
        return "+100%" if current > 0 else "0%"
    change = ((current - previous) / previous) * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}%"
