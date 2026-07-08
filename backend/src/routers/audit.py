"""Audit and integrity verification endpoints."""
from fastapi import APIRouter, HTTPException

from engines.ledger_audit_engine import (
    run_full_audit,
)
from src.common import DB_PATH

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/report")
def api_audit_report():
    """
    Run full ledger audit and return combined report.

    Phase 2C: Read-only integrity verification.

    Returns:
        {
            "overall_status": "PASS" or "FAIL",
            "ledger_integrity": {...},
            "hash_verification": {...}
        }
    """
    try:
        report = run_full_audit(DB_PATH)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
