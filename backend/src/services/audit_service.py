"""
Audit business orchestration service.
"""
from typing import Any
from src.engines.ledger_audit_engine import run_full_audit
from src.services.base import BaseService


class AuditService(BaseService):
    """
    Orchestrates audit operations using engines.

    Provides integrity verification for ledger data.
    """

    def run_full_audit(self) -> dict[str, Any]:
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
