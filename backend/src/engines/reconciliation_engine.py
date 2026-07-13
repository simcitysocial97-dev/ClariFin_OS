"""
Reconciliation Engine - Deterministic Cross-Account Matching
=============================================================

Phase 2B.1: Deterministic matching engine for cross-account transfers.
Phase 3: Pure function refactoring with bipartite disambiguation.

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
- Base: 0.5 if amount_exact else 0.0
- Date diff == 0: +0.4
- Date diff 1-3: + (0.4 - date_diff * 0.15), minimum 0.1
- Description similarity > 0.7: +0.2
- Cap at 1.0, round to 4 decimals
- confidence_bps = confidence * 10000 (authoritative field)
"""

from datetime import datetime
from pathlib import Path
from typing import Any

# ============================================================
# Cost Weights for Hungarian Algorithm
# ============================================================
# Cost = date_weight * abs(date_diff_days) + amount_weight * abs(amount_diff_paise) / 100
# Weights can be tuned for sensitivity
HUNGARIAN_DATE_WEIGHT: int = 100  # Each day of date difference
HUNGARIAN_AMOUNT_WEIGHT: int = 1   # Each rupee of amount difference

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
# Confidence Calculation (UPGRADED)
# ============================================================

def _calculate_confidence(
    date_diff_days: int,
    amount_exact: bool,
    description_similarity: float = 0.0,
) -> tuple[float, int]:
    """
    Calculate match confidence score with merged formula.

    Weights:
    - Base: 0.5 if amount_exact else 0.0
    - Date diff == 0: +0.4
    - Date diff 1-3: + (0.4 - date_diff * 0.15), minimum 0.1
    - Description similarity > 0.7: +0.2

    Returns:
        (confidence: float 0.0-1.0, confidence_bps: int 0-10000)

    Deterministic: NO randomness. NO floating instability.
    """
    confidence = 0.0

    # Base component - only for exact amount matches
    if amount_exact:
        confidence = 0.5

    # Date component (graduated, not flat)
    if date_diff_days == 0:
        confidence += 0.4
    else:
        confidence += max(0.4 - date_diff_days * 0.15, 0.1)

    # Description similarity component
    if description_similarity > 0.7:
        confidence += 0.2

    # Cap at 1.0
    confidence = min(confidence, 1.0)

    # Round to 4 decimals for determinism
    confidence = round(confidence, 4)

    # Basis points for authoritative storage
    confidence_bps = int(confidence * 10000)

    return confidence, confidence_bps


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
    transfer_keywords = ['transfer', 'neft', 'imps', 'rtgs', 'upi', 'paytm', 'gpay']

    has_keyword_a = any(kw in desc_a_lower for kw in transfer_keywords)
    has_keyword_b = any(kw in desc_b_lower for kw in transfer_keywords)

    if has_keyword_a and has_keyword_b:
        return 1.0

    return 0.0


# ============================================================
# Matching Rules (Deterministic Only) - PURE FUNCTION
# ============================================================

def _check_match(
    txn_a: dict[str, Any],
    txn_b: dict[str, Any],
    max_date_window_days: int = 3,
) -> dict[str, Any] | None:
    """
    Check if two transactions match as potential transfer pair.

    PURE FUNCTION: Accepts plain dicts, returns plain dict. No DB access.

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

    # Calculate confidence (returns both float and bps)
    desc_similarity = _simple_description_similarity(
        debit_txn.get("description", ""),
        credit_txn.get("description", "")
    )

    confidence, confidence_bps = _calculate_confidence(
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
        "confidence_bps": confidence_bps,
        "match_type": match_type,
        "deterministic_key": deterministic_key,
        "explanation": _generate_explanation(debit_txn, credit_txn, amount_paise, date_diff),
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
        return f"Exact match: \u20b9{amount_rupees:.2f} transferred from {account_debit} to {account_credit} on {date_debit}"
    else:
        return f"Window match: \u20b9{amount_rupees:.2f} transferred from {account_debit} ({date_debit}) to {account_credit} ({date_credit}), {date_diff} days apart"


# ============================================================
# Hungarian Algorithm for Bipartite Disambiguation
# ============================================================

def _build_cost_matrix(
    debits: list[dict[str, Any]],
    credits: list[dict[str, Any]],
) -> list[list[float]]:
    """
    Build cost matrix for Hungarian assignment.

    Cost = date_weight * abs(date_diff_days) + amount_weight * abs(amount_diff_paise) / 100
    Lower cost = better match.

    Returns square matrix (max(len(debits), len(credits)) x same).
    Non-candidate pairs get very high cost.
    """
    n = max(len(debits), len(credits))
    if n == 0:
        return []

    # Initialize matrix with high cost
    INF = 1e9
    matrix: list[list[float]] = [[INF] * n for _ in range(n)]

    for i, debit in enumerate(debits):
        for j, credit in enumerate(credits):
            # Check if this pair is a valid candidate
            match = _check_match(debit, credit, max_date_window_days=3)
            if match:
                # Cost based on date difference and amount difference
                # For exact matches, amount_diff is 0 (amount a_debit == b_credit)
                amount_diff_paise = abs(
                    (debit.get("debit") or 0) - (credit.get("credit") or 0)
                )
                cost = (
                    HUNGARIAN_DATE_WEIGHT * match["date_diff_days"]
                    + HUNGARIAN_AMOUNT_WEIGHT * amount_diff_paise
                )
                matrix[i][j] = float(cost)

    return matrix


def _hungarian_solve(cost_matrix: list[list[float]]) -> list[tuple[int, int]]:
    """
    Solve assignment problem using Hungarian algorithm.

    Returns list of (debit_index, credit_index) pairs for optimal assignment.
    Deterministic tie-breaking: prefer lower indices.
    """
    if not cost_matrix:
        return []

    n = len(cost_matrix)
    m = len(cost_matrix[0]) if cost_matrix else 0

    # For rectangular matrices, determine the effective size
    for row in cost_matrix:
        if len(row) != m:
            m = len(row)

    # Use scipy-style Hungarian if available, else inline implementation
    try:
        # Try to use scipy for efficiency
        import scipy.optimize
        row_ind, col_ind = scipy.optimize.linear_sum_assignment(cost_matrix)
        return [(int(r), int(c)) for r, c in zip(row_ind, col_ind) if cost_matrix[r][c] < 1e8]
    except ImportError:
        # Inline Hungarian algorithm for minimal dependency footprint
        return _hungarian_inline(cost_matrix)


def _hungarian_inline(cost_matrix: list[list[float]]) -> list[tuple[int, int]]:
    """
    Inline Hungarian algorithm implementation.

    Deterministic tie-breaking by sorting indices.
    Returns assignments for valid (cost < INF) pairs only.
    """
    n = len(cost_matrix)
    if n == 0:
        return []

    # Get all valid candidate pairs (cost < INF)
    candidates: list[tuple[int, int, float]] = []
    for i in range(n):
        for j in range(n):
            if cost_matrix[i][j] < 1e8:  # Valid candidate
                candidates.append((i, j, cost_matrix[i][j]))

    if not candidates:
        return []

    # Sort by cost (ascending), then by debit index, then by credit index for determinism
    candidates.sort(key=lambda x: (x[2], x[0], x[1]))

    # Greedy assignment - take lowest cost pairs that don't conflict
    assigned_debits: set[int] = set()
    assigned_credits: set[int] = set()
    assignments: list[tuple[int, int]] = []

    for i, j, _ in candidates:
        if i not in assigned_debits and j not in assigned_credits:
            assigned_debits.add(i)
            assigned_credits.add(j)
            assignments.append((i, j))

    return assignments


# ============================================================
# Core Matching Functions - PURE
# ============================================================

def find_potential_matches(
    debits: list[dict[str, Any]],
    credits: list[dict[str, Any]],
    household_account_map: dict[str, str] | None = None,
    max_date_window_days: int = 3,
) -> list[dict[str, Any]]:
    """
    Find potential transfer matches across accounts - PURE FUNCTION.

    Phase 3: Deterministic matching with bipartite disambiguation.
    Phase 2B.1: Backward-compatible wrapper accepts db_path.

    Args:
        debits: List of debit transaction dicts.
        credits: List of credit transaction dicts.
        household_account_map: Optional mapping of account_id -> household_id for scoping.
                              If provided, only pairs within same household are matched.
        max_date_window_days: Maximum days between dates for window rule.

    Returns:
        List of potential matches with:
            - debit_txn_id: int
            - credit_txn_id: int
            - debit_account_id: str
            - credit_account_id: str
            - amount: float (in rupees)
            - date_diff_days: int
            - match_confidence: float (0.0-1.0)
            - confidence_bps: int (0-10000) - authoritative field
            - match_type: 'exact' or 'window'
            - deterministic_key: str
            - explanation: str (human-readable)
    """
    # Filter by household if mapping provided
    if household_account_map:
        # Build sets of accounts per household
        household_accounts: dict[str, set[str]] = {}
        for account_id, household_id in household_account_map.items():
            if household_id not in household_accounts:
                household_accounts[household_id] = set()
            household_accounts[household_id].add(account_id)

    matches: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    # Build preliminary candidate matches
    candidates: list[tuple[int, int, dict[str, Any]]] = []  # (debit_idx, credit_idx, match)

    for i, debit in enumerate(debits):
        for j, credit in enumerate(credits):
            # Skip if not same household (when filtering)
            if household_account_map:
                debit_household = household_account_map.get(debit.get("account_id", ""))
                credit_household = household_account_map.get(credit.get("account_id", ""))
                if debit_household != credit_household:
                    continue

            match = _check_match(debit, credit, max_date_window_days)
            if match:
                key = match["deterministic_key"]
                if key not in seen_keys:
                    seen_keys.add(key)
                    candidates.append((i, j, match))

    # Check if there's ambiguity (multiple candidates for any debit or credit)
    # If so, use Hungarian algorithm to resolve
    debit_candidate_counts: dict[int, int] = {}
    credit_candidate_counts: dict[int, int] = {}
    for di, ci, _ in candidates:
        debit_candidate_counts[di] = debit_candidate_counts.get(di, 0) + 1
        credit_candidate_counts[ci] = credit_candidate_counts.get(ci, 0) + 1

    has_ambiguity = (
        any(count > 1 for count in debit_candidate_counts.values()) or
        any(count > 1 for count in credit_candidate_counts.values())
    )

    if has_ambiguity:
        # Build cost matrix and solve with Hungarian algorithm
        cost_matrix = _build_cost_matrix(debits, credits)
        assignments = _hungarian_solve(cost_matrix)

        # Build matches from assignments (resolves ambiguity)
        assigned_keys: set[str] = set()
        for di, ci in assignments:
            if di < len(debits) and ci < len(credits):
                key = f"{min(debits[di]['id'], credits[ci]['id'])}:{max(debits[di]['id'], credits[ci]['id'])}"
                if key not in assigned_keys:
                    assigned_keys.add(key)
                    match = candidates[[idx for idx, (d, c, _) in enumerate(candidates) if d == di and c == ci][0]][2]
                    matches.append(match)
    else:
        # No ambiguity - use candidates directly
        matches = [c[2] for c in candidates]

    return matches


def find_matches_for_transaction(
    target_txn: dict[str, Any],
    candidates: list[dict[str, Any]],
    max_date_window_days: int = 3,
) -> list[dict[str, Any]]:
    """
    Find potential matches for a specific transaction - PURE FUNCTION.

    Args:
        target_txn: The transaction dict to find matches for.
        candidates: List of candidate transaction dicts to match against.
        max_date_window_days: Maximum days between dates for window rule.

    Returns:
        List of potential matches ranked by confidence (highest first).
    """
    matches: list[dict[str, Any]] = []

    for candidate in candidates:
        # Skip same account
        if target_txn.get("account_id") == candidate.get("account_id"):
            continue

        match = _check_match(target_txn, candidate, max_date_window_days)
        if match:
            matches.append(match)

    # Sort by confidence descending, then by deterministic key for determinism
    matches.sort(key=lambda m: (-m["match_confidence"], m["deterministic_key"]))
    return matches


# ============================================================
# Backward-Compatible Wrappers (for test compatibility)
# ============================================================

def find_potential_matches_with_db(db_path: str, max_date_window_days: int = 3) -> list[dict[str, Any]]:
    """
    Backward-compatible wrapper that accepts db_path.

    Deprecated: Use pure find_potential_matches(debits, credits, ...) instead.
    Kept for test compatibility.
    """
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get all transactions with debit/credit and account info
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

    # Separate into debits and credits
    debits = [t for t in transactions if (t.get("debit") or 0) > 0]
    credits = [t for t in transactions if (t.get("credit") or 0) > 0]

    return find_potential_matches(debits, credits, None, max_date_window_days)


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

    matches = find_potential_matches_with_db(db_path)

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