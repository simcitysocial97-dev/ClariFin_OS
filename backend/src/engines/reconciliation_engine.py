"""
Reconciliation Engine - Deterministic Cross-Account Matching
=============================================================

Phase 2B.1: Deterministic matching engine for cross-account transfers.

Key Principles:
1. NO ledger mutation - reconciliation is metadata-only
2. NO fuzzy AI scoring - deterministic rules only
3. Confidence calculated from weighted factors
4. All matches are explainable
5. Idempotent - same inputs → same outputs

Matching Rules:
1. Exact Match: Same amount (debit = credit), same date, different accounts
2. Date Window Match: Same amount, date within 3 days, different accounts

Confidence Calculation:
- Exact same date: +0.4
- Within 1 day: +0.3
- Amount exact: +0.4
- Description similarity > 0.7: +0.2
- Cap at 1.0, round to 4 decimals

Usage:
    from engines.reconciliation_engine import find_potential_matches
    matches = find_potential_matches(db_path)
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

# ============================================================
# Date Utilities
# ============================================================


def _parse_date_iso(date_iso: str) -> datetime | None:
    """Parse YYYY-MM-DD date string to datetime."""
    if not date_iso:
        return None
    try:
        return datetime.strptime(date_iso, "%Y-%m-%d")
    except ValueError:
        return None


def _date_difference_days(date_a: str, date_b: str) -> int | None:
    """
    Calculate absolute difference in days between two ISO dates.
    Returns None if either date is invalid.
    """
    dt_a = _parse_date_iso(date_a)
    dt_b = _parse_date_iso(date_b)

    if dt_a is None or dt_b is None:
        return None

    return abs((dt_a - dt_b).days)


# ============================================================
# Confidence Calculation
# ============================================================


def _calculate_confidence(
    date_diff_days: int,
    amount_exact: bool,
    description_similarity: float = 0.0,
) -> float:
    """
    Calculate match confidence score.

    Weights:
    - Exact same date: +0.4
    - Within 1 day: +0.3
    - Amount exact: +0.4
    - Description similarity > 0.7: +0.2

    Cap at 1.0, round to 4 decimals.
    NO randomness. NO floating instability.
    """
    confidence = 0.0

    # Date factor
    if date_diff_days == 0:
        confidence += 0.4  # Exact same date
    elif date_diff_days == 1:
        confidence += 0.3  # Within 1 day

    # Amount factor
    if amount_exact:
        confidence += 0.4

    # Description similarity factor
    if description_similarity > 0.7:
        confidence += 0.2

    # Cap at 1.0
    confidence = min(confidence, 1.0)

    # Round to 4 decimals for determinism
    return round(confidence, 4)


def _simple_description_similarity(desc_a: str, desc_b: str) -> float:
    """
    Simple text similarity check.
    Returns 1.0 if both contain common transfer keywords, 0.0 otherwise.

    This is a deterministic check, not ML-based.
    """
    if not desc_a or not desc_b:
        return 0.0

    desc_a_lower = desc_a.lower()
    desc_b_lower = desc_b.lower()

    # Common transfer-related keywords
    transfer_keywords = ["transfer", "neft", "imps", "rtgs", "upi", "paytm", "gpay"]

    has_keyword_a = any(kw in desc_a_lower for kw in transfer_keywords)
    has_keyword_b = any(kw in desc_b_lower for kw in transfer_keywords)

    if has_keyword_a and has_keyword_b:
        return 1.0

    return 0.0


# ============================================================
# Matching Rules (Deterministic Only)
# ============================================================


def _check_match(
    txn_a: dict[str, Any], txn_b: dict[str, Any], max_date_window_days: int = 3
) -> dict[str, Any] | None:
    """
    Check if two transactions match as potential transfer pair.

    Returns match details if matched, None otherwise.

    Matching Criteria:
    - Opposite sign amounts (abs(debit) == abs(credit))
    - Different account_id
    - Date difference <= max_date_window_days
    """
    # Must be different accounts
    if txn_a["account_id"] == txn_b["account_id"]:
        return None

    # Get debit/credit values
    a_debit = txn_a.get("debit") or 0
    a_credit = txn_a.get("credit") or 0
    b_debit = txn_b.get("debit") or 0
    b_credit = txn_b.get("credit") or 0

    # Determine which is debit and which is credit
    debit_txn = None
    credit_txn = None
    amount_paise = 0

    if a_debit > 0 and b_credit > 0 and a_debit == b_credit:
        debit_txn = txn_a
        credit_txn = txn_b
        amount_paise = a_debit
    elif a_credit > 0 and b_debit > 0 and a_credit == b_debit:
        debit_txn = txn_b
        credit_txn = txn_a
        amount_paise = a_credit

    if debit_txn is None or credit_txn is None:
        return None  # No match

    # Check dates
    date_debit = debit_txn.get("date_iso") or ""
    date_credit = credit_txn.get("date_iso") or ""

    if not date_debit or not date_credit:
        return None

    date_diff = _date_difference_days(date_debit, date_credit)
    if date_diff is None:
        return None

    if date_diff > max_date_window_days:
        return None

    # Determine match type
    if date_diff == 0:
        match_type = "exact"
    else:
        match_type = "window"

    # Calculate confidence
    desc_similarity = _simple_description_similarity(
        debit_txn.get("description", ""), credit_txn.get("description", "")
    )

    confidence = _calculate_confidence(
        date_diff_days=date_diff,
        amount_exact=True,  # We already verified amount match
        description_similarity=desc_similarity,
    )

    # Generate deterministic key
    min_id = min(debit_txn["id"], credit_txn["id"])
    max_id = max(debit_txn["id"], credit_txn["id"])
    deterministic_key = f"{min_id}:{max_id}"

    return {
        "debit_txn_id": debit_txn["id"],
        "credit_txn_id": credit_txn["id"],
        "debit_account_id": debit_txn["account_id"],
        "credit_account_id": credit_txn["account_id"],
        "amount": amount_paise / 100,  # Convert to rupees
        "date_diff_days": date_diff,
        "match_confidence": confidence,
        "match_type": match_type,
        "deterministic_key": deterministic_key,
        "explanation": _generate_explanation(
            debit_txn, credit_txn, amount_paise, date_diff
        ),
    }


def _generate_explanation(
    debit_txn: dict[str, Any],
    credit_txn: dict[str, Any],
    amount_paise: int,
    date_diff: int,
) -> str:
    """Generate human-readable explanation for a match."""
    amount_rupees = amount_paise / 100

    date_debit = debit_txn.get("date_iso", "?")
    date_credit = credit_txn.get("date_iso", "?")

    account_debit = debit_txn.get("account_id", "?")
    account_credit = credit_txn.get("account_id", "?")

    if date_diff == 0:
        return f"Exact match: ₹{amount_rupees:.2f} transferred from {account_debit} to {account_credit} on {date_debit}"
    else:
        return f"Window match: ₹{amount_rupees:.2f} transferred from {account_debit} ({date_debit}) to {account_credit} ({date_credit}), {date_diff} days apart"


# ============================================================
# Core Matching Functions
# ============================================================


def find_potential_matches(
    db_path: str, max_date_window_days: int = 3
) -> list[dict[str, Any]]:
    """
    Find potential transfer matches across accounts.

    Phase 2B.1: Deterministic matching only. No ML, no fuzzy scoring.

    Args:
        db_path: Path to SQLite database
        max_date_window_days: Maximum days between dates for window rule

    Returns:
        List of potential matches with:
            - debit_txn_id: int
            - credit_txn_id: int
            - debit_account_id: str
            - credit_account_id: str
            - amount: float (in rupees)
            - date_diff_days: int
            - match_confidence: float (0.0-1.0)
            - match_type: 'exact' or 'window'
            - deterministic_key: str
            - explanation: str (human-readable)
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get all transactions with debit/credit and account info
    # Ordered deterministically: amount ASC, date_iso ASC, id ASC
    cur = conn.execute("""
        SELECT
            id, date_iso, description, debit, credit, account_id
        FROM transactions
        WHERE account_id IS NOT NULL AND account_id != ''
          AND (debit > 0 OR credit > 0)
          AND date_iso IS NOT NULL AND date_iso != ''
        ORDER BY
            (debit + credit) ASC,
            date_iso ASC,
            id ASC
    """)

    transactions = [dict(row) for row in cur.fetchall()]
    conn.close()

    matches = []
    seen_keys = set()

    # Compare all pairs
    for i, txn_a in enumerate(transactions):
        for txn_b in transactions[i + 1 :]:
            # Check for match
            match = _check_match(txn_a, txn_b, max_date_window_days)

            if match:
                key = match["deterministic_key"]
                if key not in seen_keys:
                    seen_keys.add(key)
                    matches.append(match)

    return matches


def find_matches_for_transaction(
    db_path: str, txn_id: int, max_date_window_days: int = 3
) -> list[dict[str, Any]]:
    """
    Find potential matches for a specific transaction.

    Args:
        db_path: Path to SQLite database
        txn_id: Transaction ID to find matches for
        max_date_window_days: Maximum days between dates for window rule

    Returns:
        List of potential matches
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get the target transaction
    cur = conn.execute(
        """
        SELECT
            id, date_iso, description, debit, credit, account_id
        FROM transactions
        WHERE id = ?
    """,
        (txn_id,),
    )

    target = cur.fetchone()
    if not target:
        conn.close()
        return []

    target_dict = dict(target)
    target_debit = target_dict.get("debit") or 0
    target_credit = target_dict.get("credit") or 0

    # Find potential matching transactions
    # Must be opposite type with same amount
    if target_debit > 0:
        amount_to_match = target_debit
        match_condition = "credit = ?"
    elif target_credit > 0:
        amount_to_match = target_credit
        match_condition = "debit = ?"
    else:
        conn.close()
        return []

    cur = conn.execute(
        f"""
        SELECT
            id, date_iso, description, debit, credit, account_id
        FROM transactions
        WHERE id != ?
          AND account_id != ?
          AND account_id IS NOT NULL AND account_id != ''
          AND {match_condition}
          AND date_iso IS NOT NULL AND date_iso != ''
        ORDER BY date_iso ASC, id ASC
    """,
        (txn_id, target_dict["account_id"], amount_to_match),
    )

    candidates = [dict(row) for row in cur.fetchall()]
    conn.close()

    matches = []

    for candidate in candidates:
        match = _check_match(target_dict, candidate, max_date_window_days)
        if match:
            matches.append(match)

    return matches


# ============================================================
# CLI Test
# ============================================================

if __name__ == "__main__":
    db_path = str(Path(__file__).parent.parent / "data" / "finance.db")

    print("=" * 60)
    print("Reconciliation Engine Test")
    print("=" * 60)
    print(f"Database: {db_path}")
    print()

    matches = find_potential_matches(db_path)

    if matches:
        print(f"Found {len(matches)} potential matches:")
        for m in matches[:10]:
            print(f"  [{m['match_type']}] {m['deterministic_key']}")
            print(f"    Confidence: {m['match_confidence']:.2%}")
            print(f"    {m['explanation']}")
        if len(matches) > 10:
            print(f"  ... and {len(matches) - 10} more matches")
    else:
        print("No potential matches found.")
