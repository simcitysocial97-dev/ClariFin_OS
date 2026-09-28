"""
M9-C57 — Financial semantic layer.

Provides invariant definitions, assertion helpers, and failure parsing
for financial domain verification. The semantic layer sits above the
execution orchestrator and adds domain-meaningful error messages to
test failures.
"""

from __future__ import annotations

from .assertions import (
    FINANCIAL_INVARIANTS,
    FinancialAssertion,
    FinancialInvariant,
    FinancialInvariantViolation,
)
from .parser import SemanticFailure, SemanticFailureParser

__all__ = [
    "FinancialInvariant",
    "FinancialInvariantViolation",
    "FINANCIAL_INVARIANTS",
    "FinancialAssertion",
    "SemanticFailure",
    "SemanticFailureParser",
]
