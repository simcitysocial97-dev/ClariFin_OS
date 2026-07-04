"""Account Repository

Data access layer for account entities.
"""

from typing import List
import sqlite3
from core.models import Account
from core.db.connection import DatabaseConnection

class AccountRepository:
    """Repository for account data access."""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def get_all_accounts(self) -> List[Account]:
        """Get all accounts from database."""
        with self.db.connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, bank_name, account_type,
                       balance_paise, credit_limit_paise, is_active
                FROM accounts
                ORDER BY name
            """)

            accounts = []
            for row in cursor.fetchall():
                accounts.append(Account(
                    id=row['id'],
                    name=row['name'],
                    bank_name=row['bank_name'],
                    account_type=row['account_type'],
                    balance_paise=row['balance_paise'],
                    credit_limit_paise=row['credit_limit_paise'],
                    is_active=bool(row['is_active'])
                ))

            return accounts

    def get_account_by_id(self, account_id: int) -> Account | None:
        """Get account by ID."""
        with self.db.connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, bank_name, account_type,
                       balance_paise, credit_limit_paise, is_active
                FROM accounts
                WHERE id = ?
            """, (account_id,))

            row = cursor.fetchone()
            if row:
                return Account(
                    id=row['id'],
                    name=row['name'],
                    bank_name=row['bank_name'],
                    account_type=row['account_type'],
                    balance_paise=row['balance_paise'],
                    credit_limit_paise=row['credit_limit_paise'],
                    is_active=bool(row['is_active'])
                )
            return None