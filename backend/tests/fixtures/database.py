"""Database fixtures for isolated, high-performance test database management.

Architecture:
- A single session-scoped pristine schema template is created once per session.
- Each test function gets a fast file copy of that template (instead of
  re-running expensive DDL + migrations).
- Only one write connection is opened during setup.
- No secondary sqlite3 connections during fixture initialization.
- No per-test PRAGMA schema inspection.
- Safe for pytest-xdist: each worker gets its own session-scoped template.
"""

from __future__ import annotations

import contextlib
import os
import shutil
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from src.core.db.schema import create_all, run_migrations, verify_schema
from src.db import FinanceDB

# ============================================================
# Session-Scoped Pristine Schema Template
# ============================================================


@pytest.fixture(scope="session")
def _pristine_db_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a single fully-initialized database template for the session.

    This fixture runs the expensive DDL + migrations once, then all
    function-scoped database fixtures copy from this file instead of
    re-running initialization.

    Returns:
        Path to the pristine template database file.
    """
    template_dir = tmp_path_factory.mktemp("schema_template")
    template_path = template_dir / "pristine.db"

    create_all(str(template_path))
    run_migrations(str(template_path))
    verify_schema(str(template_path))

    conn = __import__("sqlite3").connect(str(template_path))
    with contextlib.suppress(Exception):
        conn.execute("PRAGMA wal_checkpoint(FULL)")
    conn.close()

    return template_path


# ============================================================
# Function-Scoped Isolated Database Fixtures
# ============================================================


@pytest.fixture(scope="function")
def finance_db(
    tmp_path: Path, _pristine_db_template: Path
) -> Generator[FinanceDB, None, None]:
    """Provide an isolated FinanceDB per test function.

    The database is created by copying the session-scoped pristine schema
    template, which is ~30x faster than re-running DDL and migrations.

    The global database path override is set so that all code using
    ``get_db_path()`` or ``settings.database_path`` resolves to the
    isolated test database.

    Yields:
        A fully-initialized FinanceDB bound to an isolated temporary file.
    """
    db_path = tmp_path / f"test_finance_{os.getpid()}_{id(object())}.db"
    os.makedirs(db_path.parent, exist_ok=True)
    shutil.copy2(_pristine_db_template, db_path)

    from src.config import settings

    previous_override = getattr(settings, "_database_path_override", None)
    previous_env = os.environ.get("FINANCE_DB_PATH")
    settings._database_path_override = str(db_path)
    os.environ["FINANCE_DB_PATH"] = str(db_path)

    db = FinanceDB(db_path=str(db_path))
    yield db

    with contextlib.suppress(Exception):
        if hasattr(db, "_conn") and db._conn:
            db._conn.close()
            db._conn = None

    with contextlib.suppress(PermissionError):
        if db_path.exists():
            db_path.unlink()

    settings._database_path_override = previous_override
    if previous_env is None:
        os.environ.pop("FINANCE_DB_PATH", None)
    else:
        os.environ["FINANCE_DB_PATH"] = previous_env


@pytest.fixture(scope="function")
def db_path(finance_db: Any) -> str:
    """Provide the absolute database path from the isolated finance_db fixture."""
    return str(finance_db.db_path)


@pytest.fixture(scope="function")
def temp_db(tmp_path: Path, _pristine_db_template: Path) -> Generator[str, None, None]:
    """Provide a raw temporary database file path with strict automatic cleanup.

    The database schema is copied from the session-scoped pristine template.
    """
    db_path = tmp_path / f"temp_db_{os.getpid()}_{id(object())}.db"
    shutil.copy2(_pristine_db_template, db_path)

    yield str(db_path)

    with contextlib.suppress(Exception):
        if db_path.exists():
            db_path.unlink()


@pytest.fixture(scope="function")
def raw_db(tmp_path: Path) -> Generator[str, None, None]:
    """Provide an empty SQLite database file with no schema.

    Useful for tests that need to create custom tables without
    conflicting with the main application schema.
    """
    import sqlite3

    db_path = tmp_path / f"raw_db_{os.getpid()}_{id(object())}.db"
    sqlite3.connect(str(db_path)).close()

    yield str(db_path)

    with contextlib.suppress(Exception):
        if db_path.exists():
            db_path.unlink()
