"""
Audit Router
============
Endpoints for ledger audit and integrity checks.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter

from src.dependencies import get_db
from src.logger import log

router = APIRouter()

@router.get("/api/audit/ledger")
def api_audit_ledger():
    """Get ledger audit results."""
    db = get_db()
    from src.engines.ledger_audit_engine import run_full_audit

    report = run_full_audit(db)

    return {
        "ledger_audit": report,
        "status": "completed",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/api/audit/report")
def api_audit_report():
    """Get full audit report."""
    db = get_db()
    from src.engines.ledger_audit_engine import run_full_audit

    report = run_full_audit(db)

    return report