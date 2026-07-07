"""Data parsing utilities."""
from datetime import datetime


def parse_date(date_str: str) -> datetime | None:
    """
    Parse date string in multiple formats.

    Args:
        date_str: Date string in various formats

    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d %b %Y",
        "%d %B %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def get_month_key(date_str: str) -> str:
    """
    Extract YYYY-MM key from date string.

    Args:
        date_str: Date string

    Returns:
        Month key like "2024-01"
    """
    dt = parse_date(date_str)
    if dt:
        return dt.strftime("%Y-%m")
    return "Unknown"
