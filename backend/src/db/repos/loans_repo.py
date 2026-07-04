"""Loans repository - CRUD operations for loans and loan payments.

This module provides database operations for loan management,
including loans, loan payments, and related queries.
"""

import sqlite3
from typing import List, Dict, Optional
from collections import defaultdict

from src.logger import log


# ============================================================
# Loans CRUD
# ============================================================

def get_loans(conn: sqlite3.Connection, status: str | None = None) -> list[dict]:
    """Get all loans. Optionally filter by status.
    
    Args:
        conn: Database connection
        status: Optional status filter ('active', 'closed', 'defaulted')
    
    Returns:
        List of loan dicts ordered by created_at DESC
    """
    sql = "SELECT * FROM loans"
    params = []
    if status:
        sql += " WHERE status = ?"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


def get_loan(conn: sqlite3.Connection, loan_id: int) -> dict | None:
    """Get a single loan by ID.
    
    Args:
        conn: Database connection
        loan_id: The loan ID
    
    Returns:
        Loan dict or None if not found
    """
    cur = conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def insert_loan(conn: sqlite3.Connection, data: dict) -> int:
    """Insert a new loan. Returns the new loan ID.
    
    Args:
        conn: Database connection
        data: Dict with loan data
    
    Returns:
        The new loan ID
    """
    cur = conn.execute("""
        INSERT INTO loans (name, lender, loan_type, principal_paise, outstanding_paise, 
                          interest_rate, emi_paise, tenure_months, start_date, end_date, 
                          linked_account_id, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("name", ""),
        data.get("lender"),
        data.get("loan_type", "other"),
        data.get("principal_paise", 0),
        data.get("outstanding_paise", 0),
        data.get("interest_rate", 0.0),
        data.get("emi_paise", 0),
        data.get("tenure_months"),
        data.get("start_date"),
        data.get("end_date"),
        data.get("linked_account_id"),
        data.get("status", "active"),
        data.get("notes"),
    ))
    return cur.lastrowid


def update_loan(conn: sqlite3.Connection, loan_id: int, data: dict) -> bool:
    """Update an existing loan. Returns True if updated.
    
    Args:
        conn: Database connection
        loan_id: The loan ID
        data: Dict with fields to update
    
    Returns:
        True if updated
    """
    allowed_fields = ["name", "lender", "loan_type", "principal_paise", 
                     "outstanding_paise", "interest_rate", "emi_paise", 
                     "tenure_months", "start_date", "end_date", 
                     "linked_account_id", "status", "notes"]
    updates = []
    params = []
    for field in allowed_fields:
        if field in data:
            updates.append(f"{field} = ?")
            params.append(data[field])
    
    if not updates:
        return False
    
    # Always update updated_at via trigger
    params.append(loan_id)
    sql = f"UPDATE loans SET {', '.join(updates)} WHERE id = ?"
    cur = conn.execute(sql, params)
    return cur.rowcount > 0


def delete_loan(conn: sqlite3.Connection, loan_id: int) -> bool:
    """Delete a loan. Returns True if deleted.
    
    Args:
        conn: Database connection
        loan_id: The loan ID
    
    Returns:
        True if deleted
    """
    cur = conn.execute("DELETE FROM loans WHERE id = ?", (loan_id,))
    return cur.rowcount > 0


def delete_loan_with_payments(conn: sqlite3.Connection, loan_id: int) -> bool:
    """Delete a loan and all its payments atomically.
    
    Args:
        conn: Database connection
        loan_id: The loan ID
    
    Returns:
        True if deleted
    """
    conn.execute("DELETE FROM loan_payments WHERE loan_id = ?", (loan_id,))
    result = conn.execute("DELETE FROM loans WHERE id = ?", (loan_id,))
    deleted = result.rowcount > 0
    if deleted:
        log.info("Loan %d deleted with all payments", loan_id)
    return deleted


# ============================================================
# Loan Payments CRUD
# ============================================================

def get_loan_payments(conn: sqlite3.Connection, loan_id: int) -> list[dict]:
    """Get all payments for a specific loan.
    
    Args:
        conn: Database connection
        loan_id: The loan ID
    
    Returns:
        List of payment dicts ordered by payment_date DESC
    """
    cur = conn.execute(
        "SELECT * FROM loan_payments WHERE loan_id = ? ORDER BY payment_date DESC",
        (loan_id,)
    )
    return [dict(row) for row in cur.fetchall()]


def insert_loan_payment(conn: sqlite3.Connection, data: dict) -> int:
    """Insert a new loan payment. Returns the new payment ID.
    
    Args:
        conn: Database connection
        data: Dict with payment data
    
    Returns:
        The new payment ID
    """
    cur = conn.execute("""
        INSERT INTO loan_payments (loan_id, transaction_id, principal_component_paise, 
                                  interest_component_paise, payment_date, remaining_principal_paise)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data.get("loan_id"),
        data.get("transaction_id"),
        data.get("principal_component_paise", 0),
        data.get("interest_component_paise", 0),
        data.get("payment_date"),
        data.get("remaining_principal_paise", 0),
    ))
    return cur.lastrowid


# ============================================================
# Batch Queries
# ============================================================

def get_all_loan_payments_grouped(conn: sqlite3.Connection) -> dict[int, list[dict]]:
    """Fetch all payments for active loans, grouped by loan_id.
    
    Optimized: Replaces N queries (one per loan) with 1 query.
    Used by projection_engine._prepare_loan_states()
    
    Args:
        conn: Database connection
    
    Returns:
        Dict mapping loan_id to list of payment dicts
    """
    cur = conn.execute("""
        SELECT lp.* FROM loan_payments lp
        JOIN loans l ON lp.loan_id = l.id
        WHERE l.status = 'active'
        ORDER BY lp.loan_id, lp.payment_date ASC
    """)
    
    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in cur.fetchall():
        grouped[row["loan_id"]].append(dict(row))
    
    return dict(grouped)
