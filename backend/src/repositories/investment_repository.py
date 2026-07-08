"""Investment domain repository."""
from src.repositories.base import BaseRepository


class InvestmentRepository(BaseRepository):
    """Repository for investment-related operations."""

    def get_all(self):
        """Get all active investments."""
        return self._db().get_all_investments()

    def create(self, **kwargs):
        """Create a new investment."""
        return self._db().create_investment(**kwargs)

    def update(self, investment_id, **kwargs):
        """Update an investment."""
        return self._db().update_investment(investment_id, **kwargs)

    def delete(self, investment_id):
        """Delete an investment."""
        return self._db().delete_investment(investment_id)
