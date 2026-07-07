"""
Data Transfer Objects (DTOs)
=============================

DTOs define the API contract between backend and frontend.
All monetary fields use the _paise suffix to make units explicit.

Architecture:
- DTOs are the ONLY way to serialize domain objects to JSON
- All monetary fields must end with _paise
- Backward compatibility fields end with _rupees (temporary)
- DTOs provide validation and documentation via Pydantic
"""

from .account_dto import AccountDTO, AccountListResponse
from .dashboard_dto import DashboardSummaryDTO, OverviewDTO
from .transaction_dto import TransactionDTO, TransactionListResponse

__all__ = [
    'AccountDTO',
    'AccountListResponse',
    'TransactionDTO',
    'TransactionListResponse',
    'DashboardSummaryDTO',
    'OverviewDTO',
]
