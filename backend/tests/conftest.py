"""Shared fixtures and configuration for all backend tests.

This conftest provides:
- finance_db fixture: Enterprise-grade temporary database with full schema initialization and lifecycle management
- test_client fixture: FastAPI TestClient with isolated DB and dependency injection overrides
- Shared builders, helpers, and deterministic seed data factories
- Hypothesis profiles and strict type enforcement for property testing
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from hypothesis import settings as hypothesis_settings

# Configure enterprise hypothesis profiles
hypothesis_settings.register_profile("ci", max_examples=500, deadline=None)
hypothesis_settings.register_profile("dev", max_examples=50, deadline=1000)
hypothesis_settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))


@pytest.fixture(scope="function")
def finance_db(tmp_path) -> Generator[Any, None, None]:
    """Create an enterprise-grade isolated FinanceDB for testing with automatic path propagation.

    Guarantees full DDL migration execution and clean teardown per test function.
    """
    from src.config import settings
    from src.db import FinanceDB

    db_path = tmp_path / f"test_finance_{os.getpid()}_{id(object())}.db"
    os.makedirs(db_path.parent, exist_ok=True)

    # 1. Force global environment & settings override for complete path isolation
    os.environ["FINANCE_DB_PATH"] = str(db_path)
    settings._database_path_override = str(db_path)

    # 2. Initialize database — FinanceDB.__init__() handles the full
    #    initialization sequence: create tables, run migrations, verify schema.
    #    No redundant calls to _create_tables() or _run_migrations() needed.
    db = FinanceDB(db_path=str(db_path))

    yield db

    # 3. Restore original configuration settings post-test
    settings._database_path_override = None

    # Enterprise teardown and resource release
    with contextlib.suppress(Exception):
        if hasattr(db, "_conn") and db._conn:
            db._conn.close()
            db._conn = None

    if db_path.exists():
        with contextlib.suppress(PermissionError):
            db_path.unlink()  # Windows file lock fallback safety


@pytest.fixture(autouse=True)
def seed_test_database(finance_db):
    """Safely seed minimal baseline data matching the actual database schema."""
    import sqlite3

    db_path = str(finance_db.db_path)
    conn = sqlite3.connect(db_path)

    try:
        # 1. Seed Accounts (using integer ID as required by schema)
        conn.execute("""
            INSERT OR IGNORE INTO accounts
            (id, name, bank, account_type, balance_paise, account_number_last4)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            1,
            "Primary Checking",
            "Test Bank",
            "savings",
            500000,
            "1234",
        ))

        # 2. Seed Statements (required as a foreign key prerequisite for transactions)
        conn.execute("""
            INSERT OR IGNORE INTO statements
            (id, bank, file_name)
            VALUES (?, ?, ?)
        """, (
            1,
            "Test Bank",
            "test.pdf",
        ))

        # 3. Seed Transactions
        conn.execute("""
            INSERT OR IGNORE INTO transactions
            (id, statement_id, date, date_iso, description, amount_paise, type, account_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            1,
            1,
            "01/01/2025",
            "2025-01-01",
            "Test Txn",
            100000,
            "debit",
            1,
        ))

        # 4. Seed Account Balance History
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(account_balance_history);")
        history_cols = [row[1] for row in cursor.fetchall()]
        print("DEBUG account_balance_history columns:", history_cols)
        if history_cols:
            conn.execute("""
                INSERT OR IGNORE INTO account_balance_history (account_id, timestamp, balance_paise)
                VALUES (?, ?, ?)
            """, (1, '2025-01-01T00:00:00', 500000))

        # 5. Seed Account Links
        cursor.execute("PRAGMA table_info(account_links);")
        link_cols = [row[1] for row in cursor.fetchall()]
        print("DEBUG account_links columns:", link_cols)
        if link_cols:
            conn.execute("""
                INSERT OR IGNORE INTO account_links (account_id, linked_account_id)
                VALUES (?, ?)
            """, (1, 1))

        conn.commit()
    except Exception as e:
        print(f"⚠️ seed_test_database failed: {e}")
        raise
    finally:
        conn.close()


@pytest.fixture
def db_path(finance_db: Any) -> str:
    """Get the absolute database path from the finance_db fixture."""
    return str(finance_db.db_path)


@pytest.fixture
def test_client(finance_db: Any) -> Generator[TestClient, None, None]:
    """Create a production-aligned FastAPI TestClient with isolated database bindings.

    Enables server exception propagation for rigorous debugging while routing
    app state to the isolated temporary test database.
    """
    from src.api import app

    # Bind application state to the isolated test database path
    app.state.db_path = str(finance_db.db_path)

    with TestClient(app, raise_server_exceptions=True) as client:
        yield client


@pytest.fixture
def client(test_client: TestClient) -> TestClient:
    """Enterprise alias for test_client fixture for contract, API, and e2e test suites."""
    return test_client


@pytest.fixture(scope="function")
def temp_db() -> Generator[str, None, None]:
    """Provide a raw temporary database file path with strict automatic cleanup."""
    import tempfile

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    from src.db import FinanceDB
    FinanceDB(db_path=path)
    yield path
    if os.path.exists(path):
        with contextlib.suppress(Exception):
            os.unlink(path)


# ============================================================================
# Enterprise Test Builders & Seed Factories
# ============================================================================


def make_transaction(
    date_iso: str = "2025-01-15",
    description: str = "ENTERPRISE_MERCHANT",
    amount_paise: int = 10000,
    category: str = "operations",
    time_iso: str | None = "10:00:00",
    txn_type: str = "debit",
    account_id: str = "1",
) -> dict[str, Any]:
    """Build a strongly-typed transaction dictionary adhering to core domain schema."""
    return {
        "date_iso": date_iso,
        "time_iso": time_iso,
        "description": description,
        "amount_paise": amount_paise,
        "category": category,
        "type": txn_type,
        "account_id": account_id,
    }


def make_reconciliation_match(
    debit_txn_id: int = 1,
    credit_txn_id: int = 2,
    debit_account_id: str = "1",
    credit_account_id: str = "ACC_SECONDARY_02",
    amount_paise: int = 10000,
    date_diff_days: int = 0,
    confidence_bps: int = 10000,
    match_type: str = "exact",
) -> dict[str, Any]:
    """Build a strongly-typed reconciliation match dictionary adhering to financial invariants."""
    return {
        "debit_txn_id": debit_txn_id,
        "credit_txn_id": credit_txn_id,
        "debit_account_id": debit_account_id,
        "credit_account_id": credit_account_id,
        "amount_paise": amount_paise,
        "date_diff_days": date_diff_days,
        "confidence_bps": confidence_bps,
        "match_type": match_type,
        "deterministic_key": f"{debit_txn_id}:{credit_txn_id}",
    }


# ============================================================================
# pytest Configuration & Custom Markers
# ============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register custom enterprise test markers for strict suite categorization."""
    config.addinivalue_line("markers", "capability: mark test as capability smoke test")
    config.addinivalue_line("markers", "contract: mark test as contract schema test")
    config.addinivalue_line("markers", "property: mark test as property-based hypothesis test")
    config.addinivalue_line("markers", "invariant: mark test as financial domain invariant test")
    config.addinivalue_line("markers", "golden: mark test as golden dataset baseline test")
    config.addinivalue_line("markers", "meta: mark test as meta-verification test")
