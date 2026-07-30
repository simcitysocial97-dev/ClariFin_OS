"""Credit Card domain repository - Persistence only.

All methods are focused solely on data persistence.
No financial calculations or business logic.
"""

from typing import Any

from src.repositories.base import BaseRepository


class CreditCardRepository(BaseRepository):
    """Repository for credit card persistence operations.

    Only handles CRUD for credit cards.
    All calculations belong to credit_card_engine.
    """

    # ============================================================
    # Credit Card CRUD Operations
    # ============================================================

    def create_card(
        self,
        card_id: str,
        account_id: str,
        name: str,
        bank: str,
        credit_limit_paise: int,
        interest_rate_bps: int,
        card_last4: str | None = None,
        annual_fee_paise: int = 0,
        billing_day: int | None = None,
        due_day_offset: int = 21,
        notes: str | None = None,
    ) -> str:
        """Create a new credit card record. Returns the card ID."""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO credit_cards (
                    id, account_id, name, bank, card_last4,
                    credit_limit_paise, annual_fee_paise, interest_rate_bps,
                    billing_day, due_day_offset, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    card_id,
                    account_id,
                    name,
                    bank,
                    card_last4,
                    credit_limit_paise,
                    annual_fee_paise,
                    interest_rate_bps,
                    billing_day,
                    due_day_offset,
                    notes,
                ),
            )
            conn.commit()
        return card_id

    def get_card(self, card_id: str) -> dict[str, Any] | None:
        """Get a single credit card by ID as a raw dict."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM credit_cards WHERE id = ?", (card_id,)
            ).fetchone()
        return dict(row) if row else None

    def list_cards(self, account_id: str | None = None) -> list[dict[str, Any]]:
        """Get all active credit cards as raw dicts.

        If account_id is provided, filters by account.
        """
        if account_id:
            with self._get_conn() as conn:
                rows = conn.execute(
                    """
                    SELECT * FROM credit_cards
                    WHERE is_active = 1 AND account_id = ?
                    ORDER BY created_at DESC
                """,
                    (account_id,),
                ).fetchall()
        else:
            with self._get_conn() as conn:
                rows = conn.execute("""
                    SELECT * FROM credit_cards
                    WHERE is_active = 1
                    ORDER BY created_at DESC
                """).fetchall()
        return [dict(r) for r in rows]

    def update_card(
        self, card_id: str, **kwargs: str | int | float | None
    ) -> dict[str, Any] | None:
        """Update credit card fields. Only updates provided fields."""
        allowed = {
            "name",
            "credit_limit_paise",
            "annual_fee_paise",
            "interest_rate_bps",
            "billing_day",
            "due_day_offset",
            "notes",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return self.get_card(card_id)

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = datetime('now')"
        values = list(updates.values()) + [card_id]

        with self._get_conn() as conn:
            conn.execute(f"UPDATE credit_cards SET {set_clause} WHERE id = ?", values)
            conn.commit()
        return self.get_card(card_id)

    def deactivate_card(self, card_id: str) -> bool:
        """Soft delete a credit card (set is_active to 0)."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE credit_cards SET is_active = 0, updated_at = datetime('now') WHERE id = ?",
                (card_id,),
            )
            conn.commit()
            changes_row = conn.execute("SELECT changes()").fetchone()
        return bool(changes_row[0]) if changes_row else False
