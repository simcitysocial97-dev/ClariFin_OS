"""Shared fixtures and configuration for all backend tests.

This conftest provides:
- finance_db fixture: Temporary database with proper lifecycle
- test_client fixture: FastAPI TestClient with isolated DB
- Shared builders and helpers
- Hypothesis profiles for property testing
"""

from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

# Ensure src is on path for all tests
_src_path = str(Path(__file__).parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture
def finance_db() -> Generator[Any, None, None]:
    """Create a temporary FinanceDB for testing.

    Uses pytest's tmp_path for automatic cleanup.
    Replaces the tempfile.mkstemp + os.unlink pattern used in many tests.
    """
    from db import FinanceDB

    db_path = str(Path(__file__).parent / "data" / "test_finance.db")
    os.makedirs(str(Path(db_path).parent), exist_ok=True)
    db = FinanceDB(db_path=db_path)
    yield db
    # Cleanup
    if db._conn:
        db._conn.close()
        db._conn = None
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def db_path(finance_db: Any) -> str:
    """Get the database path from a finance_db fixture."""
    return str(finance_db.db_path)


@pytest.fixture
def test_client(finance_db: Any) -> Any:
    """Create a FastAPI TestClient with an isolated database.

    Uses the finance_db fixture for proper isolation.
    Uses raise_server_exceptions=False so that 500 errors are returned
    as HTTP responses rather than raising in the test process.
    """
    from fastapi.testclient import TestClient

    from src.api import app

    # Override the db_path in the app
    app.state.db_path = str(finance_db.db_path)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def client(test_client: Any) -> Any:
    """Alias for test_client fixture for contract and e2e tests."""
    return test_client


@pytest.fixture
def temp_db():
    """Temporary database fixture for testing.

    Creates a temp file and yields the path.
    """
    import tempfile
    import os
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield db_path
    os.unlink(db_path)


# ============================================================================
# Transaction Builders
# ============================================================================


def make_transaction(
    date_iso: str = "2025-01-15",
    description: str = "MERCHANT",
    amount_paise: int = 10000,
    category: str = "shopping",
    time_iso: str | None = None,
    txn_type: str = "debit",
) -> dict[str, Any]:
    """Create a transaction dict for testing.

    Replaces the copy-pasted make_transaction helper in multiple test files.
    """
    return {
        "date_iso": date_iso,
        "time_iso": time_iso,
        "description": description,
        "amount_paise": amount_paise,
        "category": category,
        "type": txn_type,
    }


# ============================================================================
# pytest Configuration
# ============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "capability: mark test as capability smoke test")
    config.addinivalue_line("markers", "contract: mark test as contract test")
    config.addinivalue_line("markers", "property: mark test as property test")
    config.addinivalue_line("markers", "invariant: mark test as invariant test")
    config.addinivalue_line("markers", "golden: mark test as golden dataset test")
    config.addinivalue_line("markers", "meta: mark test as meta test")
