"""Explicit database seeding fixtures.

The legacy autouse ``seed_test_database`` fixture has been removed.
Seeding is now opt-in via the ``seeded_db`` fixture so tests that need
baseline data can request it explicitly.

Design goals:
- No secondary sqlite3 connections during fixture initialization.
- No per-test PRAGMA schema inspection.
- No fixture debug prints.
- One canonical write connection per setup.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest

from src.core.db.connection import get_connection_context

_BASELINE_SEED_SQL = [
    (
        "accounts",
        """
        INSERT OR IGNORE INTO accounts
            (id, name, bank, account_type, balance_paise, account_number_last4)
        VALUES (1, 'Primary Checking', 'Test Bank', 'savings', 500000, '1234')
        """,
    ),
    (
        "statements",
        """
        INSERT OR IGNORE INTO statements (id, bank, file_name)
        VALUES (1, 'Test Bank', 'test.pdf')
        """,
    ),
    (
        "transactions",
        """
        INSERT OR IGNORE INTO transactions
            (id, statement_id, date, date_iso, description, amount_paise, type, account_id)
        VALUES (1, 1, '01/01/2025', '2025-01-01', 'Test Txn', 100000, 'debit', 1)
        """,
    ),
    (
        "account_balance_history",
        """
        INSERT OR IGNORE INTO account_balance_history
            (account_id, timestamp, balance_paise)
        VALUES (1, '2025-01-01T00:00:00', 500000)
        """,
    ),
    (
        "account_links",
        """
        INSERT OR IGNORE INTO account_links (account_id, linked_account_id)
        VALUES (1, 1)
        """,
    ),
]


@pytest.fixture(scope="function")
def seeded_db(finance_db: Any) -> Generator[Any, None, None]:
    """Provide a database pre-seeded with the canonical baseline data set.

    Tests that depend on the legacy autouse seed data should request
    this fixture explicitly. Tests that do not need baseline data can
    use the unseeded ``finance_db`` fixture instead.

    Args:
        finance_db: The isolated FinanceDB to seed.

    Yields:
        The same FinanceDB instance after baseline inserts have been applied.
    """
    db_path = str(finance_db.db_path)
    with get_connection_context(db_path) as conn:
        for _table, sql in _BASELINE_SEED_SQL:
            conn.execute(sql)

    yield finance_db
