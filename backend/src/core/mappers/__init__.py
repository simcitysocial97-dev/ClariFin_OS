"""
Domain Mappers
==============

Mappers transform domain objects into API DTOs.
They are the ONLY location responsible for creating API responses.

Architecture:
- Domain objects → Mappers → DTOs → JSON API responses
- Controllers should NEVER manually construct response dictionaries
- All monetary transformations happen here
- Backward compatibility fields added here
"""

from .account_mapper import AccountMapper
from .transaction_mapper import TransactionMapper
from .dashboard_mapper import DashboardMapper

__all__ = [
    'AccountMapper',
    'TransactionMapper',
    'DashboardMapper',
]