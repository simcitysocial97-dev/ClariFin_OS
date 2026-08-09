"""Database fixtures for isolated, high-performance test database management.

Architecture:
- A single session-scoped pristine schema template is created once per session.
- Each test function gets a fast file copy of that template (instead of
  re-running expensive DDL + migrations).
- Only one write connection is opened during setup.
- No secondary sqlite3 connections during fixture initialization.
- No per-test PRAGMA schema inspection.
- Safe for pytest-xdist: each worker gets its own session-scoped template.

Program K: this module uses the canonical ``src.core.db`` infrastructure
directly and no longer depends on the ``src.db.FinanceDB`` compatibility
wrapper. The ``finance_db`` fixture yields a small handle exposing the same
attributes the test suite actually consumes (``db_path``, connection access
and the context-manager protocol).
"""

from __future__ import annotations

import contextlib
import os
import shutil
import sqlite3
import types
from collections.abc import Generator
from pathlib import Path
from typing import Any, Literal

import pytest

from src.core.db.connection import get_connection
from src.core.db.schema import create_all, run_migrations, verify_schema

# ============================================================
# Canonical Test Database Handle
# ============================================================


class TestDatabase:
    """Minimal database handle backed by the canonical ``src.core.db`` layer.

    This replaces the legacy ``FinanceDB`` compatibility wrapper inside the
    test fixture layer. It intentionally preserves the behaviour the suite
    relies on:

    - ``db_path`` attribute (the only attribute tests read today)
    - lazy connection access via the canonical connection factory
    - the context-manager protocol with commit-on-success / rollback-on-error

    Schema creation is NOT performed here. The pristine session template is
    already fully initialized, so re-running DDL per test would discard the
    template optimization.
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        """Create a new connection with canonical PRAGMA settings."""
        return get_connection(self.db_path)

    def _get_conn(self) -> sqlite3.Connection:
        """Return the active connection or open a new one."""
        if self._conn is not None:
            return self._conn
        return self._connect()

    def __enter__(self) -> TestDatabase:
        self._conn = self._connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> Literal[False]:
        if self._conn:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
            self._conn.close()
            self._conn = None
        return False  # Don't suppress exceptions


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
) -> Generator[TestDatabase, None, None]:
    """Provide an isolated test database per test function.

    The database is created by copying the session-scoped pristine schema
    template, which is ~30x faster than re-running DDL and migrations.

    The global database path override is set so that all code using
    ``get_db_path()`` or ``settings.database_path`` resolves to the
    isolated test database.

    Yields:
        A :class:`TestDatabase` handle bound to an isolated temporary file.
    """
    db_path = tmp_path / f"test_finance_{os.getpid()}_{id(object())}.db"
    os.makedirs(db_path.parent, exist_ok=True)
    shutil.copy2(_pristine_db_template, db_path)

    from src.config import settings

    previous_override = getattr(settings, "_database_path_override", None)
    previous_env = os.environ.get("FINANCE_DB_PATH")
    settings._database_path_override = str(db_path)
    os.environ["FINANCE_DB_PATH"] = str(db_path)

    db = TestDatabase(str(db_path))
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
