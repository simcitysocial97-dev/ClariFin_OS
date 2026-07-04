"""Recurring Transaction Repository

Data access layer for recurring transaction entities.
"""

from typing import List
import sqlite3
from core.models import RecurringTransaction
from core.db.connection import DatabaseConnection

class RecurringTransactionRepository:
    """Repository for recurring transaction data access."""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def get_all_recurring_transactions(self) -> List[RecurringTransaction]:
        """Get all recurring transactions from database."""
        with self.db.connection() as conn:
            cursor = conn.execute("""
                SELECT description, category, amount_paise, frequency,
                       account_id, is_active
                FROM recurring_transactions
                ORDER BY description
            """)

            recurring = []
            for row in cursor.fetchall():
                recurring.append(RecurringTransaction(
                    description=row['description'],
                    category=row['category'],
                    amount_paise=row['amount_paise'],
                    frequency=row['frequency'],
                    account_id=row['account_id'],
                    is_active=bool(row['is_active'])
                ))

            return recurring