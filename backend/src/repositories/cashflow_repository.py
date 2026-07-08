"""Cashflow domain repository."""
from src.repositories.base import BaseRepository


class CashflowRepository(BaseRepository):
    """Repository for cashflow operations."""

    def get_monthly_cashflow(
        self,
        months: int = 6,
        member: str | None = None,
    ) -> list[dict]:
        """
        Returns month-by-month income and expense aggregation.
        All monetary values in paise (INTEGER).
        Uses date_iso for proper month grouping.
        """
        return self._db().get_monthly_cashflow(months=months, member=member)
