"""
FastAPI REST API for Personal Finance Tracker
=============================================

This API wraps the existing database and pipeline, exposing functionality
as HTTP endpoints for use by external applications (Next.js, mobile apps, etc.).

Run: python src/api.py
API Docs: http://localhost:8000/docs

Phase 2 Router Extraction Complete:
- All route handlers extracted to src/routers/
- This file now contains only app setup, middleware, and remaining endpoints
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Import health module for router registration
import src.health as health

# Import configuration and utilities
from config import settings

# Import existing modules
from engines.balance_engine import (
    compute_account_balance,
    compute_running_balance,
    get_accounts_list,
)
from engines.ledger_audit_engine import (
    run_full_audit,
)
from errors import register_error_handlers

# Import shared utilities from common module
from src.common import (
    DB_PATH,
)

# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(
    title="Personal Finance API",
    description="REST API for personal finance tracker",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
register_error_handlers(app)

# Register health router
health.register_health_routes(app)

# Register routers
from src.routers import (
    banks,
    behavior,
    cards_statements,
    cashflow,
    export,
    health,
    import_router,
    investments,
    loans,
    managed_accounts,
    members,
    networth,
    reconciliation,
    transactions,
)

app.include_router(banks.router)
app.include_router(behavior.router)
app.include_router(cards_statements.router)
app.include_router(cashflow.router)
app.include_router(export.router)
app.include_router(health.router)
app.include_router(import_router.router)
app.include_router(investments.router)
app.include_router(loans.router)
app.include_router(managed_accounts.router)
app.include_router(networth.router)
app.include_router(reconciliation.router)
app.include_router(transactions.router)
app.include_router(members.router)

# ============================================================
# Balance API Endpoints (Phase 2A)
# ============================================================

@app.get("/api/accounts")
def api_get_accounts():
    """Get all accounts with their computed balances."""
    try:
        accounts = get_accounts_list(DB_PATH)
        return {"accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/accounts/{account_id}/balance")
def api_get_account_balance(account_id: str):
    """Get current balance for a specific account."""
    try:
        result = compute_account_balance(DB_PATH, account_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/accounts/{account_id}/running-balance")
def api_get_running_balance(account_id: str, limit: int = Query(100, ge=1, le=1000)):
    """Get running balance history for an account."""
    try:
        result = compute_running_balance(DB_PATH, account_id)
        # Return limited results
        return {
            "account_id": account_id,
            "transactions": result[:limit],
            "total": len(result),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Audit API Endpoints (Phase 2C)
# ============================================================

@app.get("/api/audit/report")
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


# ============================================================
# Run Server
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
