"""Reconciliations repository - CRUD operations for transaction reconciliations.

This module provides database operations for reconciling transactions
between different accounts (e.g., transfers, payments).
"""

import sqlite3
from typing import List, Dict, Optional

from src.logger import log
from ..pagination import PaginatedResult, paginate_query


def get_reconciliations(
    conn: sqlite3.Connection,
    status: Optional[str] = None
) -> List[Dict]:
    """Get all reconciliations with optional status filter.
    
    Args:
        conn: Database connection
        status: Optional status filter ('pending', 'confirmed', 'rejected')
    
    Returns:
        List of reconciliation dicts ordered by created_at DESC
    """
    sql = """
        SELECT id, debit_txn_id, credit_txn_id, debit_account_id, credit_account_id,
               amount, date_diff_days, match_confidence, match_type, status,
               created_at, confirmed_at
        FROM reconciliations
    """
    params = []
    if status:
        sql += " WHERE status = ?"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


def get_reconciliations_paginated(
    conn: sqlite3.Connection,
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 50
) -> PaginatedResult:
    """Get reconciliations with pagination.
    
    Args:
        conn: Database connection
        status: Optional status filter
        page: Page number (1-indexed)
        per_page: Items per page
    
    Returns:
        PaginatedResult with reconciliations
    """
    where_clause = "WHERE status = ?" if status else ""
    params = [status] if status else []
    
    base_query = f"""
        SELECT id, debit_txn_id, credit_txn_id, debit_account_id, credit_account_id,
               amount, date_diff_days, match_confidence, match_type, status,
               created_at, confirmed_at
        FROM reconciliations
        {where_clause}
        ORDER BY created_at DESC
    """
    
    count_query = f"SELECT COUNT(*) FROM reconciliations {where_clause}"
    
    return paginate_query(
        conn,
        base_query.strip(),
        count_query.strip(),
        tuple(params),
        page,
        per_page,
    )


def get_pending_reconciliations(conn: sqlite3.Connection) -> List[Dict]:
    """Get all pending reconciliations.
    
    Args:
        conn: Database connection
    
    Returns:
        List of pending reconciliation dicts
    """
    return get_reconciliations(conn, status="pending")


def get_reconciliation(conn: sqlite3.Connection, reconciliation_id: int) -> Optional[Dict]:
    """Get a single reconciliation by ID.
    
    Args:
        conn: Database connection
        reconciliation_id: The reconciliation ID
    
    Returns:
        Reconciliation dict or None if not found
    """
    cur = conn.execute(
        """SELECT id, debit_txn_id, credit_txn_id, debit_account_id, credit_account_id,
               amount, date_diff_days, match_confidence, match_type, status,
               created_at, confirmed_at
        FROM reconciliations WHERE id = ?""",
        (reconciliation_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


def insert_reconciliation(
    conn: sqlite3.Connection,
    debit_txn_id: int,
    credit_txn_id: int,
    debit_account_id: str,
    credit_account_id: str,
    amount: float,
    date_diff_days: int = 0,
    match_confidence: float = 0.5,
    match_type: str = "auto"
) -> int:
    """Create a new reconciliation.
    
    Args:
        conn: Database connection
        debit_txn_id: Debit transaction ID
        credit_txn_id: Credit transaction ID
        debit_account_id: Debit account identifier
        credit_account_id: Credit account identifier
        amount: Reconciliation amount
        date_diff_days: Difference in days between transactions
        match_confidence: Match confidence score (0-1)
        match_type: Match type ('exact', 'window', 'fuzzy', 'manual')
    
    Returns:
        The new reconciliation ID
    """
    # Generate deterministic key for duplicate prevention
    deterministic_key = f"{debit_txn_id}:{credit_txn_id}"
    
    cur = conn.execute(
        """INSERT INTO reconciliations 
            (debit_txn_id, credit_txn_id, debit_account_id, credit_account_id,
             amount, date_diff_days, match_confidence, match_type, status, deterministic_key)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        ON CONFLICT(deterministic_key) DO UPDATE SET
            match_confidence = excluded.match_confidence,
            match_type = excluded.match_type
        """,
        (
            debit_txn_id,
            credit_txn_id,
            debit_account_id,
            credit_account_id,
            amount,
            date_diff_days,
            match_confidence,
            match_type,
            deterministic_key,
        )
    )
    reconciliation_id = cur.lastrowid
    log.info("Reconciliation created: %d (debit_txn=%d, credit_txn=%d)",
             reconciliation_id, debit_txn_id, credit_txn_id)
    return reconciliation_id


def confirm_reconciliation(conn: sqlite3.Connection, reconciliation_id: int) -> bool:
    """Confirm a reconciliation.
    
    Args:
        conn: Database connection
        reconciliation_id: The reconciliation ID
    
    Returns:
        True if confirmed
    """
    cur = conn.execute(
        """UPDATE reconciliations 
        SET status = 'confirmed', confirmed_at = datetime('now')
        WHERE id = ? AND status = 'pending'""",
        (reconciliation_id,)
    )
    
    if cur.rowcount > 0:
        log.info("Reconciliation confirmed: %d", reconciliation_id)
    
    return cur.rowcount > 0


def reject_reconciliation(conn: sqlite3.Connection, reconciliation_id: int) -> bool:
    """Reject a reconciliation.
    
    Args:
        conn: Database connection
        reconciliation_id: The reconciliation ID
    
    Returns:
        True if rejected
    """
    cur = conn.execute(
        "UPDATE reconciliations SET status = 'rejected' WHERE id = ? AND status = 'pending'",
        (reconciliation_id,)
    )
    
    if cur.rowcount > 0:
        log.info("Reconciliation rejected: %d", reconciliation_id)
    
    return cur.rowcount > 0


def delete_reconciliation(conn: sqlite3.Connection, reconciliation_id: int) -> bool:
    """Delete a reconciliation.
    
    Args:
        conn: Database connection
        reconciliation_id: The reconciliation ID
    
    Returns:
        True if deleted
    """
    cur = conn.execute(
        "DELETE FROM reconciliations WHERE id = ?",
        (reconciliation_id,)
    )
    
    if cur.rowcount > 0:
        log.info("Reconciliation deleted: %d", reconciliation_id)
    
    return cur.rowcount > 0


def get_reconciliation_by_transactions(
    conn: sqlite3.Connection,
    debit_txn_id: int,
    credit_txn_id: int
) -> Optional[Dict]:
    """Get reconciliation by transaction pair.
    
    Args:
        conn: Database connection
        debit_txn_id: Debit transaction ID
        credit_txn_id: Credit transaction ID
    
    Returns:
        Reconciliation dict or None if not found
    """
    cur = conn.execute(
        """SELECT * FROM reconciliations
        WHERE debit_txn_id = ? AND credit_txn_id = ?""",
        (debit_txn_id, credit_txn_id)
    )
    row = cur.fetchone()
    return dict(row) if row else None
