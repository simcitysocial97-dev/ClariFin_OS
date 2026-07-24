"""Behaviour Invariants — Score ranges, normalized metrics, temporal consistency."""
from __future__ import annotations

from typing import Any


def assert_behaviour_score_valid(score: int | float, score_name: str = "score") -> None:
    """Validate behaviour score is in valid range [0, 100].

    INVARIANT: Behaviour scores are integers or floats in [0, 100].

    Args:
        score: Score value to validate
        score_name: Human-readable name for error messages

    Raises:
        AssertionError: If score is out of range
    """
    if not isinstance(score, (int, float)):
        raise AssertionError(f"{score_name}={score} must be numeric, got {type(score).__name__}")
    if score < 0 or score > 100:
        raise AssertionError(f"{score_name}={score} out of range [0, 100]")


def assert_wellness_metrics_valid(metrics: dict[str, Any]) -> None:
    """Validate behaviour wellness metrics.

    INVARIANT: All wellness sub-scores are in [0, 100].
    INVARIANT: Overall wellness is weighted average of sub-scores.

    Args:
        metrics: Wellness metrics dictionary

    Raises:
        AssertionError: If metrics violate invariants
    """
    score_fields = [
        "financial_wellness_score",
        "resilience_score",
        "savings_score",
        "debt_management_score",
        "income_stability_score",
        "overall_wellness_score",
    ]
    for field in score_fields:
        if field in metrics and metrics[field] is not None:
            value = metrics[field]
            if not isinstance(value, (int, float)):
                raise AssertionError(
                    f"{field}={value} must be numeric, got {type(value).__name__}"
                )
            if value < 0 or value > 100:
                raise AssertionError(f"{field}={value} out of range [0, 100]")


def assert_temporal_pattern_consistency(transactions: list[dict[str, Any]]) -> None:
    """Validate temporal pattern consistency in transaction list.

    INVARIANT: Transactions are sorted by date ascending.
    INVARIANT: No duplicate dates for same description+amount combination.

    Args:
        transactions: List of transaction dictionaries with date/description/amount

    Raises:
        AssertionError: If temporal patterns are inconsistent
    """
    if not transactions:
        return

    seen: set[tuple[str, str, int]] = set()
    prev_date: str | None = None

    for txn in transactions:
        date_iso = txn.get("date_iso", txn.get("date", ""))
        if prev_date and date_iso < prev_date:
            raise AssertionError(
                f"Transactions not sorted: {date_iso} < {prev_date}"
            )
        prev_date = date_iso

        desc = txn.get("description", "")
        amount = txn.get("amount_paise", 0)
        key = (date_iso, desc, amount)
        if key in seen:
            raise AssertionError(
                f"Duplicate transaction: date={date_iso}, desc={desc}, amount={amount}"
            )
        seen.add(key)


def assert_credit_dependency_ratio_valid(ratio: float) -> None:
    """Validate credit dependency ratio is in [0, 1].

    INVARIANT: Credit dependency ratio must be between 0 and 1 inclusive.

    Args:
        ratio: Credit dependency ratio

    Raises:
        AssertionError: If ratio is out of range
    """
    if not isinstance(ratio, (int, float)):
        raise AssertionError(
            f"credit_dependency_ratio={ratio} must be numeric, got {type(ratio).__name__}"
        )
    if ratio < 0 or ratio > 1:
        raise AssertionError(
            f"credit_dependency_ratio={ratio} out of range [0, 1]"
        )
