"""Statement business orchestration service."""

from typing import Any

from src.engines.balance_engine import validate_statement_balance
from src.repositories.statement_repository import StatementRepository
from src.services.base import BaseService


class StatementService(BaseService):
    """
    Business logic for statement operations.

    Orchestrates statement repository and balance engine.
    """

    def __init__(self, db_path: str | None = None):
        super().__init__(db_path)
        self.repo = StatementRepository(self.db_path)

    def validate_statement(self, statement_id: int, claimed_balance_paise: int) -> dict[str, Any]:
        """Validate a statement's closing balance against computed balance."""
        return validate_statement_balance(self.db_path, statement_id, claimed_balance_paise)
