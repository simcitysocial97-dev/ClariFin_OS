"""
Core Domain Layer
==================

This module provides the foundational domain abstractions for ClariFin_OS.

Architecture:
- Domain models (Money)
- DTOs for API contracts
- Mappers for domain-to-DTO transformation

Usage:
    from core.domain.money import Money
    from core.dtos.account_dto import AccountDTO
    from core.mappers.account_mapper import AccountMapper
"""

from .domain import Money
from .dtos import (
    AccountDTO,
    AccountListResponse,
    TransactionDTO,
    TransactionListResponse,
    DashboardSummaryDTO,
    OverviewDTO,
)
from .mappers import AccountMapper, TransactionMapper, DashboardMapper

__all__ = [
    'Money',
    'AccountDTO',
    'AccountListResponse',
    'TransactionDTO',
    'TransactionListResponse',
    'DashboardSummaryDTO',
    'OverviewDTO',
    'AccountMapper',
    'TransactionMapper',
    'DashboardMapper',
]