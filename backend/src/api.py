"""
FastAPI REST API for Personal Finance Tracker
=============================================

This API wraps the existing database and pipeline, exposing functionality
as HTTP endpoints for use by external applications (Next.js, mobile apps, etc.).

Run: python src/api.py
API Docs: http://localhost:8000/docs

Phase 2 Router Extraction Complete:
- All route handlers extracted to src/routers/
- This file now contains only app setup, middleware, and router registration
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import health module for router registration
import src.health as health

# Import configuration and utilities
from config import settings

# Import error handlers
from errors import register_error_handlers

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
    accounts,
    audit,
    banks,
    behavior,
    cards_statements,
    cashflow,
    dashboard,
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

app.include_router(accounts.router)
app.include_router(audit.router)
app.include_router(banks.router)
app.include_router(behavior.router)
app.include_router(cards_statements.router)
app.include_router(cashflow.router)
app.include_router(dashboard.router)
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
# Run Server
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
