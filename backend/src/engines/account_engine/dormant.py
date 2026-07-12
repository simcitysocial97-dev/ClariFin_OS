"""
Dormant Detection Engine - Pure calculation module
===================================================
Detects account dormancy based on activity patterns.

All monetary values in paise (integer).
All dates in ISO-8601 format.

Provides factual dormancy detection only — no recommendations.
"""

from datetime import date


def compute_days_since_activity(last_activity_date: str, reference_date: str) -> int:
    """
    Compute days since last account activity.

    Args:
        last_activity_date: Last activity date in ISO-8601 format.
        reference_date: Reference date in ISO-8601 format.

    Returns:
        Number of days since last activity (non-negative integer).

    Raises:
        ValueError: If last_activity_date is after reference_date.
    """
    last: date = date.fromisoformat(last_activity_date)
    ref: date = date.fromisoformat(reference_date)

    if last > ref:
        raise ValueError(
            f"last_activity_date ({last_activity_date}) cannot be after reference_date ({reference_date})"
        )

    return (ref - last).days


def is_account_dormant(days_since_activity: int, threshold_days: int = 365) -> bool:
    """
    Determine if account is dormant based on days since last activity.

    Args:
        days_since_activity: Days since last transaction (from compute_days_since_activity).
        threshold_days: Number of days to consider as dormant (default: 365 = 12 months).

    Returns:
        True if account is dormant (days >= threshold), False otherwise.

    INVARIANT 1: Default threshold is 365 days (12 months).
    INVARIANT 2: Dormant status is purely deterministic.
    """
    if threshold_days < 0:
        raise ValueError("threshold_days must be non-negative")

    return days_since_activity >= threshold_days
