"""API routers organized by domain."""
from . import (
    accounts,
    audit,
    banks,
    behavior,
    cards_statements,
    cashflow,
    dashboard,
    export,
    financial_intelligence,
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

__all__ = ["accounts", "audit", "banks", "behavior", "cards_statements", "cashflow", "dashboard", "export", "financial_intelligence", "health", "import_router", "investments", "loans", "managed_accounts", "networth", "reconciliation", "transactions", "members"]
