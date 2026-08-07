"""Thin root conftest — pytest_plugins loader and backward-compatible re-exports.

All fixtures, markers, and configuration have been moved into modular
plugins under ``tests/fixtures/``. This file exists solely to:

1. Register the fixture plugins with pytest.
2. Preserve legacy import paths for tests that import symbols directly
   from ``tests.conftest`` (see backward-compatibility notes below).

Backward-compatible re-exports
-------------------------------
The following symbols are imported here so that existing code such as::

    from tests.conftest import make_transaction

continues to work without modification.
"""

from __future__ import annotations

# ============================================================
# Plugin Registration
# ============================================================

pytest_plugins = [
    "tests.fixtures.pytest_config",
    "tests.fixtures.hypothesis",
    "tests.fixtures.database",
    "tests.fixtures.seed",
    "tests.fixtures.client",
    "tests.fixtures.builders",
    "tests.fixtures.factories",
]

# ============================================================
# Backward-Compatible Re-Exports
# ============================================================
# Tests that import directly from tests.conftest continue to work.
from tests.fixtures.builders import (  # noqa: F401
    make_reconciliation_match,
    make_transaction,
)
from tests.fixtures.factories import (  # noqa: F401
    AccountBuilder,
    CreditCardBuilder,
    FinancialEventBuilder,
    HouseholdBuilder,
    LoanBuilder,
    ReconciliationMatchBuilder,
    StatementBuilder,
    TransactionBuilder,
)
