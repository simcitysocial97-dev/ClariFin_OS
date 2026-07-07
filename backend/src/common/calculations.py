"""Calculation utilities."""


def percentage_change(old: float, new: float) -> float | None:
    """
    Calculate percentage change between two values.

    Args:
        old: Previous value
        new: Current value

    Returns:
        Percentage change or None if old is 0
    """
    if old == 0:
        return None
    return ((new - old) / abs(old)) * 100


def compute_is_large(amount: float, threshold: float = 10000.0) -> bool:
    """
    Classify transaction as large based on threshold.

    Args:
        amount: Transaction amount in rupees
        threshold: Threshold for large transaction (default 10k)

    Returns:
        True if transaction is large
    """
    return abs(amount) >= threshold
