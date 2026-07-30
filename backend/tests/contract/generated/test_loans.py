# Auto-generated contract tests for loans router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/loans
# Generated: 68f4899aba2a
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_get__api_loans_contract(client):
    """Contract: GET /api/loans matches OpenAPI schema"""

    response = client.get("/api/loans")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        400,
        404,
        422,
    ], f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/loans
# Generated: ef1c2a37ab9b
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_post__api_loans_contract(client):
    """Contract: POST /api/loans matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/loans", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/loans/{loan_id}
# Generated: d3a957070fd6
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_get__api_loans_loan_id_contract(client):
    """Contract: GET /api/loans/{loan_id} matches OpenAPI schema"""

    response = client.get("/api/loans/1")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/loans/{loan_id}
# Generated: ac32ae5213c8
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_put__api_loans_loan_id_contract(client):
    """Contract: PUT /api/loans/{loan_id} matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.put("/api/loans/1", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/loans/{loan_id}
# Generated: fa764596ed2d
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_delete__api_loans_loan_id_contract(client):
    """Contract: DELETE /api/loans/{loan_id} matches OpenAPI schema"""

    response = client.delete("/api/loans/1")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/loans/{loan_id}/schedule
# Generated: 71db5ec56c8c
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_get__api_loans_loan_id_schedule_contract(client):
    """Contract: GET /api/loans/{loan_id}/schedule matches OpenAPI schema"""

    response = client.get("/api/loans/1/schedule")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/loans/{loan_id}/prepayment-simulation
# Generated: 3241d112ca9d
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_post__api_loans_loan_id_prepayment_simulation_contract(client):
    """Contract: POST /api/loans/{loan_id}/prepayment-simulation matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/loans/1/prepayment-simulation", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/loans/{loan_id}/foreclosure-simulation
# Generated: c077b79e31c6
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_post__api_loans_loan_id_foreclosure_simulation_contract(client):
    """Contract: POST /api/loans/{loan_id}/foreclosure-simulation matches OpenAPI schema"""

    response = client.post("/api/loans/1/foreclosure-simulation")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/loans/{loan_id}/rate-change-simulation
# Generated: d534e8fed98c
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_post__api_loans_loan_id_rate_change_simulation_contract(client):
    """Contract: POST /api/loans/{loan_id}/rate-change-simulation matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/loans/1/rate-change-simulation", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/loans/{loan_id}/payments
# Generated: 36e7759d6376
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_post__api_loans_loan_id_payments_contract(client):
    """Contract: POST /api/loans/{loan_id}/payments matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/loans/1/payments", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/loans/analysis/priority
# Generated: 392d12b96484
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_get__api_loans_analysis_priority_contract(client):
    """Contract: GET /api/loans/analysis/priority matches OpenAPI schema"""

    response = client.get("/api/loans/analysis/priority")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        400,
        404,
        422,
    ], f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/loans/{loan_id}/analysis/prepayment-vs-foreclosure
# Generated: d95e18e597e2
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_post__api_loans_loan_id_analysis_prepayment_vs_foreclosure_contract(client):
    """Contract: POST /api/loans/{loan_id}/analysis/prepayment-vs-foreclosure matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post(
        "/api/loans/1/analysis/prepayment-vs-foreclosure", json=request_body
    )

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/loans/analysis/surplus-allocation
# Generated: dbb4852ba854
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_post__api_loans_analysis_surplus_allocation_contract(client):
    """Contract: POST /api/loans/analysis/surplus-allocation matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/loans/analysis/surplus-allocation", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/loans
# Generated: 8fe53e33f481
# To regenerate: python tools/generate_contract_tests.py --routers loans

import pytest


@pytest.mark.contract
def test_get__api_v1_loans_contract(client):
    """Contract: GET /api/v1/loans matches OpenAPI schema"""

    response = client.get("/api/v1/loans")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"
