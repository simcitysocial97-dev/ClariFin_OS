"""
Validation Engine - Deterministic Statement Validation
=======================================================

Phase B0: Deterministic delta helper for statement validation.

Key Principles:
1. Pure functions - no side effects
2. Integer-only arithmetic - no floating-point
3. Deterministic - same inputs always produce same output
4. Works for any statement type (PDF, Excel, CSV)

Usage:
    from engines.validation_engine import compute_statement_delta_paise
    delta = compute_statement_delta_paise(
        opening_balance_paise=100000,  # ₹1000.00
        closing_balance_paise=50000,   # ₹500.00
        credits_paise=[200000],         # ₹2000.00 credit
        debits_paise=[250000],          # ₹2500.00 debit
    )
    # delta == 0 → statement is balanced
    # delta != 0 → statement has discrepancy
"""

from typing import List


def compute_statement_delta_paise(
    opening_balance_paise: int,
    closing_balance_paise: int,
    credits_paise: List[int],
    debits_paise: List[int],
) -> int:
    """
    Compute the delta (discrepancy) between expected and actual closing balance.

    Formula:
        expected_closing = opening + sum(credits) - sum(debits)
        delta = expected_closing - actual_closing

    Args:
        opening_balance_paise: Opening balance in paise (1 rupee = 100 paise)
        closing_balance_paise: Closing balance in paise
        credits_paise: List of credit amounts in paise (money in)
        debits_paise: List of debit amounts in paise (money out)

    Returns:
        Delta in paise. Zero indicates a balanced statement.
        Positive delta: Expected closing > Actual closing (missing money)
        Negative delta: Expected closing < Actual closing (extra money)

    Example:
        >>> compute_statement_delta_paise(
        ...     opening_balance_paise=100000,   # ₹1000.00
        ...     closing_balance_paise=50000,    # ₹500.00
        ...     credits_paise=[200000],          # ₹2000.00 in
        ...     debits_paise=[250000],           # ₹2500.00 out
        ... )
        0  # Balanced: 1000 + 2000 - 2500 = 500

        >>> compute_statement_delta_paise(
        ...     opening_balance_paise=100000,
        ...     closing_balance_paise=60000,    # Discrepancy: says ₹600
        ...     credits_paise=[200000],
        ...     debits_paise=[250000],
        ... )
        -10000  # ₹100 discrepancy (expected 500, got 600)
    """
    # Integer-only arithmetic for determinism
    total_credits = sum(credits_paise) if credits_paise else 0
    total_debits = sum(debits_paise) if debits_paise else 0

    # Expected closing balance based on transaction flow
    expected_closing_paise = opening_balance_paise + total_credits - total_debits

    # Delta: positive means missing money, negative means extra money
    delta_paise = expected_closing_paise - closing_balance_paise

    return delta_paise


def is_statement_balanced(
    opening_balance_paise: int,
    closing_balance_paise: int,
    credits_paise: List[int],
    debits_paise: List[int],
    tolerance_paise: int = 0,
) -> bool:
    """
    Check if a statement is balanced within a tolerance.

    Args:
        opening_balance_paise: Opening balance in paise
        closing_balance_paise: Closing balance in paise
        credits_paise: List of credit amounts in paise
        debits_paise: List of debit amounts in paise
        tolerance_paise: Acceptable discrepancy in paise (default: 0)

    Returns:
        True if |delta| <= tolerance, False otherwise

    Example:
        >>> is_statement_balanced(
        ...     opening_balance_paise=100000,
        ...     closing_balance_paise=50000,
        ...     credits_paise=[200000],
        ...     debits_paise=[250000],
        ... )
        True

        >>> is_statement_balanced(
        ...     opening_balance_paise=100000,
        ...     closing_balance_paise=50100,  # ₹1.00 off
        ...     credits_paise=[200000],
        ...     debits_paise=[250000],
        ...     tolerance_paise=100,  # Allow ₹1.00 tolerance
        ... )
        True
    """
    delta = compute_statement_delta_paise(
        opening_balance_paise=opening_balance_paise,
        closing_balance_paise=closing_balance_paise,
        credits_paise=credits_paise,
        debits_paise=debits_paise,
    )
    return abs(delta) <= tolerance_paise


def compute_statement_summary(
    opening_balance_paise: int,
    closing_balance_paise: int,
    credits_paise: List[int],
    debits_paise: List[int],
) -> dict:
    """
    Compute a full summary of statement validation.

    Args:
        opening_balance_paise: Opening balance in paise
        closing_balance_paise: Closing balance in paise
        credits_paise: List of credit amounts in paise
        debits_paise: List of debit amounts in paise

    Returns:
        Dict with:
            - opening_balance_paise: int
            - closing_balance_paise: int
            - total_credits_paise: int
            - total_debits_paise: int
            - transaction_count: int
            - expected_closing_paise: int
            - delta_paise: int
            - is_balanced: bool

    Example:
        >>> compute_statement_summary(
        ...     opening_balance_paise=100000,
        ...     closing_balance_paise=50000,
        ...     credits_paise=[200000],
        ...     debits_paise=[250000],
        ... )
        {
            'opening_balance_paise': 100000,
            'closing_balance_paise': 50000,
            'total_credits_paise': 200000,
            'total_debits_paise': 250000,
            'transaction_count': 2,
            'expected_closing_paise': 50000,
            'delta_paise': 0,
            'is_balanced': True,
        }
    """
    total_credits = sum(credits_paise) if credits_paise else 0
    total_debits = sum(debits_paise) if debits_paise else 0
    expected_closing = opening_balance_paise + total_credits - total_debits
    delta = expected_closing - closing_balance_paise

    return {
        "opening_balance_paise": opening_balance_paise,
        "closing_balance_paise": closing_balance_paise,
        "total_credits_paise": total_credits,
        "total_debits_paise": total_debits,
        "transaction_count": len(credits_paise) + len(debits_paise),
        "expected_closing_paise": expected_closing,
        "delta_paise": delta,
        "is_balanced": delta == 0,
    }
