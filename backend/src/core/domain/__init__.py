"""
Financial Domain Layer
======================

This module provides the canonical monetary domain abstractions for ClariFin_OS.

Architecture:
- All monetary values are represented as integer paise (1 INR = 100 paise)
- No floating-point arithmetic for financial calculations
- Type-safe operations prevent unit confusion
- Single source of truth for all money operations

Usage:
    from core.domain.money import Money
    
    # Create from paise
    amount = Money(100000)  # ₹1,000.00
    
    # Arithmetic
    total = amount1.add(amount2)
    
    # Serialization
    dto = amount.to_dict()  # {"paise": 100000}
"""

from .money import Money

__all__ = ['Money']