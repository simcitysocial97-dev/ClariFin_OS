"""API routers organized by domain."""
from . import (
    accounts,
    audit,
    banks,
    behavior,
    behaviour_workspace,
    cards_statements,
    cashflow,
    cashflow_workspace,
    credit_cards_workspace,
    dashboard,
    export,
    forecast,
    health,
    import_router,
    investments,
    investments_workspace,
    loans,
    loans_workspace,
    managed_accounts,
    members,
    networth,
    reconciliation,
    reconciliation_workspace,
    transactions,
)

__all__ = ["accounts", "audit", "banks", "behavior", "behaviour_workspace", "cards_statements", "cashflow", "cashflow_workspace", "credit_cards_workspace", "dashboard", "export", "forecast", "health", "import_router", "investments", "investments_workspace", "loans", "loans_workspace", "managed_accounts", "networth", "reconciliation", "reconciliation_workspace", "transactions", "members"]
