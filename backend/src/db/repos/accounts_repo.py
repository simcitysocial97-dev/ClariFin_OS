"""Accounts repository - CRUD operations for bank accounts.

This module provides database operations for account management,
including savings, current, credit card, and other account types.
"""

import sqlite3
from typing import List, Dict, Optional

from src.logger import log


def get_accounts(conn: sqlite3.Connection, include_inactive: bool = False) -> List[Dict]:
    """Get all accounts.
    
    Args:
        conn: Database connection
        include_inactive: If True, include inactive (soft-deleted) accounts
    
    Returns:
        List of account dicts ordered by created_at DESC
    """
    sql = """
        SELECT id, name, bank_name, account_type, account_number_masked,
               balance_paise, credit_limit_paise, currency, color, icon,
               is_active, created_at, updated_at
        FROM accounts
    """
    if not include_inactive:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY created_at DESC"
    
    cur = conn.execute(sql)
    return [dict(row) for row in cur.fetchall()]


def get_account(conn: sqlite3.Connection, account_id: int) -> Optional[Dict]:
    """Get a single account by ID.
    
    Args:
        conn: Database connection
        account_id: The account ID
    
    Returns:
        Account dict or None if not found
    """
    cur = conn.execute(
        """SELECT id, name, bank_name, account_type, account_number_masked,
               balance_paise, credit_limit_paise, currency, color, icon,
               is_active, created_at, updated_at
        FROM accounts WHERE id = ?""",
        (account_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


def create_account(conn: sqlite3.Connection, account: Dict) -> int:
    """Create a new account.
    
    Args:
        conn: Database connection
        account: Dict with account data:
            - name: Account name
            - bank_name: Bank name
            - account_type: Type (savings, current, credit_card, fd, wallet, loan)
            - account_number_masked: Masked account number
            - balance_paise: Balance in paise
            - credit_limit_paise: Credit limit in paise (for credit cards)
            - currency: Currency code (default: INR)
            - color: Display color
            - icon: Display icon
    
    Returns:
        The new account ID
    """
    cur = conn.execute(
        """INSERT INTO accounts (name, bank_name, account_type, account_number_masked,
                             balance_paise, credit_limit_paise, currency, color, icon)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            account.get("name", ""),
            account.get("bank_name", ""),
            account.get("account_type", "savings"),
            account.get("account_number_masked", "XXXX"),
            account.get("balance_paise", 0),
            account.get("credit_limit_paise", 0),
            account.get("currency", "INR"),
            account.get("color", "#6366F1"),
            account.get("icon", "building"),
        )
    )
    account_id = cur.lastrowid
    log.info("Account created: %s (ID: %d)", account.get("name", ""), account_id)
    return account_id


def update_account(conn: sqlite3.Connection, account_id: int, account: Dict) -> bool:
    """Update an existing account.
    
    Args:
        conn: Database connection
        account_id: The account ID
        account: Dict with fields to update
    
    Returns:
        True if updated
    """
    allowed_fields = [
        "name", "bank_name", "account_type", "account_number_masked",
        "balance_paise", "credit_limit_paise", "currency", "color", "icon"
    ]
    updates = []
    params = []
    
    for field in allowed_fields:
        if field in account:
            updates.append(f"{field} = ?")
            params.append(account[field])
    
    if not updates:
        return False
    
    params.append(account_id)
    sql = f"UPDATE accounts SET {', '.join(updates)} WHERE id = ?"
    cur = conn.execute(sql, params)
    
    if cur.rowcount > 0:
        log.info("Account updated: %d", account_id)
    
    return cur.rowcount > 0


def delete_account(conn: sqlite3.Connection, account_id: int) -> bool:
    """Soft-delete an account (set is_active = 0).
    
    Args:
        conn: Database connection
        account_id: The account ID
    
    Returns:
        True if deleted
    """
    cur = conn.execute(
        "UPDATE accounts SET is_active = 0 WHERE id = ? AND is_active = 1",
        (account_id,)
    )
    
    if cur.rowcount > 0:
        log.info("Account soft-deleted: %d", account_id)
    
    return cur.rowcount > 0


def delete_account_with_cards(conn: sqlite3.Connection, account_id: int) -> bool:
    """Delete an account and all associated cards atomically.
    
    Args:
        conn: Database connection
        account_id: The account ID
    
    Returns:
        True if deleted
    """
    conn.execute("DELETE FROM cards WHERE account_id = ?", (account_id,))
    result = conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    deleted = result.rowcount > 0
    
    if deleted:
        log.info("Account %d deleted with all cards", account_id)
    
    return deleted
