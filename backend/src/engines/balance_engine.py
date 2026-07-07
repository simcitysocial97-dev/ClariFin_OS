"""
Balance Engine - Deterministic Financial Balance Computation
=============================================================

This module provides mathematically deterministic balance calculations
for the ClariFin OS personal finance tracker.

Key Principles:
1. All amounts are stored as INTEGER paise (1 rupee = 100 paise)
2. No floating-point arithmetic - all calculations use integers
3. Balances are computed by replaying transactions chronologically
4. Mismatches are flagged, never silently corrected

Usage:
    from engines.balance_engine import compute_running_balance, validate_statement_balance
"""

import sqlite3
from datetime import datetime
from pathlib import Path

# ============================================================
# Date Parsing (consistent with db.py)
# ============================================================

def _parse_date_to_ymd(date_str: str) -> str:
    """
    Parse Indian date formats to YYYY-MM-DD for sorting.
    Returns empty string if unparseable.
    """
    if not date_str:
        return ""

    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
        "%d %b %Y", "%d %b %y", "%d-%b-%Y", "%d-%b-%y",
        "%Y-%m-%d",
    ]
    s = date_str.strip()
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def _parse_date_for_sort(date_str: str) -> tuple[str, int]:
    """
    Parse date for sorting. Returns (ymd_string, original_id_for_tiebreaker).
    Used to sort transactions chronologically while preserving insertion order for same-date txns.
    """
    ymd = _parse_date_to_ymd(date_str)
    return ymd if ymd else "0000-00-00"


# ============================================================
# Core Balance Functions
# ============================================================

def compute_running_balance(
    db_path: str,
    account_id: str | None = None,
    starting_balance_paise: int = 0,
) -> list[dict]:
    """
    Compute running balance by replaying all transactions chronologically.

    Phase 2A.1: Uses SQL ORDER BY date_iso ASC, id ASC for deterministic replay.
    No Python-side sorting - all ordering is database-enforced.

    Args:
        db_path: Path to SQLite database
        account_id: Optional bank/account name to filter transactions
        starting_balance_paise: Opening balance in paise (default 0)

    Returns:
        List of dicts with keys:
            - transaction_id: int
            - date: str (original format)
            - date_iso: str (YYYY-MM-DD)
            - description: str
            - debit_paise: int
            - credit_paise: int
            - balance_paise: int (running balance after this transaction)
            - bank: str
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Phase 2A.2: Account-scoped determinism
    # Query directly by account_id - no JOIN needed
    # Uses idx_account_date_iso index for optimal performance
    if account_id:
        sql = """
            SELECT
                t.id, t.date, t.date_iso, t.description, t.debit, t.credit, t.amount_paise,
                t.account_id as bank
            FROM transactions t
            WHERE t.account_id = ?
            ORDER BY t.date_iso ASC, t.id ASC
        """
        cur = conn.execute(sql, (account_id,))
    else:
        sql = """
            SELECT
                t.id, t.date, t.date_iso, t.description, t.debit, t.credit, t.amount_paise,
                t.account_id as bank
            FROM transactions t
            ORDER BY t.date_iso ASC, t.id ASC
        """
        cur = conn.execute(sql)

    rows = [dict(row) for row in cur.fetchall()]
    conn.close()

    # Compute running balance (no sorting needed - SQL already ordered)
    balance = starting_balance_paise
    results = []

    for row in rows:
        debit = row.get("debit") or 0
        credit = row.get("credit") or 0

        # Net effect: credit increases balance, debit decreases
        balance += credit - debit

        results.append({
            "transaction_id": row["id"],
            "date": row["date"],
            "date_iso": row.get("date_iso") or _parse_date_to_ymd(row["date"]),
            "description": row["description"],
            "debit_paise": debit,
            "credit_paise": credit,
            "balance_paise": balance,
            "bank": row["bank"],
        })

    return results


def compute_account_balance(
    db_path: str,
    account_id: str,
    starting_balance_paise: int = 0,
) -> dict:
    """
    Compute current balance for a single account.

    Args:
        db_path: Path to SQLite database
        account_id: Bank/account name
        starting_balance_paise: Opening balance in paise

    Returns:
        Dict with keys:
            - account_id: str
            - balance_paise: int
            - balance_display: str (formatted INR)
            - total_debit_paise: int
            - total_credit_paise: int
            - transaction_count: int
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Phase 2A.2: Query directly by account_id - no JOIN needed
    sql = """
        SELECT
            COUNT(*) as count,
            COALESCE(SUM(t.debit), 0) as total_debit,
            COALESCE(SUM(t.credit), 0) as total_credit
        FROM transactions t
        WHERE t.account_id = ?
    """
    cur = conn.execute(sql, (account_id,))
    row = cur.fetchone()
    conn.close()

    total_debit = row["total_debit"] or 0
    total_credit = row["total_credit"] or 0
    count = row["count"] or 0

    balance = starting_balance_paise + total_credit - total_debit

    return {
        "account_id": account_id,
        "balance_paise": balance,
        "balance_display": _format_paise(balance),
        "total_debit_paise": total_debit,
        "total_credit_paise": total_credit,
        "transaction_count": count,
    }


def validate_statement_balance(
    db_path: str,
    statement_id: int,
    claimed_closing_balance_paise: int,
) -> dict:
    """
    Validate a statement's closing balance against computed balance.

    This compares the statement's claimed closing balance against the
    computed balance from replaying all transactions in that statement.

    Args:
        db_path: Path to SQLite database
        statement_id: Statement ID to validate
        claimed_closing_balance_paise: The statement's claimed closing balance

    Returns:
        Dict with keys:
            - statement_id: int
            - status: 'match' | 'mismatch'
            - computed_balance_paise: int
            - claimed_balance_paise: int
            - difference_paise: int
            - difference_display: str
            - transaction_count: int
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get all transactions for this statement
    sql = """
        SELECT
            t.id, t.debit, t.credit,
            s.bank
        FROM transactions t
        JOIN statements s ON t.statement_id = s.id
        WHERE t.statement_id = ?
        ORDER BY t.id ASC
    """
    cur = conn.execute(sql, (statement_id,))
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()

    # Compute balance from transactions
    computed_balance = 0
    for row in rows:
        debit = row.get("debit") or 0
        credit = row.get("credit") or 0
        computed_balance += credit - debit

    difference = abs(computed_balance - claimed_closing_balance_paise)

    return {
        "statement_id": statement_id,
        "status": "match" if difference == 0 else "mismatch",
        "computed_balance_paise": computed_balance,
        "computed_balance_display": _format_paise(computed_balance),
        "claimed_balance_paise": claimed_closing_balance_paise,
        "claimed_balance_display": _format_paise(claimed_closing_balance_paise),
        "difference_paise": difference,
        "difference_display": _format_paise(difference),
        "transaction_count": len(rows),
    }


def get_accounts_list(db_path: str) -> list[dict]:
    """
    Get list of all accounts (banks) with their current balances.

    Args:
        db_path: Path to SQLite database

    Returns:
        List of dicts with account info and balances.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    sql = """
        SELECT
            s.bank,
            COUNT(t.id) as transaction_count,
            COALESCE(SUM(t.debit), 0) as total_debit,
            COALESCE(SUM(t.credit), 0) as total_credit
        FROM statements s
        LEFT JOIN transactions t ON t.statement_id = s.id
        GROUP BY s.bank
        ORDER BY s.bank
    """
    cur = conn.execute(sql)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()

    results = []
    for row in rows:
        total_debit = row["total_debit"] or 0
        total_credit = row["total_credit"] or 0
        balance = total_credit - total_debit  # Assuming 0 starting balance

        results.append({
            "account_id": row["bank"],
            "bank": row["bank"],
            "transaction_count": row["transaction_count"],
            "total_debit_paise": total_debit,
            "total_credit_paise": total_credit,
            "balance_paise": balance,
            "balance_display": _format_paise(balance),
        })

    return results


# ============================================================
# Formatting Utilities
# ============================================================

def _format_paise(paise: int) -> str:
    """
    Format paise as Indian Rupee string with lakh/crore grouping.

    Examples:
        123456 -> "₹1,234.56"
        10000000 -> "₹1,00,000.00"
    """
    if paise is None:
        return "₹0.00"

    negative = paise < 0
    paise = abs(paise)

    rupees = paise // 100
    paise_part = paise % 100

    # Format with Indian grouping (lakhs, crores)
    if rupees <= 999:
        formatted = str(rupees)
    else:
        s = str(rupees)
        last3 = s[-3:]
        remaining = s[:-3]
        groups = []
        while remaining:
            groups.append(remaining[-2:] if len(remaining) >= 2 else remaining)
            remaining = remaining[:-2]
        groups.reverse()
        formatted = ",".join(groups) + "," + last3

    result = f"₹{formatted}.{paise_part:02d}"
    return f"-{result}" if negative else result


# ============================================================
# CLI Test
# ============================================================

if __name__ == "__main__":
    from pathlib import Path

    # Default db path
    db_path = str(Path(__file__).parent.parent / "data" / "finance.db")

    print("=" * 60)
    print("Balance Engine Test")
    print("=" * 60)
    print(f"Database: {db_path}")
    print()

    # Get accounts
    accounts = get_accounts_list(db_path)
    print(f"Found {len(accounts)} accounts:")
    for acc in accounts:
        print(f"  {acc['bank']}: {acc['balance_display']} ({acc['transaction_count']} txns)")

    print()

    # Show running balance for first account if exists
    if accounts:
        first_account = accounts[0]["bank"]
        print(f"Running balance for {first_account}:")
        running = compute_running_balance(db_path, first_account)
        for r in running[:10]:  # Show first 10
            print(f"  {r['date_ymd']} | {r['description'][:30]:30s} | D:{r['debit_paise']/100:8.2f} C:{r['credit_paise']/100:8.2f} | Bal: {r['balance_paise']/100:.2f}")
        if len(running) > 10:
            print(f"  ... and {len(running) - 10} more transactions")
