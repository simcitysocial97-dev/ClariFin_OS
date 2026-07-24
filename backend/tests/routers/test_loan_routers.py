"""
Loan API Contract Test Suite
=============================

Tests for loan API contract compliance.
Tests service layer directly to verify API contracts.

Run: python -m pytest tests/test_loan_routers.py -v
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import FinanceDB

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
# Loan CRUD Contract Tests
# ============================================================

class TestLoanContract:
    """Tests for loan API contract compliance."""

    def test_create_loan_request_validation(self, temp_db):
        """Test LoanCreateRequest validates correctly."""
        from models.loan import LoanCreateRequest

        # Valid request
        valid = LoanCreateRequest(
            name="Test Loan",
            lender="Test Bank",
            loan_type="personal",
            principal_paise=100000000,
            rate_bps=850,
            tenure_months=120,
            disbursed_date="2025-01-01",
        )
        assert valid.rate_bps == 850

        # Invalid principal
        with pytest.raises(ValidationError):
            LoanCreateRequest(
                name="Test Loan",
                lender="Test Bank",
                loan_type="personal",
                principal_paise=0,  # Invalid
                rate_bps=850,
                tenure_months=120,
                disbursed_date="2025-01-01",
            )

    def test_loan_response_format(self, temp_db):
        """Test LoanResponse returns proper format with rate_bps."""
        from models.loan import LoanResponse
        from services.loan_service import LoanService

        service = LoanService(db_path=temp_db)
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

        loan = service.get_loan(loan_id)
        response = LoanResponse.from_loan_dict(loan)

        assert response.id == loan_id
        assert response.rate_bps == 850  # 8.5% * 100
        assert response.tenure_months == 120

    def test_schedule_response_format(self, temp_db):
        """Test ScheduleResponse returns proper format."""
        from models.loan import ScheduleResponse
        from services.loan_service import LoanService

        service = LoanService(db_path=temp_db)
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

        schedule_data = service.get_schedule(loan_id)
        response = ScheduleResponse.from_schedule_data(
            loan_id=loan_id,
            emi_paise=schedule_data["emi_paise"],
            total_interest_paise=schedule_data["total_interest_paise"],
            schedule=schedule_data["schedule"],
        )

        assert response.loan_id == loan_id
        assert response.emi_paise == schedule_data["emi_paise"]
        assert response.total_interest_paise == schedule_data["total_interest_paise"]
        assert len(response.schedule) == 120
        # Check schedule row format
        assert response.schedule[0].month == 1
        assert response.schedule[-1].balance_paise == 0  # Final balance zero


# ============================================================
# Prepayment Simulation Tests
# ============================================================

class TestPrepaymentSimulation:
    """Tests for prepayment simulation API contract."""

    def test_prepayment_simulation_response_format(self, temp_db):
        """Test PrepaymentSimulationResponse format."""
        from models.loan_simulation import PrepaymentSimulationResponse
        from services.loan_service import LoanService
        from services.loan_simulation_service import LoanSimulationService

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
        result = sim_service.simulate_prepayment(loan_id, 10000000)

        response = PrepaymentSimulationResponse(
            original_interest_paise=result["original_interest_paise"],
            new_interest_paise=result["new_interest_paise"],
            interest_saved_paise=result["interest_saved_paise"],
            tenure_saved_months=result["tenure_saved_months"],
        )

        assert response.interest_saved_paise > 0
        assert response.tenure_saved_months > 0
        assert response.original_interest_paise > response.new_interest_paise

    def test_prepayment_simulation_does_not_mutate_db(self, temp_db):
        """Verify simulation does not mutate database."""
        from services.loan_service import LoanService
        from services.loan_simulation_service import LoanSimulationService

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

        # Store original outstanding
        original_loan = loan_service.get_loan(loan_id)
        original_outstanding = original_loan["outstanding_paise"]

        # Run simulation
        sim_service = LoanSimulationService(db_path=temp_db)
        sim_service.simulate_prepayment(loan_id, 50000000)

        # Verify outstanding unchanged
        after_loan = loan_service.get_loan(loan_id)
        assert after_loan["outstanding_paise"] == original_outstanding


# ============================================================
# Foreclosure Simulation Tests
# ============================================================

class TestForeclosureSimulation:
    """Tests for foreclosure simulation API contract."""

    def test_foreclosure_response_format(self, temp_db):
        """Test ForeclosureSimulationResponse format."""
        from models.loan_simulation import ForeclosureSimulationResponse
        from services.loan_service import LoanService
        from services.loan_simulation_service import LoanSimulationService

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

        response = ForeclosureSimulationResponse(
            outstanding_paise=result["outstanding_paise"],
            penalty_paise=result["penalty_paise"],
            foreclosure_amount_paise=result["foreclosure_amount_paise"],
        )

        assert response.outstanding_paise == 100000000
        assert response.foreclosure_amount_paise > response.outstanding_paise


# ============================================================
# Rate Change Simulation Tests
# ============================================================

class TestRateChangeSimulation:
    """Tests for rate change simulation API contract."""

    def test_rate_change_response_format(self, temp_db):
        """Test RateChangeSimulationResponse format."""
        from services.loan_service import LoanService
        from services.loan_simulation_service import LoanSimulationService

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

        assert "original_rate_bps" in result
        assert "new_rate_bps" in result
        assert "new_schedule" in result
        assert result["original_rate_bps"] == 850
        assert result["new_rate_bps"] == 950


# ============================================================
# Payment Tests
# ============================================================

class TestPaymentAPI:
    """Tests for payment API contract."""

    def test_payment_request_validation(self, temp_db):
        """Test PaymentRequest validates correctly."""
        from models.loan_simulation import PaymentRequest

        valid = PaymentRequest(
            amount_paise=1000000,
            payment_date="2025-02-01",
        )
        assert valid.amount_paise == 1000000

        # Invalid amount
        with pytest.raises(ValidationError):
            PaymentRequest(
                amount_paise=0,  # Must be > 0
                payment_date="2025-02-01",
            )


# ============================================================
# Full Prepayment Closure Tests
# ============================================================

class TestFullPrepaymentClosure:
    """Tests for full prepayment scenarios."""

    def test_full_prepayment_closes_loan(self, temp_db):
        """Test full prepayment closes the loan."""
        from services.loan_service import LoanService
        from services.loan_simulation_service import LoanSimulationService

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
        result = sim_service.simulate_prepayment(loan_id, 100000000)  # Full outstanding

        # Full prepayment should close immediately
        assert result["tenure_saved_months"] == 120  # All months saved
        assert result["interest_saved_paise"] > 0


# ============================================================
# Schedule Invariant Validation Tests
# ============================================================

class TestScheduleInvariants:
    """Tests for schedule invariant validation."""

    def test_schedule_balance_never_negative(self, temp_db):
        """Verify no negative balances in schedule."""
        from services.loan_service import LoanService

        service = LoanService(db_path=temp_db)
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

        schedule_data = service.get_schedule(loan_id)
        for row in schedule_data["schedule"]:
            assert row["balance_paise"] >= 0, "Balance should never be negative"

    def test_schedule_final_balance_zero(self, temp_db):
        """Verify final balance is zero."""
        from services.loan_service import LoanService

        service = LoanService(db_path=temp_db)
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

        schedule_data = service.get_schedule(loan_id)
        assert schedule_data["schedule"][-1]["balance_paise"] == 0
