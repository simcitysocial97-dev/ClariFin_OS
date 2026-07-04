"""Statements repository - CRUD operations for bank statements.

This module provides database operations for statement management,
including statement records and duplicate checking.
"""

import sqlite3
from typing import Optional

from src.logger import log


def insert_statement(
    conn: sqlite3.Connection,
    bank: str,
    file_name: str,
    period_from: str = "",
    period_to: str = "",
    card_last4: str = ""
) -> int:
    """Insert a statement record. Returns statement_id.
    
    If a statement with the same (bank, file_name) already exists,
    returns the existing statement_id.
    
    Args:
        conn: Database connection
        bank: Bank name
        file_name: Original filename
        period_from: Statement period start date (optional)
        period_to: Statement period end date (optional)
        card_last4: Last 4 digits of card (optional)
    
    Returns:
        The statement ID (existing or newly created)
    """
    # Check for existing statement
    cur = conn.execute(
        "SELECT id FROM statements WHERE bank = ? AND file_name = ?",
        (bank, file_name),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    # Insert new statement
    cur = conn.execute(
        """INSERT INTO statements (bank, card_last4, statement_period_from, statement_period_to, file_name)
        VALUES (?, ?, ?, ?, ?)""",
        (bank, card_last4 or None, period_from or None, period_to or None, file_name),
    )
    statement_id = cur.lastrowid
    log.info("Statement recorded: %s - %s", bank, file_name)
    return statement_id


def get_duplicate_check(conn: sqlite3.Connection, bank: str, file_name: str) -> bool:
    """Check if a statement already exists.
    
    Args:
        conn: Database connection
        bank: Bank name
        file_name: Original filename
    
    Returns:
        True if (bank, file_name) already exists in statements
    """
    cur = conn.execute(
        "SELECT 1 FROM statements WHERE bank = ? AND file_name = ?",
        (bank, file_name),
    )
    return cur.fetchone() is not None


def get_statement_by_id(conn: sqlite3.Connection, statement_id: int) -> Optional[dict]:
    """Get a single statement by ID.
    
    Args:
        conn: Database connection
        statement_id: The statement ID
    
    Returns:
        Statement dict or None if not found
    """
    cur = conn.execute(
        "SELECT * FROM statements WHERE id = ?",
        (statement_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


def get_statement_count(conn: sqlite3.Connection) -> int:
    """Get total number of imported statements.
    
    Args:
        conn: Database connection
    
    Returns:
        Total count of statements
    """
    cur = conn.execute("SELECT COUNT(*) FROM statements")
    return cur.fetchone()[0]
