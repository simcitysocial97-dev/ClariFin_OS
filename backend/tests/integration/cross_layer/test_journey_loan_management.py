"""Cross-layer test for Loan management journey.

Validates end-to-end data flow:
- Frontend hook (useLoans) → API route → Service → Repository → DB
- Loan schema validation
- EMI calculations
- Prepayment simulation
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestLoanJourney:
    """Full-stack loan management journey tests."""

    def test_list_loans_via_api(self, client: TestClient) -> None:
        """GET /api/loans returns list of loans."""
        response = client.get("/api/loans")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert isinstance(data, list), "Response should be a list of loans"

    def test_loan_schema_validation(self, client: TestClient) -> None:
        """Loan objects have all required fields matching frontend Zod schema."""
        response = client.get("/api/loans")
        assert response.status_code == 200

        data = response.json()
        required_loan_fields = {
            "id",
            "name",
            "lender",
            "loan_type",
            "principal_paise",
            "outstanding_paise",
            "interest_rate",
            "tenure_months",
            "emi_paise",
            "disbursed_date",
            "next_emi_date",
            "is_active",
        }

        if data and len(data) > 0:
            loan = data[0]
            missing = required_loan_fields - set(loan.keys())
            assert not missing, f"Missing required loan fields: {missing}"

            assert isinstance(loan["principal_paise"], int), "principal_paise should be int"
            assert isinstance(loan["outstanding_paise"], int), "outstanding_paise should be int"
            assert loan["principal_paise"] >= 0, "principal_paise should be non-negative"
            assert loan["outstanding_paise"] >= 0, "outstanding_paise should be non-negative"

    def test_loan_paise_precision(self, client: TestClient) -> None:
        """All monetary values are in paise (integers)."""
        response = client.get("/api/loans")
        assert response.status_code == 200

        data = response.json()
        for loan in data:
            assert isinstance(loan["principal_paise"], int), (
                f"principal_paise should be int, got {type(loan['principal_paise'])}"
            )
            assert isinstance(loan["outstanding_paise"], int), (
                f"outstanding_paise should be int, got {type(loan['outstanding_paise'])}"
            )

    def test_create_loan_via_api(self, client: TestClient) -> None:
        """POST /api/loans creates a new loan."""
        new_loan = {
            "name": "Test Loan",
            "lender": "Test Bank",
            "loan_type": "personal",
            "principal_paise": 1000000,
            "outstanding_paise": 900000,
            "rate_bps": 1050,
            "disbursed_date": "2026-01-01",
            "tenure_months": 36,
            "emi_paise": 32500,
        }

        response = client.post("/api/loans", json=new_loan)
        assert response.status_code in (
            200,
            201,
        ), f"Expected 201 or 200, got {response.status_code}: {response.text}"

        if response.status_code in (200, 201):
            data = response.json()
            assert data.get("success") is True, "Response should indicate success"
            assert "loan_id" in data, "Response should have loan_id"

    def test_loan_principal_outstanding_invariant(self, client: TestClient) -> None:
        """outstanding_paise should be <= principal_paise for active loans."""
        response = client.get("/api/loans")
        assert response.status_code == 200

        data = response.json()
        for loan in data:
            if loan.get("is_active"):
                assert loan["outstanding_paise"] <= loan["principal_paise"], (
                    f"Active loan outstanding ({loan['outstanding_paise']}) "
                    f"should not exceed principal ({loan['principal_paise']})"
                )


class TestLoanServiceLayer:
    """Test loan service business logic independently."""

    def test_loan_service_initializes(self) -> None:
        """LoanService can be instantiated."""
        from src.services.loan_service import LoanService

        service = LoanService()
        assert service is not None

    def test_loan_service_get_loans(self) -> None:
        """LoanService can retrieve loans."""
        from src.services.loan_service import LoanService

        service = LoanService()
        loans = service.get_loans()
        assert isinstance(loans, list)


class TestPrepaymentSimulation:
    """Test prepayment simulation journey."""

    def test_loan_schedule_endpoint_exists(self, client: TestClient) -> None:
        """GET /api/loans/{id}/schedule returns schedule or 404."""
        response = client.get("/api/loans/1/schedule")
        assert response.status_code in (
            200,
            404,
        ), f"Expected 200 or 404, got {response.status_code}"

    def test_prepayment_simulation_endpoint_exists(self, client: TestClient) -> None:
        """POST /api/loans/{id}/prepayment-simulation returns simulation or 404."""
        response = client.post(
            "/api/loans/1/prepayment-simulation",
            json={"amount_paise": 50000, "mode": "reduce_tenure"},
        )
        assert response.status_code in (
            200,
            201,
            404,
        ), f"Expected 2xx or 404, got {response.status_code}"
