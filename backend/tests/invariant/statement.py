"""Statement Invariants - Date integrity, amount validation."""
from __future__ import annotations

from typing import Any


def assert_statement_integrity(statement: dict[str, Any]) -> None:
    """Validate statement format and required fields.

    INVARIANT: Statement must have valid date and amount fields.

    Args:
        statement: Statement dictionary to validate

    Raises:
        AssertionError: If statement violates invariants
    """
    from .money import assert_money_invariants

    assert_money_invariants(statement)

    # Statement cycle day must be valid (1-31)
    if "statement_cycle_day" in statement:
        day = statement["statement_cycle_day"]
        if day is not None and (day < 1 or day > 31):
            raise AssertionError(f"Invalid statement_cycle_day: {day}")


def assert_statement_detection_invariants(result: dict[str, Any]) -> None:
    """Validate statement detection engine output invariants.

    INVARIANT: Detected statement amounts must be non-negative.
    INVARIANT: Confidence in valid bps range.

    Args:
        result: Detection result from statement engine

    Raises:
        AssertionError: If detection violates invariants
    """
    if "total_outstanding_paise" in result:
        if result["total_outstanding_paise"] < 0:
            raise AssertionError("total_outstanding_paise cannot be negative")

    if "confidence_bps" in result:
        if result["confidence_bps"] < 0 or result["confidence_bps"] > 10000:
            raise AssertionError(f"confidence_bps out of range: {result['confidence_bps']}")
