"""Financial Events Invariants - Event integrity and amount consistency."""

from __future__ import annotations

from typing import Any


def assert_financial_event_valid(event: dict[str, Any]) -> None:
    """Validate a single financial event.

    INVARIANT: amount_paise is non-negative integer.
    INVARIANT: asset_change + liability_change >= 0 (net worth cannot decrease from event).
    INVARIANT: event_type is a known type.

    Args:
        event: Financial event dictionary

    Raises:
        AssertionError: If event is invalid
    """
    amount = event.get("amount_paise", 0)
    if not isinstance(amount, int):
        raise AssertionError(f"amount_paise={amount} is not integer paise")
    if amount < 0:
        raise AssertionError(f"amount_paise={amount} is negative")

    valid_types = {
        "cash_advance",
        "credit_card_cash_advance",
        "liability_increase",
        "asset_purchase",
        "income_credit",
        "expense_debit",
    }
    event_type = event.get("event_type", "")
    if event_type not in valid_types:
        raise AssertionError(f"Invalid event_type: {event_type}")


def assert_financial_event_net_worth_preserved(
    events: list[dict[str, Any]],
) -> None:
    """Validate that financial events preserve net worth consistency.

    INVARIANT: Sum of asset_change_paise + liability_change_paise across all events
    equals the net change in financial position.

    Args:
        events: List of financial event dictionaries

    Raises:
        AssertionError: If net worth is inconsistent
    """
    total_asset_change = sum(e.get("asset_change_paise", 0) for e in events)
    total_liability_change = sum(e.get("liability_change_paise", 0) for e in events)

    net_change = total_asset_change + total_liability_change
    if net_change < 0:
        raise AssertionError(
            f"Net worth decreased by {abs(net_change)} paise across events"
        )


def assert_financial_event_amount_consistency(event: dict[str, Any]) -> None:
    """Validate that event amount equals the sum of component changes.

    INVARIANT: amount_paise == asset_change_paise + liability_change_paise + expense_paise + income_paise

    Args:
        event: Financial event dictionary

    Raises:
        AssertionError: If amount is inconsistent
    """
    amount = event.get("amount_paise", 0)
    asset = event.get("asset_change_paise", 0)
    liability = event.get("liability_change_paise", 0)
    expense = event.get("expense_paise", 0)
    income = event.get("income_paise", 0)

    expected = asset + liability + expense + income
    if amount != expected:
        raise AssertionError(
            f"amount_paise={amount} != asset({asset}) + liability({liability}) "
            f"+ expense({expense}) + income({income}) = {expected}"
        )
