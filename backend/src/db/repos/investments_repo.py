"""Investments repository - CRUD operations for investments.

This module provides database operations for investment management,
including mutual funds, stocks, FDs, PPF, and other investment types.
"""

import sqlite3
from typing import List, Dict, Optional

from src.logger import log


def get_investments(conn: sqlite3.Connection, active_only: bool = True) -> List[Dict]:
    """Get all investments.
    
    Args:
        conn: Database connection
        active_only: If True, return only active investments
    
    Returns:
        List of investment dicts ordered by created_at DESC
    """
    sql = """
        SELECT id, name, type, platform, invested_paise, current_value_paise,
               units, purchase_date, maturity_date, linked_account_id,
               is_active, notes, last_updated, created_at
        FROM investments
    """
    if active_only:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY created_at DESC"
    
    cur = conn.execute(sql)
    return [dict(row) for row in cur.fetchall()]


def get_investment(conn: sqlite3.Connection, investment_id: int) -> Optional[Dict]:
    """Get a single investment by ID.
    
    Args:
        conn: Database connection
        investment_id: The investment ID
    
    Returns:
        Investment dict or None if not found
    """
    cur = conn.execute(
        """SELECT id, name, type, platform, invested_paise, current_value_paise,
               units, purchase_date, maturity_date, linked_account_id,
               is_active, notes, last_updated, created_at
        FROM investments WHERE id = ?""",
        (investment_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


def insert_investment(conn: sqlite3.Connection, investment: Dict) -> int:
    """Create a new investment.
    
    Args:
        conn: Database connection
        investment: Dict with investment data:
            - name: Investment name
            - type: Investment type (mutual_fund, stock, fd, ppf, etc.)
            - platform: Platform/broker
            - invested_paise: Amount invested in paise
            - current_value_paise: Current value in paise
            - units: Number of units
            - purchase_date: Purchase date
            - maturity_date: Maturity date (for FDs)
            - linked_account_id: Associated account ID
            - is_active: Active status
            - notes: Additional notes
    
    Returns:
        The new investment ID
    """
    cur = conn.execute(
        """INSERT INTO investments (name, type, platform, invested_paise, current_value_paise,
                                units, purchase_date, maturity_date, linked_account_id,
                                is_active, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            investment.get("name", ""),
            investment.get("type", "other"),
            investment.get("platform", ""),
            investment.get("invested_paise", 0),
            investment.get("current_value_paise", 0),
            investment.get("units", 0),
            investment.get("purchase_date"),
            investment.get("maturity_date"),
            investment.get("linked_account_id"),
            1 if investment.get("is_active", True) else 0,
            investment.get("notes", ""),
        )
    )
    investment_id = cur.lastrowid
    log.info("Investment created: %s (ID: %d)", investment.get("name", ""), investment_id)
    return investment_id


def update_investment(conn: sqlite3.Connection, investment_id: int, investment: Dict) -> bool:
    """Update an existing investment.
    
    Args:
        conn: Database connection
        investment_id: The investment ID
        investment: Dict with fields to update
    
    Returns:
        True if updated
    """
    allowed_fields = [
        "name", "type", "platform", "invested_paise", "current_value_paise",
        "units", "purchase_date", "maturity_date", "linked_account_id",
        "is_active", "notes"
    ]
    updates = []
    params = []
    
    for field in allowed_fields:
        if field in investment:
            if field == "is_active":
                params.append(1 if investment[field] else 0)
            else:
                params.append(investment[field])
            updates.append(f"{field} = ?")
    
    if not updates:
        return False
    
    # Update last_updated timestamp
    updates.append("last_updated = datetime('now')")
    
    params.append(investment_id)
    sql = f"UPDATE investments SET {', '.join(updates)} WHERE id = ?"
    cur = conn.execute(sql, params)
    
    if cur.rowcount > 0:
        log.info("Investment updated: %d", investment_id)
    
    return cur.rowcount > 0


def delete_investment(conn: sqlite3.Connection, investment_id: int) -> bool:
    """Soft-delete an investment (set is_active = 0).
    
    Args:
        conn: Database connection
        investment_id: The investment ID
    
    Returns:
        True if deleted
    """
    cur = conn.execute(
        "UPDATE investments SET is_active = 0 WHERE id = ? AND is_active = 1",
        (investment_id,)
    )
    
    if cur.rowcount > 0:
        log.info("Investment soft-deleted: %d", investment_id)
    
    return cur.rowcount > 0


def get_total_invested_value(conn: sqlite3.Connection) -> Dict:
    """Get total invested and current values across all active investments.
    
    Args:
        conn: Database connection
    
    Returns:
        Dict with total_invested_paise and total_current_paise
    """
    cur = conn.execute(
        """SELECT 
            COALESCE(SUM(invested_paise), 0) as total_invested_paise,
            COALESCE(SUM(current_value_paise), 0) as total_current_paise
        FROM investments
        WHERE is_active = 1"""
    )
    row = cur.fetchone()
    return dict(row) if row else {"total_invested_paise": 0, "total_current_paise": 0}
