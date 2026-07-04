"""Card Repository

Data access layer for card entities.
"""

from typing import List
import sqlite3
from core.models import Card
from core.db.connection import DatabaseConnection

class CardRepository:
    """Repository for card data access."""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def get_all_cards(self) -> List[Card]:
        """Get all cards from database."""
        with self.db.connection() as conn:
            cursor = conn.execute("""
                SELECT c.id, c.card_name, c.issuer, c.card_type,
                       c.credit_limit_paise, c.is_active, c.account_id
                FROM cards c
                ORDER BY c.card_name
            """)

            cards = []
            for row in cursor.fetchall():
                cards.append(Card(
                    id=row['id'],
                    card_name=row['card_name'],
                    issuer=row['issuer'],
                    card_type=row['card_type'],
                    credit_limit_paise=row['credit_limit_paise'],
                    account_id=row['account_id'],
                    is_active=bool(row['is_active'])
                ))

            return cards

    def get_card_by_id(self, card_id: int) -> Card | None:
        """Get card by ID."""
        with self.db.connection() as conn:
            cursor = conn.execute("""
                SELECT c.id, c.card_name, c.issuer, c.card_type,
                       c.credit_limit_paise, c.is_active, c.account_id
                FROM cards c
                WHERE c.id = ?
            """, (card_id,))

            row = cursor.fetchone()
            if row:
                return Card(
                    id=row['id'],
                    card_name=row['card_name'],
                    issuer=row['issuer'],
                    card_type=row['card_type'],
                    credit_limit_paise=row['credit_limit_paise'],
                    account_id=row['account_id'],
                    is_active=bool(row['is_active'])
                )
            return None