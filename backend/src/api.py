"""
FastAPI REST API for Personal Finance Tracker
==============================================

This API wraps the existing database and pipeline, exposing functionality
as HTTP endpoints for use by external applications (Next.js, mobile apps, etc.).

Run: python src/api.py
API Docs: http://localhost:8000/docs
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import health module for router registration
import src.health as health

# Import configuration and utilities
from config import settings

# Import mapper for DTO transformation
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
# Configuration
# ============================================================

# Upload directory
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# Helper Functions
# ============================================================

# Note: All utility functions (format_inr, parse_date, enrich_transaction, etc.)
# are now imported from src.common module to avoid duplication.


# ============================================================
# Pydantic Models
# ============================================================

class CategoryUpdate(BaseModel):
    category: str
    subcategory: str | None = None


class BulkCategoryUpdate(BaseModel):
    ids: list[int]
    category: str


class ImportExecute(BaseModel):
    filename: str
    mapping: dict
    member: str = "Self"


class MemberCreate(BaseModel):
    name: str
    color: str = "#6366F1"


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

# Banks routes → routers/banks.py
# Behavior routes → routers/behavior.py
# Cashflow routes → routers/cashflow.py
# Export routes → routers/export.py
# Investments routes → routers/investments.py
# Loans routes → routers/loans.py
# Managed accounts routes → routers/managed_accounts.py
# Networth routes → routers/networth.py
# Reconciliation routes → routers/reconciliation.py
# Transactions routes → routers/transactions.py
# Import routes → routers/import_router.py


# ============================================================
# Balance API Endpoints (Phase 2A)
# ============================================================


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
