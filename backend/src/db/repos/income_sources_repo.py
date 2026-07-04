"""Income sources repository - CRUD operations for income sources.

This module provides database operations for income source management,
including salary, freelance, rental, and other income types.
"""

import sqlite3
from typing import List, Dict, Optional

from src.logger import log


def get_income_sources(conn: sqlite3.Connection, active_only: bool = False) -> List[Dict]:
    """Get all income sources.
    
    Args:
        conn: Database connection
        active_only: If True, return only active income sources
    
    Returns:
        List of income source dicts ordered by created_at DESC
    """
    sql = """
        SELECT id, name, type, account_id, amount_paise, frequency,
               start_date, end_date, is_active, notes, created_at, updated_at
        FROM income_sources
    """
    if active_only:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY created_at DESC"
    
    cur = conn.execute(sql)
    return [dict(row) for row in cur.fetchall()]


def get_income_source(conn: sqlite3.Connection, source_id: int) -> Optional[Dict]:
    """Get a single income source by ID.
    
    Args:
        conn: Database connection
        source_id: The income source ID
    
    Returns:
        Income source dict or None if not found
    """
    cur = conn.execute(
        """SELECT id, name, type, account_id, amount_paise, frequency,
               start_date, end_date, is_active, notes, created_at, updated_at
        FROM income_sources WHERE id = ?""",
        (source_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


def insert_income_source(conn: sqlite3.Connection, source: Dict) -> int:
    """Create a new income source.
    
    Args:
        conn: Database connection
        source: Dict with income source data:
            - name: Income source name
            - type: Income type (salary, freelance, business, rental, etc.)
            - account_id: Associated account ID
            - amount_paise: Income amount in paise
            - frequency: Payment frequency (monthly, quarterly, annual, irregular)
            - start_date: Start date
            - end_date: End date (optional)
            - is_active: Active status
            - notes: Additional notes
    
    Returns:
        The new income source ID
    """
    cur = conn.execute(
        """INSERT INTO income_sources (name, type, account_id, amount_paise, frequency,
                                    start_date, end_date, is_active, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            source.get("name", ""),
            source.get("type", "other"),
            source.get("account_id"),
            source.get("amount_paise", 0),
            source.get("frequency", "monthly"),
            source.get("start_date"),
            source.get("end_date"),
            1 if source.get("is_active", True) else 0,
            source.get("notes", ""),
        )
    )
    source_id = cur.lastrowid
    log.info("Income source created: %s (ID: %d)", source.get("name", ""), source_id)
    return source_id


def update_income_source(conn: sqlite3.Connection, source_id: int, source: Dict) -> bool:
    """Update an existing income source.
    
    Args:
        conn: Database connection
        source_id: The income source ID
        source: Dict with fields to update
    
    Returns:
        True if updated
    """
    allowed_fields = [
        "name", "type", "account_id", "amount_paise", "frequency",
        "start_date", "end_date", "is_active", "notes"
    ]
    updates = []
    params = []
    
    for field in allowed_fields:
        if field in source:
            if field == "is_active":
                params.append(1 if source[field] else 0)
            else:
                params.append(source[field])
            updates.append(f"{field} = ?")
    
    if not updates:
        return False
    
    params.append(source_id)
    sql = f"UPDATE income_sources SET {', '.join(updates)} WHERE id = ?"
    cur = conn.execute(sql, params)
    
    if cur.rowcount > 0:
        log.info("Income source updated: %d", source_id)
    
    return cur.rowcount > 0


def delete_income_source(conn: sqlite3.Connection, source_id: int) -> bool:
    """Soft-delete an income source (set is_active = 0).
    
    Args:
        conn: Database connection
        source_id: The income source ID
    
    Returns:
        True if deleted
    """
    cur = conn.execute(
        "UPDATE income_sources SET is_active = 0 WHERE id = ? AND is_active = 1",
        (source_id,)
    )
    
    if cur.rowcount > 0:
        log.info("Income source soft-deleted: %d", source_id)
    
    return cur.rowcount > 0


def get_total_income_by_frequency(conn: sqlite3.Connection) -> Dict[str, int]:
    """Get total income grouped by frequency.
    
    Args:
        conn: Database connection
    
    Returns:
        Dict mapping frequency to total amount in paise
    """
    cur = conn.execute(
        """SELECT frequency, COALESCE(SUM(amount_paise), 0) as total_paise
        FROM income_sources
        WHERE is_active = 1
        GROUP BY frequency"""
    )
    return {row["frequency"]: row["total_paise"] for row in cur.fetchall()}
