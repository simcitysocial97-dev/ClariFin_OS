"""Bank domain repository."""
from src.repositories.base import BaseRepository


class BankRepository(BaseRepository):
    """Repository for bank-related operations."""

    def get_all(self):
        """Get all distinct bank names."""
        return self._db().get_banks()
