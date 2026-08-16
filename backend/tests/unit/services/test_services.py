"""
Service Test Suite
==================

Tests for business orchestration services.
Validates service layer behavior without database mutation.

Run: python -m pytest tests/test_services.py -v
"""

import pytest

from src.services.dashboard_service import DashboardService
from src.services.reconciliation_service import ReconciliationService

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
        """Test get_summary returns DashboardSummaryDTO with expected fields."""
        service = DashboardService(db_path=temp_db)
        result = service.get_summary()

        assert result is not None
        assert hasattr(result, "net_cash_flow_paise")
        assert hasattr(result, "total_income_paise")
        assert hasattr(result, "total_expenses_paise")
        assert hasattr(result, "savings_rate")
        assert hasattr(result, "emi_paise")
        assert hasattr(result, "emi_ratio")
        assert hasattr(result, "buffer_days")


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
# Loan Service Tests
# ============================================================


class TestLoanService:
    """Tests for LoanService."""

    def test_get_loan_not_found(self, temp_db):
        """Test get_loan raises error for non-existent loan."""
        from services.loan_service import LoanService

        service = LoanService(db_path=temp_db)
        with pytest.raises(ValueError, match="Loan .* not found"):
            service.get_loan(99999)

    def test_list_loans_returns_list(self, temp_db):
        """Test list_loans returns a list."""
        from services.loan_service import LoanService

        service = LoanService(db_path=temp_db)
        result = service.get_loans()
        assert isinstance(result, list)

    def test_create_and_get_loan(self, temp_db):
        """Test loan creation and retrieval."""
        from services.loan_service import LoanService

        # Create loan
        service = LoanService(db_path=temp_db)
        loan_id = service.create_loan(
            name="Test Loan",
            lender="Test Bank",
            loan_type="personal",
            principal_paise=100000000,  # ₹10,00,000
            outstanding_paise=100000000,
            interest_rate=8.5,
            disbursed_date="2025-01-01",
            tenure_months=120,
        )

        assert loan_id > 0

        # Get the loan
        loan = service.get_loan(loan_id)
        assert loan["name"] == "Test Loan"
        assert loan["lender"] == "Test Bank"

    def test_get_schedule_returns_schedule(self, temp_db):
        """Test get_schedule returns amortization schedule matching Phase 5 spec."""
        from services.loan_service import LoanService

        service = LoanService(db_path=temp_db)
        # First create a loan
        loan_id = service.create_loan(
            name="Test Loan",
            lender="Test Bank",
            loan_type="personal",
            principal_paise=100000000,
            outstanding_paise=100000000,
            interest_rate=8.5,
            disbursed_date="2025-01-01",
            tenure_months=120,
        )

        result = service.get_schedule(loan_id)
        assert "schedule" in result
        assert "total_interest_paise" in result
        assert len(result["schedule"]) == 120


# ============================================================
# Loan Simulation Service Tests
# ============================================================


class TestLoanSimulationService:
    """Tests for LoanSimulationService."""

    def test_simulate_prepayment(self, temp_db):
        """Test prepayment simulation returns correct structure matching Phase 5 spec."""
        from services.loan_service import LoanService
        from services.loan_simulation_service import LoanSimulationService

        # Create a loan first
        loan_service = LoanService(db_path=temp_db)
        loan_id = loan_service.create_loan(
            name="Test Loan",
            lender="Test Bank",
            loan_type="personal",
            principal_paise=100000000,
            outstanding_paise=100000000,
            interest_rate=8.5,
            disbursed_date="2025-01-01",
            tenure_months=120,
        )

        sim_service = LoanSimulationService(db_path=temp_db)
        result = sim_service.simulate_prepayment(loan_id, 10000000)  # ₹1,00,000

        assert "original_interest_paise" in result
        assert "new_interest_paise" in result
        assert "interest_saved_paise" in result
        assert "tenure_saved_months" in result
        assert result["interest_saved_paise"] > 0

    def test_simulate_foreclosure(self, temp_db):
        """Test foreclosure simulation returns correct structure matching Phase 5 spec."""
        from services.loan_service import LoanService
        from services.loan_simulation_service import LoanSimulationService

        # Create a loan first
        loan_service = LoanService(db_path=temp_db)
        loan_id = loan_service.create_loan(
            name="Test Loan",
            lender="Test Bank",
            loan_type="personal",
            principal_paise=100000000,
            outstanding_paise=100000000,
            interest_rate=8.5,
            disbursed_date="2025-01-01",
            tenure_months=120,
        )

        sim_service = LoanSimulationService(db_path=temp_db)
        result = sim_service.simulate_foreclosure(loan_id)

        # Phase 5 spec format: outstanding_paise, penalty_paise, foreclosure_amount_paise
        assert "outstanding_paise" in result
        assert "penalty_paise" in result
        assert "foreclosure_amount_paise" in result

    def test_simulate_rate_change(self, temp_db):
        """Test rate change simulation returns correct structure."""
        from services.loan_service import LoanService
        from services.loan_simulation_service import LoanSimulationService

        # Create a loan first
        loan_service = LoanService(db_path=temp_db)
        loan_id = loan_service.create_loan(
            name="Test Loan",
            lender="Test Bank",
            loan_type="personal",
            principal_paise=100000000,
            outstanding_paise=100000000,
            interest_rate=8.5,
            disbursed_date="2025-01-01",
            tenure_months=120,
        )

        sim_service = LoanSimulationService(db_path=temp_db)
        result = sim_service.simulate_rate_change(loan_id, 12, 950)

        assert "new_schedule" in result
        assert "original_rate_bps" in result
        assert "new_rate_bps" in result


# ============================================================
# Loan Analysis Service Tests
# ============================================================


class TestLoanAnalysisService:
    """Tests for LoanAnalysisService."""

    def test_analyze_surplus_allocation_no_surplus(self, temp_db):
        """Test surplus allocation with zero surplus returns all NONE actions."""
        from services.loan_analysis_service import LoanAnalysisService

        service = LoanAnalysisService(db_path=temp_db)
        result = service.analyze_surplus_allocation(0)

        assert result.surplus_paise == 0
        assert result.total_interest_saved_paise == 0
        assert all(r.action == "NONE" for r in result.recommendations)

    def test_analyze_prepayment_vs_foreclosure(self, temp_db):
        """Test prepayment vs foreclosure comparison."""
        from services.loan_analysis_service import LoanAnalysisService
        from services.loan_service import LoanService

        # Create a loan
        loan_service = LoanService(db_path=temp_db)
        loan_id = loan_service.create_loan(
            name="Test Loan",
            lender="Test Bank",
            loan_type="personal",
            principal_paise=100000000,
            outstanding_paise=100000000,
            interest_rate=8.5,
            disbursed_date="2025-01-01",
            tenure_months=120,
        )

        analysis_service = LoanAnalysisService(db_path=temp_db)
        result = analysis_service.analyze_prepayment_vs_foreclosure(loan_id, 50000000)

        assert result.loan_id == loan_id
        assert result.action in ("PREPAY", "FORECLOSE", "NONE")
        assert result.interest_saved_paise >= 0
