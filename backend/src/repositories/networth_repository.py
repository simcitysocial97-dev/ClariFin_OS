"""Net worth domain repository."""
from src.repositories.base import BaseRepository


class NetWorthRepository(BaseRepository):
    """Repository for net worth operations."""

    def get_networth_data(self) -> dict:
        """
        Get all data needed for net worth calculation.
        Returns accounts, loans, investments, and statements.
        """
        return self._db().get_networth_data()

    def get_net_worth(self) -> dict:
        """
        Calculate net worth from accounts, loans, and investments.
        """
        return self._db().get_net_worth()
