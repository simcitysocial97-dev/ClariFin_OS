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

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.errors import register_error_handlers
from src.health import register_health_routes
from src.startup import run_startup_validation

# ============================================================
# FastAPI App
# ============================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    # Ensure the SQLite schema exists/is current before serving requests.
    # Delegates to the canonical startup-validation owner (src/startup.py),
    # which now performs idempotent schema initialization.
    run_startup_validation()
    yield


app = FastAPI(
    title="Personal Finance API",
    description="REST API for personal finance tracker",
    version="1.0.0",
    lifespan=lifespan,
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
register_health_routes(app)

# Register routers
from src.routers import (
    accounts,
    audit,
    banks,
    behaviour,
    behaviour_workspace,
    cards_statements,
    cashflow,
    cashflow_workspace,
    credit_cards,
    credit_cards_workspace,
    dashboard,
    export,
    financial_events,
    financial_intelligence,
    forecast,
    import_router,
    investments,
    investments_workspace,
    loans,
    loans_workspace,
    managed_accounts,
    members,
    networth,
    networth_workspace,
    reconciliation,
    reconciliation_workspace,
    transactions,
)

app.include_router(accounts.router)
app.include_router(audit.router)
app.include_router(banks.router)
app.include_router(behaviour.router)
app.include_router(behaviour_workspace.router)
app.include_router(cards_statements.router)
app.include_router(credit_cards.router)
app.include_router(credit_cards_workspace.router)
app.include_router(cashflow.router)
app.include_router(cashflow_workspace.router)
app.include_router(dashboard.router)
app.include_router(export.router)
app.include_router(financial_events.router)
app.include_router(
    financial_intelligence.router,
    prefix="/api/v1",
    tags=["financial-intelligence"],
)
app.include_router(forecast.router)
app.include_router(import_router.router)
app.include_router(investments.router)
app.include_router(investments_workspace.router)
app.include_router(loans.router)
app.include_router(loans_workspace.router)
app.include_router(managed_accounts.router)
app.include_router(members.router)
app.include_router(networth.router)
app.include_router(networth_workspace.router)
app.include_router(reconciliation.router)
app.include_router(reconciliation_workspace.router)
app.include_router(transactions.router)

# ============================================================
# Run Server
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
