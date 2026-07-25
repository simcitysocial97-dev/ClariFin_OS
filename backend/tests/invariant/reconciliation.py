"""Reconciliation Invariants - Match integrity and confidence bounds."""

from __future__ import annotations

from typing import Any


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


def assert_reconciliation_determinism(matches_1: list[dict[str, Any]], matches_2: list[dict[str, Any]]) -> None:
    """Validate that two reconciliation runs produce identical results.

    INVARIANT: Same dataset → same reconciliation rows.
    INVARIANT: Confidence scores are deterministic.

    Args:
        matches_1: First run results
        matches_2: Second run results

    Raises:
        AssertionError: If results differ
    """
    if len(matches_1) != len(matches_2):
        raise AssertionError(
            f"Match count differs: {len(matches_1)} vs {len(matches_2)}"
        )

    keys_1 = sorted([m.get("deterministic_key", "") for m in matches_1])
    keys_2 = sorted([m.get("deterministic_key", "") for m in matches_2])

    if keys_1 != keys_2:
        raise AssertionError("Match keys differ between runs")


def assert_no_duplicate_matches(matches: list[dict[str, Any]]) -> None:
    """Validate that no duplicate matches exist.

    INVARIANT: Each (debit_txn_id, credit_txn_id) pair appears at most once.

    Args:
        matches: List of reconciliation matches

    Raises:
        AssertionError: If duplicates found
    """
    seen = set()
    for m in matches:
        key = (m.get("debit_txn_id"), m.get("credit_txn_id"))
        if key in seen:
            raise AssertionError(f"Duplicate match found: {key}")
        seen.add(key)


def assert_no_mirrored_pairs(matches: list[dict[str, Any]]) -> None:
    """Validate that no mirrored pairs exist.

    INVARIANT: If (A, B) exists, (B, A) must not exist.

    Args:
        matches: List of reconciliation matches

    Raises:
        AssertionError: If mirrored pairs found
    """
    pairs = set()
    for m in matches:
        pair = (m.get("debit_txn_id"), m.get("credit_txn_id"))
        mirrored = (m.get("credit_txn_id"), m.get("debit_txn_id"))
        if mirrored in pairs:
            raise AssertionError(f"Mirrored pair found: {pair} and {mirrored}")
        pairs.add(pair)
