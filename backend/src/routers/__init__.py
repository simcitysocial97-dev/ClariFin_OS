"""API routers organized by domain."""
from . import (
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

__all__ = ["banks", "behavior", "cards_statements", "cashflow", "export", "health", "import_router", "investments", "loans", "managed_accounts", "networth", "reconciliation", "transactions", "members"]
