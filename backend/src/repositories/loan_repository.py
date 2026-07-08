"""Loan domain repository."""
from src.repositories.base import BaseRepository


class LoanRepository(BaseRepository):
    """Repository for loan-related operations."""

    def get_all(self):
        """Get all active loans."""
        return self._db().get_all_loans()

    def create(self, **kwargs):
        """Create a new loan."""
        return self._db().create_loan(**kwargs)

    def update(self, loan_id, **kwargs):
        """Update a loan."""
        return self._db().update_loan(loan_id, **kwargs)

    def delete(self, loan_id):
        """Delete a loan."""
        return self._db().delete_loan(loan_id)

    def get_by_id(self, loan_id):
        """Get a single loan by ID."""
        return self._db().get_loan_by_id(loan_id)
