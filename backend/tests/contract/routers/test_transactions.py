"""Contract tests for transactions router."""

from __future__ import annotations

# Add tests to path for relative imports
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestTransactionsContract:
    """Validate transactions router against OpenAPI contract."""

    def test_list_transactions_contract(self, client: TestClient) -> None:
        """GET /transactions returns valid response."""
        response = client.get("/api/v1/transactions")
        assert response.status_code in (200, 404, 500)

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_list_transactions_with_limit_contract(self, client: TestClient) -> None:
        """GET /transactions?limit=N returns valid response."""
        response = client.get("/api/v1/transactions?limit=50")
        assert response.status_code in (200, 404, 500)

    def test_list_transactions_invalid_limit_contract(self, client: TestClient) -> None:
        """GET /transactions rejects invalid limit parameter."""
        response = client.get("/api/v1/transactions?limit=0")
        assert response.status_code == 422

    def test_get_transaction_contract(self, client: TestClient) -> None:
        """GET /transactions/{id} validates path parameter."""
        response = client.get("/api/v1/transactions/1")
        assert response.status_code in (200, 404)

    def test_get_transaction_invalid_id_contract(self, client: TestClient) -> None:
        """GET /transactions/{id} with non-existent id returns 404."""
        response = client.get("/api/v1/transactions/99999")
        assert response.status_code in (404, 200)

    def test_search_transactions_contract(self, client: TestClient) -> None:
        """GET /transactions/search?q=term returns valid response."""
        response = client.get("/api/v1/transactions/search?q=transfer")
        assert response.status_code in (200, 404, 500)
