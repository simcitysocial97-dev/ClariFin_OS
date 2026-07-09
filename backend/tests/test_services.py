"""
Service Test Suite
==================

Tests for business orchestration services.
Validates service layer behavior without database mutation.

Run: python -m pytest tests/test_services.py -v
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import FinanceDB
from services.behavior_service import BehaviorService
from services.dashboard_service import DashboardService
from services.reconciliation_service import ReconciliationService

# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    FinanceDB(db_path=db_path)

    yield db_path

    os.unlink(db_path)


# ============================================================
# Dashboard Service Tests
# ============================================================

class TestDashboardService:
    """Tests for DashboardService."""

    def test_service_initialization(self, temp_db):
        """Test DashboardService can be initialized with db_path."""
        service = DashboardService(db_path=temp_db)
        assert service.db_path == temp_db

    def test_service_default_db_path(self):
        """Test DashboardService uses default DB_PATH when not provided."""
        service = DashboardService()
        assert service.db_path is not None

    def test_get_summary_returns_valid_structure(self, temp_db):
        """Test get_summary returns DashboardSummary with expected fields."""
        service = DashboardService(db_path=temp_db)
        result = service.get_summary()

        # Should return a DashboardSummary object
        assert result is not None
        assert hasattr(result, "behavior_score")
        assert hasattr(result, "spending_this_month")


# ============================================================
# Reconciliation Service Tests
# ============================================================

class TestReconciliationService:
    """Tests for ReconciliationService."""

    def test_service_initialization(self, temp_db):
        """Test ReconciliationService can be initialized with db_path."""
        service = ReconciliationService(db_path=temp_db)
        assert service.db_path == temp_db

    def test_scan_potential_matches_returns_list(self, temp_db):
        """Test scan_potential_matches returns a list."""
        service = ReconciliationService(db_path=temp_db)
        result = service.scan_potential_matches()

        assert isinstance(result, list)
        # Empty database should return empty list
        assert len(result) == 0

    def test_scan_with_data_returns_matches(self, temp_db):
        """Test scan_potential_matches finds matches with test data."""
        import sqlite3

        from repositories.statement_repository import StatementRepository

        # Create test data
        stmt_repo = StatementRepository(temp_db)
        stmt_repo.insert_statement("AccountA", "stmt_a.pdf")
        stmt_repo.insert_statement("AccountB", "stmt_b.pdf")

        conn = sqlite3.connect(temp_db)
        conn.execute("""
            INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id)
            VALUES
                (1, '01/01/2025', '2025-01-01', 'Transfer out', 100000, 'debit', 'AccountA'),
                (2, '01/01/2025', '2025-01-01', 'Transfer in', 100000, 'credit', 'AccountB')
        """)
        conn.commit()
        conn.close()

        # Run scan
        service = ReconciliationService(db_path=temp_db)
        result = service.scan_potential_matches()

        # Should find the exact match
        assert len(result) >= 1


# ============================================================
# Behavior Service Tests
# ============================================================

class TestBehaviorService:
    """Tests for BehaviorService."""

    def test_service_initialization(self, temp_db):
        """Test BehaviorService can be initialized with db_path."""
        service = BehaviorService(db_path=temp_db)
        assert service.db_path == temp_db

    def test_compute_profile_returns_dict(self, temp_db):
        """Test compute_profile returns proper structure."""
        service = BehaviorService(db_path=temp_db)
        profile = service.compute_profile()

        assert isinstance(profile, dict)
        assert "financial_health_score" in profile or "behavioral_indices" in profile

    def test_health_score_in_valid_range(self, temp_db):
        """Test health score is in valid range after profile computation."""
        service = BehaviorService(db_path=temp_db)
        profile = service.compute_profile()

        score = profile.get("financial_health_score", 50)
        assert 0 <= score <= 100

    def test_generate_insights_returns_dict(self, temp_db):
        """Test generate_insights returns proper structure."""
        service = BehaviorService(db_path=temp_db)
        result = service.generate_insights()

        assert isinstance(result, dict)
        assert "insights" in result
        assert "nudges" in result

    def test_cached_profile_returns_dict(self, temp_db):
        """Test get_cached_profile returns a dict structure."""
        service = BehaviorService(db_path=temp_db)
        profile = service.get_cached_profile()

        # Should return None or a valid profile dict
        if profile is not None:
            assert isinstance(profile, dict)
            assert "financial_health_score" in profile
