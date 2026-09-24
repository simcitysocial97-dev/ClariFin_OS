"""Tests for the app-wide request logging middleware (M07)."""

import logging

import pytest
from fastapi.testclient import TestClient


def test_transactions_endpoint_logs_request(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """A previously-silent endpoint emits one middleware log line per request."""
    with caplog.at_level(logging.INFO, logger="clarifin"):
        response = client.get("/api/transactions")

    assert response.status_code == 200
    matching = [
        r
        for r in caplog.records
        if "GET /api/transactions - 200" in r.getMessage()
        and "duration_ms=" in r.getMessage()
        and "correlation_id=" in r.getMessage()
    ]
    assert (
        matching
    ), "expected middleware log line for GET /api/transactions, got: " + "; ".join(
        r.getMessage() for r in caplog.records[-5:]
    )


def test_correlation_id_generated_and_returned(client: TestClient) -> None:
    """Middleware generates X-Correlation-Id when absent and returns it."""
    response = client.get("/api/transactions")
    assert "X-Correlation-Id" in response.headers
    assert response.headers["X-Correlation-Id"]


def test_correlation_id_passthrough(client: TestClient) -> None:
    """Client-supplied X-Correlation-Id is echoed back unchanged."""
    response = client.get(
        "/api/transactions", headers={"X-Correlation-Id": "m07-test-id"}
    )
    assert response.headers["X-Correlation-Id"] == "m07-test-id"


def test_status_code_reflected_in_log(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """A 404 response is still logged with its status code."""
    with caplog.at_level(logging.INFO, logger="clarifin"):
        response = client.get("/api/does-not-exist-m07")

    assert response.status_code == 404
    assert any(
        "GET /api/does-not-exist-m07 - 404" in r.getMessage() for r in caplog.records
    )
