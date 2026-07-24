"""
Router/API Test Suite
======================

Tests for FastAPI router endpoints.
Uses TestClient for integration testing.

Run: python -m pytest tests/test_routers.py -v
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import FinanceDB

# ============================================================
# Test Client Fixture with proper isolation
# ============================================================

@pytest.fixture
def isolated_app():
    """Create a TestClient with an isolated temporary database."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Create fresh database
    FinanceDB(db_path=db_path)

    # Create fresh app for each test
    from fastapi import FastAPI

    from src.errors import register_error_handlers
    from src.health import register_health_routes
    from src.routers.reconciliation import router as reconciliation_router
    from src.routers.transactions import router as transactions_router

    test_app = FastAPI(title="Test API")
    register_error_handlers(test_app)
    register_health_routes(test_app)
    test_app.include_router(transactions_router)
    test_app.include_router(reconciliation_router)

    yield TestClient(test_app), db_path

    os.unlink(db_path)


# ============================================================
# Transactions Router Tests
# ============================================================

class TestTransactionsRouter:
    """Tests for /api/transactions endpoints."""

    def test_get_transactions_returns_list(self, isolated_app):
        """Test GET /api/transactions returns a list."""
        client, _ = isolated_app
        response = client.get("/api/transactions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_transactions_with_invalid_limit(self, isolated_app):
        """Test GET /api/transactions rejects invalid limit."""
        client, _ = isolated_app
        response = client.get("/api/transactions?limit=0")
        assert response.status_code == 422  # Validation error

    def test_get_overview_returns_success(self, isolated_app):
        """Test GET /api/overview returns valid response structure."""
        client, _ = isolated_app
        response = client.get("/api/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_spend" in data or "spending_this_month" in data

    def test_get_analytics_returns_success(self, isolated_app):
        """Test GET /api/analytics returns valid response structure."""
        client, _ = isolated_app
        response = client.get("/api/analytics")
        assert response.status_code == 200

    def test_get_categories_returns_success(self, isolated_app):
        """Test GET /api/categories returns valid response structure."""
        client, _ = isolated_app
        response = client.get("/api/categories")
        assert response.status_code == 200


# ============================================================
# Reconciliation Router Tests
# ============================================================

class TestReconciliationRouter:
    """Tests for /api/reconciliations endpoints."""

    def test_scan_reconciliations_returns_success(self, isolated_app):
        """Test GET /api/reconciliations/scan returns valid response."""
        client, _ = isolated_app
        response = client.get("/api/reconciliations/scan")
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert "count" in data

    def test_batch_insert_reconciliations_returns_success(self, isolated_app):
        """Test POST /api/reconciliations/batch-insert returns valid response."""
        client, _ = isolated_app
        response = client.post("/api/reconciliations/batch-insert")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_create_reconciliation_missing_params(self, isolated_app):
        """Test POST /api/reconciliations/create with missing params returns error."""
        client, _ = isolated_app
        response = client.post("/api/reconciliations/create")
        assert response.status_code == 422  # Validation error


# ============================================================
# Health Router Tests
# ============================================================

class TestHealthRouter:
    """Tests for /api/health endpoints."""

    def test_health_check_endpoint(self, isolated_app):
        """Test GET /health returns healthy status."""
        client, _ = isolated_app
        response = client.get("/health")
        assert response.status_code == 200
