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

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from src.logger import log
from src.utils import parse_date_to_iso, parse_date_for_sort, format_paise

if TYPE_CHECKING:
    from db import FinanceDB


# ============================================================
# Core Balance Functions
# ============================================================

def compute_running_balance(
    db: "FinanceDB",
    account_id: Optional[str] = None,
    starting_balance_paise: int = 0,
) -> List[Dict]:
    """
    Compute running balance by replaying all transactions chronologically.
    
    Phase 2A.1: Uses SQL ORDER BY date_iso ASC, id ASC for deterministic replay.
    No Python-side sorting - all ordering is database-enforced.
    
    Args:
        db: FinanceDB instance
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
    log.info("Computing running balance for account %s", account_id)
    
    # Check for empty transactions
    with db.connection() as conn:
        if account_id:
            cur = conn.execute("SELECT 1 FROM transactions WHERE account_id = ? LIMIT 1", (account_id,))
        else:
            cur = conn.execute("SELECT 1 FROM transactions LIMIT 1")
        if not cur.fetchone():
            log.warning("No transactions found for balance computation")
            return []
    
    # Phase 2A.2: Account-scoped determinism
    # Query directly by account_id - no JOIN needed
    # Uses idx_account_date_iso index for optimal performance
    with db.connection() as conn:
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
            "date_iso": row.get("date_iso") or parse_date_to_iso(row["date"]),
            "description": row["description"],
            "debit_paise": debit,
            "credit_paise": credit,
            "balance_paise": balance,
            "bank": row["bank"],
        })
    
    return results


def compute_account_balance(
    db: "FinanceDB",
    account_id: str,
    starting_balance_paise: int = 0,
) -> Dict:
    """
    Compute current balance for a single account.
    
    Args:
        db: FinanceDB instance
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
    with db.connection() as conn:
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
    
    total_debit = row["total_debit"] or 0
    total_credit = row["total_credit"] or 0
    count = row["count"] or 0
    
    balance = starting_balance_paise + total_credit - total_debit
    
    return {
        "account_id": account_id,
        "balance_paise": balance,
        "balance_display": format_paise(balance),
        "total_debit_paise": total_debit,
        "total_credit_paise": total_credit,
        "transaction_count": count,
    }


def validate_statement_balance(
    db: "FinanceDB",
    statement_id: int,
    claimed_closing_balance_paise: int,
) -> Dict:
    """
    Validate a statement's closing balance against computed balance.
    
    This compares the statement's claimed closing balance against the
    computed balance from replaying all transactions in that statement.
    
    Args:
        db: FinanceDB instance
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
    with db.connection() as conn:
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
        "computed_balance_display": format_paise(computed_balance),
        "claimed_balance_paise": claimed_closing_balance_paise,
        "claimed_balance_display": format_paise(claimed_closing_balance_paise),
        "difference_paise": difference,
        "difference_display": format_paise(difference),
        "transaction_count": len(rows),
    }


def get_accounts_list(db: "FinanceDB") -> List[Dict]:
    """
    Get list of all accounts (banks) with their current balances.
    
    Args:
        db: FinanceDB instance
    
    Returns:
        List of dicts with account info and balances.
    """
    with db.connection() as conn:
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
            "balance_display": format_paise(balance),
        })
    
    return results


# ============================================================
# CLI Test
# ============================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Import FinanceDB for CLI testing
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from db import FinanceDB
    
    # Default db path
    db_path = str(Path(__file__).parent.parent / "data" / "finance.db")
    db = FinanceDB(db_path)
    
    log.info("=" * 60)
    log.info("Balance Engine Test")
    log.info("=" * 60)
    log.info("Database: %s", db_path)
    
    # Get accounts
    accounts = get_accounts_list(db)
    log.info("Found %d accounts:", len(accounts))
    for acc in accounts:
        log.info("  %s: %s (%d txns)", acc['bank'], acc['balance_display'], acc['transaction_count'])
    
    # Show running balance for first account if exists
    if accounts:
        first_account = accounts[0]["bank"]
        log.info("Running balance for %s:", first_account)
        running = compute_running_balance(db, first_account)
        for r in running[:10]:  # Show first 10
            log.info("  %s | %s | D:%.2f C:%.2f | Bal: %.2f",
                r['date_iso'], r['description'][:30],
                r['debit_paise']/100, r['credit_paise']/100,
                r['balance_paise']/100)
        if len(running) > 10:
            log.info("  ... and %d more transactions", len(running) - 10)
    
    db.close()
