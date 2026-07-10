"""Reconciliation business orchestration service."""

from typing import Any

from src.engines.reconciliation_engine import find_potential_matches
from src.repositories.reconciliation_repository import ReconciliationRepository
from src.services.base import BaseService


class ReconciliationService(BaseService):
    """
    Business logic for reconciliation operations.

    Orchestrates reconciliation repository and reconciliation engine.
    """

    def __init__(self, db_path: str | None = None):
        super().__init__(db_path)
        self.repo = ReconciliationRepository(self.db_path)

    def scan_potential_matches(self) -> list[dict[str, Any]]:
        """
        Scan for potential transfer matches across accounts.

        Phase 2B.1: Deterministic matching with confidence scoring.
        Returns potential matches that can be saved as reconciliations.
        """
        return find_potential_matches(self.db_path)
