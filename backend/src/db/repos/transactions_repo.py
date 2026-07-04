"""Transactions repository - CRUD operations for transactions.

This module provides database operations for transaction management,
including bulk inserts, queries, and aggregations.
"""

import hashlib
import sqlite3
from typing import List, Dict, Optional

from src.logger import log
from src.utils import parse_date_to_iso, parse_amount_to_float


def _parse_date_to_ymd(date_str: str) -> str:
    """Parse Indian date formats to YYYY-MM-DD for sorting/grouping."""
    result = parse_date_to_iso(date_str)
    return result if result is not None else ""


def _parse_amount(raw: str) -> float:
    """Convert amount string to float. Removes commas, handles empty."""
    return parse_amount_to_float(raw)


def insert_transactions(
    conn: sqlite3.Connection,
    statement_id: int,
    transactions: List[Dict]
) -> int:
    """Bulk insert transactions. Deduplicates by hash_signature.
    
    Args:
        conn: Database connection
        statement_id: The statement ID to associate with transactions
        transactions: List of transaction dicts with keys:
            - date: Transaction date string
            - description: Transaction description
            - amount: Transaction amount string/number
            - type: 'debit' or 'credit'
            - category: Transaction category (optional)
            - subcategory: Transaction subcategory (optional)
    
    Returns:
        Number of transactions inserted (duplicates are skipped)
    """
    if not transactions:
        return 0

    inserted = 0
    skipped = 0
    
    cur = conn.execute("SELECT bank FROM statements WHERE id = ?", (statement_id,))
    row = cur.fetchone()
    account_id = row["bank"] if row else ""

    for seq, txn in enumerate(transactions):
        amount = _parse_amount(txn.get("amount", "0"))
        date = str(txn.get("date", "")).strip()
        description = str(txn.get("description", "")).strip()
        txn_type = str(txn.get("type", "")).strip()
        category = str(txn.get("category", "Uncategorized")).strip() or "Uncategorized"
        subcategory = str(txn.get("subcategory", "")).strip() or None
        raw_description = description
        
        amount_paise = int(round(amount * 100))
        date_iso = _parse_date_to_ymd(date) if date else ""

        if not date:
            continue

        # credit/debit are GENERATED ALWAYS columns - do not include in INSERT
        hash_input = f"{account_id}|{date_iso}|{description}|{amount_paise}"
        hash_signature = hashlib.sha256(hash_input.encode()).hexdigest().lower()

        cur = conn.execute(
            """INSERT OR IGNORE INTO transactions
                (statement_id, sequence_num, date, description, amount, type, category, subcategory, raw_description,
                 amount_paise, date_iso, hash_signature, account_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (statement_id, seq, date, description, amount, txn_type, category, subcategory, raw_description,
             amount_paise, date_iso, hash_signature, account_id),
        )
        if cur.rowcount > 0:
            inserted += 1
        else:
            skipped += 1

    log.info("Inserted %d transactions, skipped %d duplicates", inserted, skipped)
    return inserted


def get_all_transactions(
    conn: sqlite3.Connection,
    filters: Optional[Dict] = None
) -> List[Dict]:
    """Fetch transactions with optional filters.
    
    Args:
        conn: Database connection
        filters: Optional dict with filter keys:
            - date_from: Start date (inclusive)
            - date_to: End date (inclusive)
            - bank: Bank name filter
            - category: Category filter
            - min_amount: Minimum amount
            - max_amount: Maximum amount
            - type: 'debit' or 'credit'
    
    Returns:
        List of transaction dicts ordered by date DESC
    """
    filters = filters or {}
    conditions = []
    params = []

    if filters.get("date_from"):
        conditions.append("t.date >= ?")
        params.append(filters["date_from"])
    if filters.get("date_to"):
        conditions.append("t.date <= ?")
        params.append(filters["date_to"])
    if filters.get("bank"):
        conditions.append("s.bank = ?")
        params.append(filters["bank"])
    if filters.get("category"):
        conditions.append("t.category = ?")
        params.append(filters["category"])
    if filters.get("min_amount") is not None:
        conditions.append("t.amount >= ?")
        params.append(float(filters["min_amount"]))
    if filters.get("max_amount") is not None:
        conditions.append("t.amount <= ?")
        params.append(float(filters["max_amount"]))
    if filters.get("type"):
        conditions.append("t.type = ?")
        params.append(filters["type"])

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    sql = f"""SELECT t.id, t.statement_id, t.date, t.description, t.amount,
            t.type, t.category, t.subcategory, t.raw_description, t.created_at,
            s.bank, s.file_name, s.statement_period_from, s.statement_period_to
        FROM transactions t
        JOIN statements s ON t.statement_id = s.id
        {where}
        ORDER BY t.date DESC, t.id DESC"""

    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


def get_transaction_by_id(conn: sqlite3.Connection, transaction_id: int) -> Optional[Dict]:
    """Get a single transaction by ID.
    
    Args:
        conn: Database connection
        transaction_id: The transaction ID
    
    Returns:
        Transaction dict or None if not found
    """
    cur = conn.execute(
        """SELECT t.*, s.bank
        FROM transactions t
        JOIN statements s ON t.statement_id = s.id
        WHERE t.id = ?""",
        (transaction_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


def get_banks(conn: sqlite3.Connection) -> List[str]:
    """Get list of distinct bank names from statements.
    
    Args:
        conn: Database connection
    
    Returns:
        List of bank names ordered alphabetically
    """
    cur = conn.execute("SELECT DISTINCT bank FROM statements ORDER BY bank")
    return [row[0] for row in cur.fetchall()]


def get_transaction_count(conn: sqlite3.Connection) -> int:
    """Get total number of transactions.
    
    Args:
        conn: Database connection
    
    Returns:
        Total count of transactions
    """
    cur = conn.execute("SELECT COUNT(*) FROM transactions")
    return cur.fetchone()[0]


def get_transaction_summary_by_category(
    conn: sqlite3.Connection,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> List[Dict]:
    """Get transaction summary grouped by category.
    
    Args:
        conn: Database connection
        date_from: Optional start date filter
        date_to: Optional end date filter
    
    Returns:
        List of dicts with category, total_debit, total_credit, count
    """
    conditions = []
    params = []
    
    if date_from:
        conditions.append("date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date <= ?")
        params.append(date_to)
    
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    
    sql = f"""SELECT 
            category,
            COALESCE(SUM(debit), 0) as total_debit_paise,
            COALESCE(SUM(credit), 0) as total_credit_paise,
            COUNT(*) as transaction_count
        FROM transactions
        {where}
        GROUP BY category
        ORDER BY total_debit_paise DESC"""
    
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


def get_monthly_totals(
    conn: sqlite3.Connection,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> List[Dict]:
    """Get monthly debit/credit totals.
    
    Args:
        conn: Database connection
        date_from: Optional start date filter
        date_to: Optional end date filter
    
    Returns:
        List of dicts with month, total_debit, total_credit
    """
    conditions = []
    params = []
    
    if date_from:
        conditions.append("date_iso >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date_iso <= ?")
        params.append(date_to)
    
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    
    sql = f"""SELECT 
            substr(date_iso, 1, 7) as month,
            COALESCE(SUM(debit), 0) as total_debit_paise,
            COALESCE(SUM(credit), 0) as total_credit_paise,
            COUNT(*) as transaction_count
        FROM transactions
        {where}
        GROUP BY month
        ORDER BY month DESC"""
    
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]
