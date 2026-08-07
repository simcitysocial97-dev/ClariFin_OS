"""API test client fixtures.

Provides FastAPI TestClient instances bound to isolated, seeded databases.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def test_client(seeded_db: Any) -> Generator[TestClient, None, None]:
    """Create a FastAPI TestClient bound to an isolated seeded database.

    Args:
        seeded_db: The isolated, pre-seeded FinanceDB to bind the client to.

    Yields:
        A TestClient instance with raise_server_exceptions enabled.
    """
    from src.api import app

    app.state.db_path = str(seeded_db.db_path)

    with TestClient(app, raise_server_exceptions=True) as client:
        yield client


@pytest.fixture(scope="function")
def client(test_client: TestClient) -> TestClient:
    """Alias for test_client for contract, API, and e2e test suites."""
    return test_client
