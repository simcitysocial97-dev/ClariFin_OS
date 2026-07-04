"""Transaction Repository

Data access layer for transaction entities.
"""

from typing import List
import sqlite3
from core.models import Transaction
from core.db.connection import DatabaseConnection

class TransactionRepository:
    """Repository for transaction data access."""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def get_all_transactions(self) -> List[Transaction]:
        """Get all transactions from database."""
        with self.db.connection() as conn:
            cursor = conn.execute("""
                SELECT id, description, amount_paise, type, category,
                       date_iso, account_id, statement_id
                FROM transactions
                ORDER BY date_iso DESC
            """)

            transactions = []
            for row in cursor.fetchall():
                transactions.append(Transaction(
                    id=row['id'],
                    description=row['description'],
                    amount_paise=row['amount_paise'],
                    type=row['type'],
                    category=row['category'],
                    date_iso=row['date_iso'],
                    account_id=row['account_id'],
                    statement_id=row['statement_id']
                ))

            return transactions

    def get_transactions_by_category(self) -> dict:
        """Get transaction summary by category."""
        with self.db.connection() as conn:
            cursor = conn.execute("""
                SELECT
                    category,
                    COUNT(*) as transaction_count,
                    SUM(CASE WHEN type = 'debit' THEN amount_paise ELSE 0 END) as total_debit_paise,
                    SUM(CASE WHEN type = 'credit' THEN amount_paise ELSE 0 END) as total_credit_paise
                FROM transactions
                GROUP BY category
                ORDER BY transaction_count DESC
            """)

            results = {}
            for row in cursor.fetchall():
                results[row['category']] = {
                    'transaction_count': row['transaction_count'],
                    'total_debit_paise': row['total_debit_paise'],
                    'total_credit_paise': row['total_credit_paise']
                }

            return results

    def get_uncategorized_transactions(self) -> List[Transaction]:
        """Get uncategorized transactions."""
        with self.db.connection() as conn:
            cursor = conn.execute("""
                SELECT id, description, amount_paise, type, category,
                       date_iso, account_id, statement_id
                FROM transactions
                WHERE category = 'Uncategorized'
                ORDER BY date_iso DESC
            """)

            transactions = []
            for row in cursor.fetchall():
                transactions.append(Transaction(
                    id=row['id'],
                    description=row['description'],
                    amount_paise=row['amount_paise'],
                    type=row['type'],
                    category=row['category'],
                    date_iso=row['date_iso'],
                    account_id=row['account_id'],
                    statement_id=row['statement_id']
                ))

            return transactions