# Auto-generated contract tests for loans router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/loans
# Generated: 2026-07-25T16:41:44.638969
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_get__api_loans_contract(client):
    """Contract: GET /api/loans matches OpenAPI schema"""

    response = client.get("/api/loans")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/loans
# Generated: 2026-07-25T16:41:44.645384
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_post__api_loans_contract(client):
    """Contract: POST /api/loans matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/LoanCreateRequest"}
            }
        },
        "required": True,
    }
    response = client.post("/api/loans", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/loans/{loan_id}
# Generated: 2026-07-25T16:41:44.651389
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_get__api_loans_loan_id_contract(client):
    """Contract: GET /api/loans/{loan_id} matches OpenAPI schema"""

    response = client.get("/api/loans/{loan_id}")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/loans/{loan_id}
# Generated: 2026-07-25T16:41:44.655410
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_put__api_loans_loan_id_contract(client):
    """Contract: PUT /api/loans/{loan_id} matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/LoanUpdateRequest"}
            }
        },
    }
    response = client.put("/api/loans/{loan_id}", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/loans/{loan_id}
# Generated: 2026-07-25T16:41:44.659475
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_delete__api_loans_loan_id_contract(client):
    """Contract: DELETE /api/loans/{loan_id} matches OpenAPI schema"""

    response = client.delete("/api/loans/{loan_id}")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/loans/{loan_id}/schedule
# Generated: 2026-07-25T16:41:44.663316
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_get__api_loans_loan_id_schedule_contract(client):
    """Contract: GET /api/loans/{loan_id}/schedule matches OpenAPI schema"""

    response = client.get("/api/loans/{loan_id}/schedule")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/loans/{loan_id}/prepayment-simulation
# Generated: 2026-07-25T16:41:44.667556
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_post__api_loans_loan_id_prepayment_simulation_contract(client):
    """Contract: POST /api/loans/{loan_id}/prepayment-simulation matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/PrepaymentSimulationRequest"}
            }
        },
    }
    response = client.post(
        "/api/loans/{loan_id}/prepayment-simulation", json=request_body
    )

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/loans/{loan_id}/foreclosure-simulation
# Generated: 2026-07-25T16:41:44.671912
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_post__api_loans_loan_id_foreclosure_simulation_contract(client):
    """Contract: POST /api/loans/{loan_id}/foreclosure-simulation matches OpenAPI schema"""

    response = client.post("/api/loans/{loan_id}/foreclosure-simulation")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/loans/{loan_id}/rate-change-simulation
# Generated: 2026-07-25T16:41:44.676966
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_post__api_loans_loan_id_rate_change_simulation_contract(client):
    """Contract: POST /api/loans/{loan_id}/rate-change-simulation matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/RateChangeSimulationRequest"}
            }
        },
    }
    response = client.post(
        "/api/loans/{loan_id}/rate-change-simulation", json=request_body
    )

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/loans/{loan_id}/payments
# Generated: 2026-07-25T16:41:44.681978
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_post__api_loans_loan_id_payments_contract(client):
    """Contract: POST /api/loans/{loan_id}/payments matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/PaymentRequest"}
            }
        },
    }
    response = client.post("/api/loans/{loan_id}/payments", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/loans/analysis/priority
# Generated: 2026-07-25T16:41:44.686542
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_get__api_loans_analysis_priority_contract(client):
    """Contract: GET /api/loans/analysis/priority matches OpenAPI schema"""

    response = client.get("/api/loans/analysis/priority")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/loans/{loan_id}/analysis/prepayment-vs-foreclosure
# Generated: 2026-07-25T16:41:44.690258
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_post__api_loans_loan_id_analysis_prepayment_vs_foreclosure_contract(client):
    """Contract: POST /api/loans/{loan_id}/analysis/prepayment-vs-foreclosure matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/PaymentRequest"}
            }
        },
    }
    response = client.post(
        "/api/loans/{loan_id}/analysis/prepayment-vs-foreclosure", json=request_body
    )

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/loans/analysis/surplus-allocation
# Generated: 2026-07-25T16:41:44.693762
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_post__api_loans_analysis_surplus_allocation_contract(client):
    """Contract: POST /api/loans/analysis/surplus-allocation matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/PaymentRequest"}
            }
        },
        "required": True,
    }
    response = client.post("/api/loans/analysis/surplus-allocation", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/loans
# Generated: 2026-07-25T16:41:44.698298
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_get__api_v1_loans_contract(client):
    """Contract: GET /api/v1/loans matches OpenAPI schema"""

    response = client.get("/api/v1/loans")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
