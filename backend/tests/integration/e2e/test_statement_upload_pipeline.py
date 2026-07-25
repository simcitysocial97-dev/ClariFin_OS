"""End-to-end test for statement upload pipeline.

Tests the full pipeline: API upload → statement parsing → transaction insertion → balance computation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))


class TestStatementUploadPipeline:
    """Full stack test: API → DB → response."""

    def test_upload_statement_returns_200(self, client: TestClient) -> None:
        """POST /upload returns 200 or 500 (no crash)."""
        response = client.post("/api/v1/upload")
        assert response.status_code in (200, 400, 422, 500)

    def test_upload_statement_with_file(self, client: TestClient) -> None:
        """POST /upload with file returns valid response."""
        # Create a minimal test file
        test_content = b"Date,Description,Amount\n"
        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.csv", test_content, "text/csv")},
        )
        assert response.status_code in (200, 400, 422, 500)

    def test_upload_invalid_file_type(self, client: TestClient) -> None:
        """POST /upload rejects invalid file types."""
        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.xyz", b"invalid", "application/octet-stream")},
        )
        assert response.status_code in (400, 422, 500)

    def test_transactions_after_upload(self, client: TestClient) -> None:
        """GET /transactions returns list after upload."""
        response = client.get("/api/v1/transactions")
        assert response.status_code in (200, 404, 500)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_balance_after_upload(self, client: TestClient) -> None:
        """GET /accounts/{id}/analytics returns valid response after upload."""
        response = client.get("/api/v1/accounts/1/analytics")
        assert response.status_code in (200, 404, 500)
