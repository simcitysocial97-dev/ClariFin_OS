"""Centralized router registry for the FastAPI application.

This module provides a single source of truth for all API routers,
making it easy to see what endpoints are available.
"""

from fastapi import FastAPI

# Import all router modules
from src.routers import (
    transactions,
    upload,
    categories,
    accounts,
    dashboard,
    reconciliation,
    behavior,
    audit,
    cards,
    income_sources,
    loans,
    investments,
    recurring,
    snapshots,
    projections,
    export,
    jobs,
    imports,
    cashflow_true_net,
)

# List of all routers to register
# Each router is imported from its module and included in this list
ROUTERS = [
    transactions.router,
    upload.router,
    categories.router,
    accounts.router,
    dashboard.router,
    reconciliation.router,
    behavior.router,
    audit.router,
    cards.router,
    income_sources.router,
    loans.router,
    investments.router,
    recurring.router,
    snapshots.router,
    projections.router,
    export.router,
    jobs.router,
    imports.router,
    cashflow_true_net.router,
]


def register_routers(app: FastAPI) -> None:
    """Register all routers with the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    for router in ROUTERS:
        app.include_router(router)
