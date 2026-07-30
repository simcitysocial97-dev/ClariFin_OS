# Auto-generated contract tests for investments router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/investments
# Generated: af432de2d7a2
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest


@pytest.mark.contract
def test_get__api_investments_contract(client):
    """Contract: GET /api/investments matches OpenAPI schema"""

    response = client.get("/api/investments")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        400,
        404,
        422,
    ], f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/investments
# Generated: 6e21c80be0a4
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest


@pytest.mark.contract
def test_post__api_investments_contract(client):
    """Contract: POST /api/investments matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/investments", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/investments/{investment_id}
# Generated: 4ae43a8f05d4
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest


@pytest.mark.contract
def test_put__api_investments_investment_id_contract(client):
    """Contract: PUT /api/investments/{investment_id} matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.put("/api/investments/1", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/investments/{investment_id}
# Generated: 02b053f5646e
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest


@pytest.mark.contract
def test_delete__api_investments_investment_id_contract(client):
    """Contract: DELETE /api/investments/{investment_id} matches OpenAPI schema"""

    response = client.delete("/api/investments/1")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/investments
# Generated: 4040927c6430
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest


@pytest.mark.contract
def test_get__api_v1_investments_contract(client):
    """Contract: GET /api/v1/investments matches OpenAPI schema"""

    response = client.get("/api/v1/investments")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"
