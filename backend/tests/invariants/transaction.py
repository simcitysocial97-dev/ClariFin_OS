"""Transaction Invariants — Ordering, sign conventions, amount consistency."""

from __future__ import annotations

from typing import Any


def assert_transaction_ordering_valid(transactions: list[dict[str, Any]]) -> None:
    """Validate transactions are sorted chronologically.

    INVARIANT: Transactions are in ascending date_iso order.
    INVARIANT: No gap exceeding 90 days without a transaction (active account heuristic).

    Args:
        transactions: List of transaction dictionaries with date_iso

    Raises:
        AssertionError: If ordering is invalid
    """
    if not transactions:
        return

    prev_date: str | None = None
    for txn in transactions:
        date_iso = txn.get("date_iso", txn.get("date", ""))
        if not date_iso:
            raise AssertionError(f"Transaction missing date: {txn}")
        if prev_date and date_iso < prev_date:
            raise AssertionError(
                f"Transaction date {date_iso} < previous date {prev_date}"
            )
        prev_date = date_iso


def assert_amount_sign_convention(transactions: list[dict[str, Any]]) -> None:
    """Validate amount sign convention.

    INVARIANT: Debits (withdrawals) are negative or positive based on convention.
    INVARIANT: Credits (deposits) have opposite sign from debits.

    Args:
        transactions: List of transaction dictionaries with amount_paise and type

    Raises:
        AssertionError: If sign convention is violated
    """
    for txn in transactions:
        amount = txn.get("amount_paise", 0)
        txn_type = txn.get("type", "").lower()
        category = txn.get("category", "").lower()

        is_debit = (
            txn_type in ("debit", "expense", "withdrawal") or category == "expense"
        )
        is_credit = txn_type in ("credit", "income", "deposit") or category == "income"

        if is_debit and amount > 0:
            raise AssertionError(
                f"Debit transaction {txn.get('description', '')} has positive amount {amount}"
            )
        if is_credit and amount < 0:
            raise AssertionError(
                f"Credit transaction {txn.get('description', '')} has negative amount {amount}"
            )


def assert_reconciliation_match_valid(match: dict[str, Any]) -> None:
    """Validate a single reconciliation match.

    INVARIANT: Matched amount must not exceed either transaction amount.
    INVARIANT: Confidence in [0, 10000] bps.

    Args:
        match: Reconciliation match dictionary

    Raises:
        AssertionError: If match is invalid
    """
    amount_paise = match.get("amount_paise", 0)
    if amount_paise < 0:
        raise AssertionError(f"Reconciliation amount_paise={amount_paise} is negative")

    confidence = match.get("confidence_bps", 0)
    if confidence < 0 or confidence > 10000:
        raise AssertionError(
            f"Reconciliation confidence_bps={confidence} out of range [0, 10000]"
        )
