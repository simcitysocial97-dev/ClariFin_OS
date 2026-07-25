"""Domain Primitive Generators - Plain Python functions (Hypothesis-agnostic)."""

import random


def paise(min_val: int = -10000000, max_val: int = 10000000) -> int:
    """Generate random paise value within bounds.

    Args:
        min_val: Minimum paise value (default -₹100,000)
        max_val: Maximum paise value (default ₹100,000)

    Returns:
        Random integer paise value
    """
    return random.randint(min_val, max_val)


def positive_paise(min_val: int = 1, max_val: int = 10000000) -> int:
    """Generate positive paise value.

    Args:
        min_val: Minimum (default 1 paisa)
        max_val: Maximum (default ₹1,00,000)

    Returns:
        Positive integer paise value
    """
    return random.randint(min_val, max_val)


def confidence_bps() -> int:
    """Generate random confidence in basis points (0-10000).

    Returns:
        Integer between 0-10000 representing 0-100% confidence
    """
    return random.randint(0, 10000)


def iso_date(min_year: int = 2020, max_year: int = 2030) -> str:
    """Generate random ISO 8601 date string.

    Args:
        min_year: Minimum year
        max_year: Maximum year

    Returns:
        ISO date string YYYY-MM-DD
    """
    year = random.randint(min_year, max_year)
    month = random.randint(1, 12)

    # Handle month-end edge cases
    if month in (1, 3, 5, 7, 8, 10, 12):
        day = random.randint(1, 31)
    elif month in (4, 6, 9, 11):
        day = random.randint(1, 30)
    else:
        # February - handle leap years
        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        day = random.randint(1, 29 if is_leap else 28)

    return f"{year:04d}-{month:02d}-{day:02d}"


def loan_rate_bps() -> int:
    """Generate random loan interest rate in basis points.

    Typical range: 600-2400 bps (6%-24% annual)

    Returns:
        Integer basis points
    """
    return random.randint(600, 2400)


def credit_rate_bps() -> int:
    """Generate random credit card interest rate in basis points.

    Typical range: 1800-4800 bps (18%-48% annual)

    Returns:
        Integer basis points
    """
    return random.randint(1800, 4800)


def statement_cycle_day() -> int:
    """Generate statement cycle day (1-31).

    Returns:
        Day of month for statement
    """
    return random.randint(1, 31)


def account_id() -> str:
    """Generate random account ID.

    Returns:
        Account ID string
    """
    banks = ["HDFC", "ICICI", "SBI", "AXIS", "KOTAK"]
    account_types = ["SB", "CA", "CC"]
    return (
        f"{random.choice(banks)}_{random.choice(account_types)}{random.randint(1, 999)}"
    )
