"""Display formatting utilities."""
import re


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


def format_date_display(date_str: str) -> str:
    """Convert any date format to: 15 Jun 2025"""
    from .parsing import parse_date
    dt = parse_date(date_str)
    if dt:
        return dt.strftime("%d %b %Y")
    return date_str


def clean_description(desc: str) -> str:
    """Clean transaction descriptions for display."""
    if not desc:
        return ""
    # Remove leading date+time
    cleaned = re.sub(r'^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s+', '', desc)
    # Remove leading timestamp
    cleaned = re.sub(r'^\d{2}:\d{2}:\d{2}\s+', '', cleaned)
    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned
