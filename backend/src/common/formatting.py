"""Display formatting utilities."""
import re
from datetime import datetime


def format_inr(amount: float) -> str:
    """
    Format amount as Indian Rupees with proper separators.

    Args:
        amount: Amount in rupees (NOT paise)

    Returns:
        Formatted string like "₹1,23,456.78"
    """
    if amount < 0:
        return f"-₹{abs(amount):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"₹{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_date_display(date_str: str) -> str:
    """
    Format date string for display.

    Args:
        date_str: Date in various formats (YYYY-MM-DD, DD/MM/YYYY, etc.)

    Returns:
        Standardized display format
    """
    try:
        # Try parsing common formats
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%d %b %Y")
            except ValueError:
                continue
        return date_str  # Return as-is if parsing fails
    except Exception:
        return date_str


def clean_description(desc: str) -> str:
    """
    Clean transaction description for display.

    Args:
        desc: Raw transaction description

    Returns:
        Cleaned description with normalized whitespace
    """
    # Remove multiple spaces
    cleaned = re.sub(r'\s+', ' ', desc)
    # Remove common banking prefixes
    cleaned = re.sub(r'^(UPI|NEFT|IMPS|RTGS)[-\s]*', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()
