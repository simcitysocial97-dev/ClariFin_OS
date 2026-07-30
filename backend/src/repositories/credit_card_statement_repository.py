"""Credit Card Statement domain repository - Persistence only.

All methods are focused solely on data persistence.
No financial calculations or business logic.
"""

from typing import Any

from src.repositories.base import BaseRepository


class CreditCardStatementRepository(BaseRepository):
    """Repository for credit card statement persistence operations.

    Only handles CRUD for statements.
    All calculations belong to credit_card_engine.
    """

    def create_statement(
        self,
        card_id: str,
        statement_date: str,
        due_date: str,
        total_outstanding_paise: int,
        minimum_due_paise: int,
        interest_charged_paise: int = 0,
    ) -> int:
        """Create a new statement record. Returns the statement ID.

        Uses UNIQUE(card_id, statement_date) constraint to prevent duplicates.
        """
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO credit_card_statements (
                    card_id, statement_date, due_date,
                    total_outstanding_paise, minimum_due_paise,
                    interest_charged_paise
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    card_id,
                    statement_date,
                    due_date,
                    total_outstanding_paise,
                    minimum_due_paise,
                    interest_charged_paise,
                ),
            )
            conn.commit()
        return cur.lastrowid or 0

    def get_statement(self, statement_id: int) -> dict[str, Any] | None:
        """Get a single statement by ID as a raw dict."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM credit_card_statements WHERE id = ?", (statement_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_latest_statement(self, card_id: str) -> dict[str, Any] | None:
        """Get the most recent statement for a card."""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM credit_card_statements
                WHERE card_id = ?
                ORDER BY statement_date DESC
                LIMIT 1
            """,
                (card_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_latest_open_statement(self, card_id: str) -> dict[str, Any] | None:
        """Get the most recent statement without a payment."""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM credit_card_statements
                WHERE card_id = ? AND payment_date IS NULL
                ORDER BY statement_date DESC
                LIMIT 1
            """,
                (card_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_statements(
        self,
        card_id: str,
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        """Get statement history for a card, most recent first."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM credit_card_statements
                WHERE card_id = ?
                ORDER BY statement_date DESC
                LIMIT ?
            """,
                (card_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def update_payment(
        self,
        statement_id: int,
        payment_date: str,
        amount_paise: int,
    ) -> bool:
        """Record a payment on a statement."""
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE credit_card_statements
                SET payment_date = ?, payment_amount_paise = ?
                WHERE id = ?
            """,
                (payment_date, amount_paise, statement_id),
            )
            conn.commit()
            changes = conn.execute("SELECT changes()").fetchone()
        return bool(changes[0]) if changes else False

    def list_all_statements(self) -> list[dict[str, Any]]:
        """Get all statements for workspace services."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM credit_card_statements
                ORDER BY statement_date DESC
            """).fetchall()
        return [dict(r) for r in rows]
