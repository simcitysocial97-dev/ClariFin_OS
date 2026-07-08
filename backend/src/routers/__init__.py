"""API routers organized by domain."""
from . import (
    banks,
    cashflow,
    export,
    health,
    investments,
    loans,
    managed_accounts,
    members,
    networth,
)

__all__ = ["banks", "cashflow", "export", "health", "investments", "loans", "managed_accounts", "networth", "members"]
