"""
Layout Templates Repository
===========================
Database operations for layout template persistence.

Provides CRUD operations for layout_templates table with fingerprint-based lookup.

Example:
    from src.db.layout_templates_repo import (
        get_template_by_fingerprint,
        upsert_template,
        mark_template_used,
    )
    
    # Look up existing template
    template = get_template_by_fingerprint(conn, fingerprint)
    
    # Create or update template
    template_id = upsert_template(conn, fingerprint, bank, width, height, bbox)
    
    # Update last_used timestamp
    mark_template_used(conn, template_id)
"""

import json
import uuid
from typing import Optional
import sqlite3

from src.logger import log


# Schema definition for reference
DDL_LAYOUT_TEMPLATES = """
CREATE TABLE IF NOT EXISTS layout_templates (
    id TEXT PRIMARY KEY,
    bank TEXT NOT NULL,
    fingerprint TEXT UNIQUE NOT NULL,
    page_width REAL,
    page_height REAL,
    bbox_norm_json TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    last_used_at TEXT,
    notes TEXT
);
"""

DDL_LAYOUT_TEMPLATES_INDEX = """
CREATE INDEX IF NOT EXISTS idx_layout_templates_fingerprint 
ON layout_templates(fingerprint);
"""


def init_layout_templates_table(conn: sqlite3.Connection) -> None:
    """Create layout_templates table and indexes if they don't exist."""
    conn.execute(DDL_LAYOUT_TEMPLATES)
    conn.execute(DDL_LAYOUT_TEMPLATES_INDEX)
    log.debug("Layout templates table initialized")


def get_template_by_fingerprint(
    conn: sqlite3.Connection,
    fingerprint: str
) -> Optional[dict]:
    """
    Get a layout template by its fingerprint.
    
    Args:
        conn: SQLite connection
        fingerprint: SHA256 fingerprint string
    
    Returns:
        Template dict with keys: id, bank, fingerprint, page_width, page_height,
        bbox_norm_json, created_at, last_used_at, notes
        Returns None if not found.
    """
    cur = conn.execute(
        """
        SELECT id, bank, fingerprint, page_width, page_height, 
               bbox_norm_json, created_at, last_used_at, notes
        FROM layout_templates
        WHERE fingerprint = ?
        """,
        (fingerprint,)
    )
    row = cur.fetchone()
    
    if row is None:
        return None
    
    template = dict(row)
    
    # Parse bbox_norm_json if present
    if template.get("bbox_norm_json"):
        try:
            template["bbox_norm"] = json.loads(template["bbox_norm_json"])
        except json.JSONDecodeError:
            template["bbox_norm"] = None
    else:
        template["bbox_norm"] = None
    
    return template


def upsert_template(
    conn: sqlite3.Connection,
    fingerprint: str,
    bank: str,
    page_width: float,
    page_height: float,
    bbox_norm: Optional[list[float]] = None,
    notes: Optional[str] = None
) -> str:
    """
    Insert or update a layout template.
    
    If a template with the same fingerprint exists, updates the bank and dimensions.
    Otherwise, creates a new template with a new UUID.
    
    Args:
        conn: SQLite connection
        fingerprint: SHA256 fingerprint string
        bank: Bank name (e.g., "HDFC Bank")
        page_width: Page width in PDF points
        page_height: Page height in PDF points
        bbox_norm: Optional normalized bbox [x0, y0, x1, y1] in top-left origin
        notes: Optional notes about this template
    
    Returns:
        Template ID (UUID string)
    """
    # Check if template exists
    existing = get_template_by_fingerprint(conn, fingerprint)
    
    if existing:
        template_id = existing["id"]
        
        # Update existing template
        conn.execute(
            """
            UPDATE layout_templates
            SET bank = ?, page_width = ?, page_height = ?, 
                bbox_norm_json = ?, notes = COALESCE(?, notes),
                last_used_at = datetime('now')
            WHERE id = ?
            """,
            (
                bank,
                page_width,
                page_height,
                json.dumps(bbox_norm) if bbox_norm else None,
                notes,
                template_id,
            )
        )
        log.debug("Updated layout template: %s (fingerprint: %s...)", 
                  template_id, fingerprint[:16])
    else:
        # Create new template
        template_id = str(uuid.uuid4())
        
        conn.execute(
            """
            INSERT INTO layout_templates 
            (id, bank, fingerprint, page_width, page_height, bbox_norm_json, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                template_id,
                bank,
                fingerprint,
                page_width,
                page_height,
                json.dumps(bbox_norm) if bbox_norm else None,
                notes,
            )
        )
        log.info("Created layout template: %s (fingerprint: %s...)", 
                 template_id, fingerprint[:16])
    
    return template_id


def mark_template_used(
    conn: sqlite3.Connection,
    template_id: str
) -> bool:
    """
    Update the last_used_at timestamp for a template.
    
    Args:
        conn: SQLite connection
        template_id: Template UUID
    
    Returns:
        True if template was found and updated, False otherwise
    """
    cur = conn.execute(
        """
        UPDATE layout_templates
        SET last_used_at = datetime('now')
        WHERE id = ?
        """,
        (template_id,)
    )
    
    if cur.rowcount > 0:
        log.debug("Marked template %s as used", template_id)
        return True
    else:
        log.warning("Template %s not found for mark_used", template_id)
        return False


def get_template_by_id(
    conn: sqlite3.Connection,
    template_id: str
) -> Optional[dict]:
    """
    Get a layout template by its ID.
    
    Args:
        conn: SQLite connection
        template_id: Template UUID
    
    Returns:
        Template dict or None if not found
    """
    cur = conn.execute(
        """
        SELECT id, bank, fingerprint, page_width, page_height, 
               bbox_norm_json, created_at, last_used_at, notes
        FROM layout_templates
        WHERE id = ?
        """,
        (template_id,)
    )
    row = cur.fetchone()
    
    if row is None:
        return None
    
    template = dict(row)
    
    # Parse bbox_norm_json if present
    if template.get("bbox_norm_json"):
        try:
            template["bbox_norm"] = json.loads(template["bbox_norm_json"])
        except json.JSONDecodeError:
            template["bbox_norm"] = None
    else:
        template["bbox_norm"] = None
    
    return template


def list_templates(
    conn: sqlite3.Connection,
    bank: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> list[dict]:
    """
    List layout templates with optional bank filter.
    
    Args:
        conn: SQLite connection
        bank: Optional bank name filter
        limit: Maximum results to return
        offset: Offset for pagination
    
    Returns:
        List of template dicts
    """
    if bank:
        cur = conn.execute(
            """
            SELECT id, bank, fingerprint, page_width, page_height, 
                   bbox_norm_json, created_at, last_used_at, notes
            FROM layout_templates
            WHERE bank = ?
            ORDER BY last_used_at DESC NULLS LAST, created_at DESC
            LIMIT ? OFFSET ?
            """,
            (bank, limit, offset)
        )
    else:
        cur = conn.execute(
            """
            SELECT id, bank, fingerprint, page_width, page_height, 
                   bbox_norm_json, created_at, last_used_at, notes
            FROM layout_templates
            ORDER BY last_used_at DESC NULLS LAST, created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )
    
    rows = cur.fetchall()
    templates = []
    
    for row in rows:
        template = dict(row)
        
        # Parse bbox_norm_json if present
        if template.get("bbox_norm_json"):
            try:
                template["bbox_norm"] = json.loads(template["bbox_norm_json"])
            except json.JSONDecodeError:
                template["bbox_norm"] = None
        else:
            template["bbox_norm"] = None
        
        templates.append(template)
    
    return templates


def delete_template(conn: sqlite3.Connection, template_id: str) -> bool:
    """
    Delete a layout template by ID.
    
    Args:
        conn: SQLite connection
        template_id: Template UUID
    
    Returns:
        True if deleted, False if not found
    """
    cur = conn.execute(
        "DELETE FROM layout_templates WHERE id = ?",
        (template_id,)
    )
    
    if cur.rowcount > 0:
        log.info("Deleted layout template: %s", template_id)
        return True
    else:
        return False


# Export public API
__all__ = [
    "DDL_LAYOUT_TEMPLATES",
    "DDL_LAYOUT_TEMPLATES_INDEX",
    "init_layout_templates_table",
    "get_template_by_fingerprint",
    "get_template_by_id",
    "upsert_template",
    "mark_template_used",
    "list_templates",
    "delete_template",
]