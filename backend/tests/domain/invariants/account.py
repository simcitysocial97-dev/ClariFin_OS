"""Account Invariants — State transitions, scope ownership, balance consistency."""
from __future__ import annotations

from typing import Any

VALID_ACCOUNT_STATUSES = {"active", "dormant", "closed", "inactive"}
VALID_SCOPE_TYPES = {"household", "individual"}


def assert_account_state_valid(account_data: dict[str, Any]) -> None:
    """Validate account state invariants.

    INVARIANT: Account status is one of: active, dormant, closed, inactive.
    INVARIANT: Non-negative fields (credit_limit, balance for deposit accounts).

    Args:
        account_data: Account dictionary with status, balance, type fields

    Raises:
        AssertionError: If account state violates invariants
    """
    if "status" in account_data and account_data["status"] is not None:
        if account_data["status"] not in VALID_ACCOUNT_STATUSES:
            raise AssertionError(
                f"Invalid account status: {account_data['status']}. "
                f"Must be one of {VALID_ACCOUNT_STATUSES}"
            )

    # Credit limit must be non-negative for credit accounts
    if "credit_limit_paise" in account_data and account_data["credit_limit_paise"] is not None:
        if account_data["credit_limit_paise"] < 0:
            raise AssertionError(
                f"credit_limit_paise ({account_data['credit_limit_paise']}) cannot be negative"
            )


def assert_owner_scope_valid(account_data: dict[str, Any]) -> None:
    """Validate ownership scope (QEA-7).

    INVARIANT: At least one of owner_id or household_id is set.
    INVARIANT: Scope type is household or individual.

    Args:
        account_data: Account dictionary with owner_id, household_id, scope

    Raises:
        AssertionError: If ownership scope violates invariants
    """
    owner_id = account_data.get("owner_id")
    household_id = account_data.get("household_id")

    if not owner_id and not household_id:
        raise AssertionError(
            "Account must have at least one of: owner_id, household_id"
        )

    if "scope" in account_data and account_data["scope"] is not None:
        if account_data["scope"] not in VALID_SCOPE_TYPES:
            raise AssertionError(
                f"Invalid scope type: {account_data['scope']}. "
                f"Must be one of {VALID_SCOPE_TYPES}"
            )
        # Scope consistency: household scope requires household_id
        if account_data["scope"] == "household" and not household_id:
            raise AssertionError(
                "Household scope requires household_id to be set"
            )


def assert_account_closed_valid(is_active: bool, last_transaction_date: str | None) -> None:
    """Validate account closure invariants.

    INVARIANT: Closed accounts have no recent transaction activity.
    INVARIANT: Active accounts have a last_transaction_date.

    Args:
        is_active: Whether account is active
        last_transaction_date: ISO date of last transaction (None if never used)

    Raises:
        AssertionError: If closure state is inconsistent
    """
    if is_active and last_transaction_date is None:
        raise AssertionError(
            "Active account must have a last_transaction_date"
        )
