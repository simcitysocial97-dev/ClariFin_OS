"""Audit and integrity verification endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException

from src.services import AuditService

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/report")
def api_audit_report() -> dict[str, Any]:
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
        service = AuditService()
        report = service.run_full_audit()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
