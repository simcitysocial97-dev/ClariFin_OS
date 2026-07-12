"""
Account Lifecycle Engine - Pure calculation module
=================================================
Account state transitions.

All monetary values in paise (integer).
All dates in ISO-8601 format.

Provides factual state transitions only — no recommendations or heuristics.
"""



def compute_account_status(
    is_active: bool,
    last_transaction_date: str | None,
    reference_date: str,
) -> str:
    """
    Compute account status based on activity and closure state.

    Args:
        is_active: Whether the account is administratively active.
        last_transaction_date: Last transaction date in ISO-8601 format, or None.
        reference_date: Reference date in ISO-8601 format.

    Returns:
        Status string: "ACTIVE", "DORMANT", or "CLOSED".

    State Rules:
        - CLOSED: Terminal state (is_active=False or no transaction history)
        - DORMANT: No transactions for 365+ days
        - ACTIVE: Otherwise
    """
    # CLOSED is terminal - explicit admin closure
    if not is_active:
        return "CLOSED"

    # No transaction history means closed account
    if last_transaction_date is None:
        return "CLOSED"

    # Import dormancy check
    from .dormant import compute_days_since_activity, is_account_dormant

    days_since = compute_days_since_activity(last_transaction_date, reference_date)

    if is_account_dormant(days_since, threshold_days=365):
        return "DORMANT"

    return "ACTIVE"


def is_account_closed(is_active: bool, last_transaction_date: str | None) -> bool:
    """
    Check if account is in closed state.

    Args:
        is_active: Whether the account is administratively active.
        last_transaction_date: Last transaction date in ISO-8601 format, or None.

    Returns:
        True if account is CLOSED, False otherwise.
    """
    return not is_active or last_transaction_date is None
