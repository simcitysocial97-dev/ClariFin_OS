"""Data parsing utilities."""
import re
from datetime import datetime


def parse_date(date_str: str) -> datetime | None:
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
    # Handle "01 Aug 25" → "01 Aug 2025"
    m = re.match(r'^(\d{1,2})\s+([A-Za-z]{3})\s+(\d{2})$', s)
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


def get_month_key(date_str: str) -> str:
    """Extract YYYY-MM from date string."""
    dt = parse_date(date_str)
    if dt:
        return dt.strftime("%Y-%m")
    return ""


def get_weekday(date_str: str) -> str:
    """Get day of week name from date string."""
    dt = parse_date(date_str)
    if dt:
        return dt.strftime("%A")
    return ""
