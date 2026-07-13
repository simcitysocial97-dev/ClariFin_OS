"""Liquidity Pattern Repository - Persistence for liquidity provider/purpose patterns.

LOC WATCH: No repository file > 200 LOC.
"""
from typing import Any

from src.repositories.base import BaseRepository


class LiquidityPatternRepository(BaseRepository):
    """Repository for liquidity pattern operations."""

    def get_active_provider_patterns(self) -> list[dict[str, Any]]:
        """Get all active liquidity provider patterns."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, provider_name, description_pattern,
                       fee_min_bps, fee_max_bps,
                       review_fee_min_bps, review_fee_max_bps,
                       typical_settlement_days, is_active, confirmed_by_user
                FROM liquidity_provider_patterns
                WHERE is_active = 1
                ORDER BY provider_name
            """).fetchall()
        return [dict(row) for row in rows]

    def get_active_purpose_patterns(self) -> list[dict[str, Any]]:
        """Get all active liquidity purpose patterns."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, purpose, description_pattern, is_active
                FROM liquidity_purpose_patterns
                WHERE is_active = 1
                ORDER BY purpose
            """).fetchall()
        return [dict(row) for row in rows]

    def get_provider_by_id(self, pattern_id: int) -> dict[str, Any] | None:
        """Get a single provider pattern by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM liquidity_provider_patterns WHERE id = ?",
                (pattern_id,),
            ).fetchone()
        return dict(row) if row else None

    def confirm_pattern(self, pattern_id: int) -> bool:
        """Mark a provider pattern as confirmed by user."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE liquidity_provider_patterns SET confirmed_by_user = 1 WHERE id = ?",
                (pattern_id,),
            )
            conn.commit()
            changes = conn.execute("SELECT changes()").fetchone()
        return bool(changes[0]) if changes else False

    def insert_new_pattern(
        self,
        provider_name: str,
        description_pattern: str,
        fee_min_bps: int = 150,
        fee_max_bps: int = 400,
        review_fee_min_bps: int = 50,
        review_fee_max_bps: int = 800,
        typical_settlement_days: int = 2,
    ) -> int:
        """
        Insert a new provider pattern.

        Returns the pattern ID.
        """
        with self._get_conn() as conn:
            cur = conn.execute("""
                INSERT INTO liquidity_provider_patterns
                    (provider_name, description_pattern, fee_min_bps, fee_max_bps,
                     review_fee_min_bps, review_fee_max_bps, typical_settlement_days,
                     is_active, confirmed_by_user)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)
            """, (
                provider_name,
                description_pattern,
                fee_min_bps,
                fee_max_bps,
                review_fee_min_bps,
                review_fee_max_bps,
                typical_settlement_days,
            ))
            conn.commit()
        return int(cur.lastrowid or 0)

    def deactivate_pattern(self, pattern_id: int) -> bool:
        """Deactivate a provider pattern."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE liquidity_provider_patterns SET is_active = 0 WHERE id = ?",
                (pattern_id,),
            )
            conn.commit()
            changes = conn.execute("SELECT changes()").fetchone()
        return bool(changes[0]) if changes else False