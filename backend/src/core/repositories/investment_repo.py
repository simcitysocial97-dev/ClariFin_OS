"""Investment Repository

Data access layer for investment entities.
"""

from typing import List
import sqlite3
from core.models import Investment
from core.db.connection import DatabaseConnection

class InvestmentRepository:
    """Repository for investment data access."""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def get_all_investments(self) -> List[Investment]:
        """Get all investments from database."""
        with self.db.connection() as conn:
            cursor = conn.execute("""
                SELECT id, type as investment_type, platform,
                       current_value_paise, is_active
                FROM investments
                ORDER BY platform, type
            """)

            investments = []
            for row in cursor.fetchall():
                investments.append(Investment(
                    id=row['id'],
                    investment_type=row['investment_type'],
                    platform=row['platform'],
                    current_value_paise=row['current_value_paise'],
                    is_active=bool(row['is_active'])
                ))

            return investments

    def get_investment_by_id(self, investment_id: int) -> Investment | None:
        """Get investment by ID."""
        with self.db.connection() as conn:
            cursor = conn.execute("""
                SELECT id, type as investment_type, platform,
                       current_value_paise, is_active
                FROM investments
                WHERE id = ?
            """, (investment_id,))

            row = cursor.fetchone()
            if row:
                return Investment(
                    id=row['id'],
                    investment_type=row['investment_type'],
                    platform=row['platform'],
                    current_value_paise=row['current_value_paise'],
                    is_active=bool(row['is_active'])
                )
            return None