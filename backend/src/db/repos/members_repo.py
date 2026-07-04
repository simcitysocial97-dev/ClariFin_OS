"""Members repository - CRUD operations for family members.

This module provides database operations for member management,
including adding, updating, and listing family members.
"""

import sqlite3
from typing import List, Dict, Optional

from src.logger import log


def get_members(conn: sqlite3.Connection) -> List[Dict]:
    """Get all family members.
    
    Args:
        conn: Database connection
    
    Returns:
        List of member dicts ordered by name
    """
    cur = conn.execute(
        """SELECT id, name, color, created_at
        FROM members
        ORDER BY name"""
    )
    return [dict(row) for row in cur.fetchall()]


def get_member(conn: sqlite3.Connection, member_id: int) -> Optional[Dict]:
    """Get a single member by ID.
    
    Args:
        conn: Database connection
        member_id: The member ID
    
    Returns:
        Member dict or None if not found
    """
    cur = conn.execute(
        """SELECT id, name, color, created_at
        FROM members WHERE id = ?""",
        (member_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


def get_member_by_name(conn: sqlite3.Connection, name: str) -> Optional[Dict]:
    """Get a member by name (case-insensitive).
    
    Args:
        conn: Database connection
        name: The member name
    
    Returns:
        Member dict or None if not found
    """
    cur = conn.execute(
        """SELECT id, name, color, created_at
        FROM members WHERE LOWER(name) = LOWER(?)""",
        (name,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


def add_member(conn: sqlite3.Connection, name: str, color: str = "#6366F1") -> int:
    """Add a new family member.
    
    Args:
        conn: Database connection
        name: Member name
        color: Display color (default: indigo)
    
    Returns:
        The new member ID
    """
    cur = conn.execute(
        "INSERT INTO members (name, color) VALUES (?, ?)",
        (name, color)
    )
    member_id = cur.lastrowid
    log.info("Member created: %s (ID: %d)", name, member_id)
    return member_id


def update_member(conn: sqlite3.Connection, member_id: int, name: Optional[str] = None, color: Optional[str] = None) -> bool:
    """Update an existing member.
    
    Args:
        conn: Database connection
        member_id: The member ID
        name: New name (optional)
        color: New color (optional)
    
    Returns:
        True if updated
    """
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if color is not None:
        updates.append("color = ?")
        params.append(color)
    
    if not updates:
        return False
    
    params.append(member_id)
    sql = f"UPDATE members SET {', '.join(updates)} WHERE id = ?"
    cur = conn.execute(sql, params)
    
    if cur.rowcount > 0:
        log.info("Member updated: %d", member_id)
    
    return cur.rowcount > 0


def delete_member(conn: sqlite3.Connection, member_id: int) -> bool:
    """Delete a member.
    
    Note: This will fail if the member is referenced by transactions.
    
    Args:
        conn: Database connection
        member_id: The member ID
    
    Returns:
        True if deleted
    """
    cur = conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
    
    if cur.rowcount > 0:
        log.info("Member deleted: %d", member_id)
    
    return cur.rowcount > 0


def ensure_default_member(conn: sqlite3.Connection) -> int:
    """Ensure the default 'Self' member exists.
    
    Args:
        conn: Database connection
    
    Returns:
        The default member ID
    """
    member = get_member_by_name(conn, "Self")
    if member:
        return member["id"]
    
    return add_member(conn, "Self", "#6366F1")
