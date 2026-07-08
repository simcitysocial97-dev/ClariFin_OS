"""API routers organized by domain."""
from . import (
    banks,
    cards_statements,
    cashflow,
    export,
    health,
    investments,
    loans,
    managed_accounts,
    members,
    networth,
)

__all__ = ["banks", "cards_statements", "cashflow", "export", "health", "investments", "loans", "managed_accounts", "networth", "members"]
