"""Net worth domain repository."""
from src.repositories.base import BaseRepository


class NetWorthRepository(BaseRepository):
    """Repository for net worth operations."""

    def get_networth_data(self) -> dict:
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
            "loans": LoanRepository(self.db_path).get_all(),
            "investments": InvestmentRepository(self.db_path).get_all(),
            "statements": StatementRepository(self.db_path).get_all_statements(),
        }

    def get_net_worth(self) -> dict:
        """
        Calculate net worth from accounts, loans, and investments.
        Returns:
            {
                total_assets_paise: int,
                total_liabilities_paise: int,
                net_worth_paise: int,
                accounts_total_paise: int,
                loans_total_paise: int,
                investments_total_paise: int
            }
        """
        with self._get_conn() as conn:
            # Get total account balances (assets)
            accounts_row = conn.execute(
                "SELECT COALESCE(SUM(balance_paise), 0) as total FROM accounts WHERE is_active = 1"
            ).fetchone()
            accounts_total = accounts_row[0] or 0

            # Get total outstanding loans (liabilities)
            loans_row = conn.execute(
                "SELECT COALESCE(SUM(outstanding_paise), 0) as total FROM loans WHERE status = 'active'"
            ).fetchone()
            loans_total = loans_row[0] or 0

            # Get total investment value
            investments_row = conn.execute(
                "SELECT COALESCE(SUM(current_value_paise), 0) as total FROM investments WHERE is_active = 1"
            ).fetchone()
            investments_total = investments_row[0] or 0

            # Net worth = (accounts + investments) - loans
            net_worth = (accounts_total + investments_total) - loans_total

        return {
            "total_assets_paise": accounts_total + investments_total,
            "total_liabilities_paise": loans_total,
            "net_worth_paise": net_worth,
            "accounts_total_paise": accounts_total,
            "loans_total_paise": loans_total,
            "investments_total_paise": investments_total,
        }
