"""Audit domain repository."""
from src.repositories.base import DB_PATH
from src.engines.ledger_audit_engine import run_full_audit


class AuditRepository:
    """Repository for audit operations."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or DB_PATH

    def run_full_audit(self) -> dict:
        """
        Run all audit checks and return combined report.

        Returns:
            {
                "ledger_integrity": {...},
                "hash_verification": {...},
                "overall_status": "PASS" or "FAIL"
            }
        """
        return run_full_audit(self.db_path)
