"""Net worth domain repository."""
from typing import Any

from src.repositories.base import BaseRepository


class NetWorthRepository(BaseRepository):
    """Repository for net worth data aggregation."""

    def get_networth_data(self) -> dict[str, Any]:
        """
        Get all data needed for net worth calculation.
        Returns accounts, loans, investments, and statements.
        """
        from src.repositories.account_repository import AccountRepository
        from src.repositories.investment_repository import InvestmentRepository
        from src.repositories.loan_repository import LoanRepository
        from src.repositories.statement_repository import StatementRepository

        return {
            "accounts": AccountRepository(self.db_path).get_all_accounts(),
            "loans": LoanRepository(self.db_path).list_loans(),
            "investments": InvestmentRepository(self.db_path).get_all(),
            "statements": StatementRepository(self.db_path).get_all_statements(),
        }
