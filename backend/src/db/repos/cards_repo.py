"""Cards repository - CRUD operations for credit/debit cards.

This module provides database operations for card management,
including card CRUD and association with accounts.
"""

import sqlite3
from typing import List, Dict, Optional

from src.logger import log


def get_cards(
    conn: sqlite3.Connection,
    account_id: Optional[int] = None,
    include_inactive: bool = False
) -> List[Dict]:
    """Get all cards.
    
    Args:
        conn: Database connection
        account_id: Optional account ID to filter by
        include_inactive: If True, include inactive (soft-deleted) cards
    
    Returns:
        List of card dicts ordered by created_at DESC
    """
    conditions = []
    params = []
    
    if account_id is not None:
        conditions.append("account_id = ?")
        params.append(account_id)
    
    if not include_inactive:
        conditions.append("is_active = 1")
    
    sql = """
        SELECT id, account_id, card_name, card_type, issuer, last_four,
               cardholder_name, credit_limit_paise, billing_date,
               card_color, card_gradient, is_active, created_at, updated_at
        FROM cards
    """
    
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    
    sql += " ORDER BY created_at DESC"
    
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


def get_card(conn: sqlite3.Connection, card_id: int) -> Optional[Dict]:
    """Get a single card by ID.
    
    Args:
        conn: Database connection
        card_id: The card ID
    
    Returns:
        Card dict or None if not found
    """
    cur = conn.execute(
        """SELECT id, account_id, card_name, card_type, issuer, last_four,
               cardholder_name, credit_limit_paise, billing_date,
               card_color, card_gradient, is_active, created_at, updated_at
        FROM cards WHERE id = ?""",
        (card_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


def create_card(conn: sqlite3.Connection, card: Dict) -> int:
    """Create a new card.
    
    Args:
        conn: Database connection
        card: Dict with card data:
            - account_id: Associated account ID
            - card_name: Card name
            - card_type: Card type (visa, mastercard, rupay, amex, diners)
            - issuer: Card issuer/bank
            - last_four: Last 4 digits
            - cardholder_name: Name on card
            - credit_limit_paise: Credit limit in paise
            - billing_date: Billing date (day of month)
            - card_color: Display color
            - card_gradient: Display gradient
    
    Returns:
        The new card ID
    """
    cur = conn.execute(
        """INSERT INTO cards (account_id, card_name, card_type, issuer, last_four,
                          cardholder_name, credit_limit_paise, billing_date,
                          card_color, card_gradient)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            card.get("account_id"),
            card.get("card_name", ""),
            card.get("card_type", "visa"),
            card.get("issuer", ""),
            card.get("last_four", "XXXX"),
            card.get("cardholder_name", ""),
            card.get("credit_limit_paise", 0),
            card.get("billing_date", 1),
            card.get("card_color", "#1E293B"),
            card.get("card_gradient", "from-slate-800 to-slate-900"),
        )
    )
    card_id = cur.lastrowid
    log.info("Card created: %s (ID: %d)", card.get("card_name", ""), card_id)
    return card_id


def update_card(conn: sqlite3.Connection, card_id: int, card: Dict) -> bool:
    """Update an existing card.
    
    Args:
        conn: Database connection
        card_id: The card ID
        card: Dict with fields to update
    
    Returns:
        True if updated
    """
    allowed_fields = [
        "account_id", "card_name", "card_type", "issuer", "last_four",
        "cardholder_name", "credit_limit_paise", "billing_date",
        "card_color", "card_gradient"
    ]
    updates = []
    params = []
    
    for field in allowed_fields:
        if field in card:
            updates.append(f"{field} = ?")
            params.append(card[field])
    
    if not updates:
        return False
    
    params.append(card_id)
    sql = f"UPDATE cards SET {', '.join(updates)} WHERE id = ?"
    cur = conn.execute(sql, params)
    
    if cur.rowcount > 0:
        log.info("Card updated: %d", card_id)
    
    return cur.rowcount > 0


def delete_card(conn: sqlite3.Connection, card_id: int) -> bool:
    """Soft-delete a card (set is_active = 0).
    
    Args:
        conn: Database connection
        card_id: The card ID
    
    Returns:
        True if deleted
    """
    cur = conn.execute(
        "UPDATE cards SET is_active = 0 WHERE id = ? AND is_active = 1",
        (card_id,)
    )
    
    if cur.rowcount > 0:
        log.info("Card soft-deleted: %d", card_id)
    
    return cur.rowcount > 0


def get_cards_by_account(conn: sqlite3.Connection, account_id: int) -> List[Dict]:
    """Get all cards for a specific account.
    
    Args:
        conn: Database connection
        account_id: The account ID
    
    Returns:
        List of card dicts
    """
    return get_cards(conn, account_id=account_id)
