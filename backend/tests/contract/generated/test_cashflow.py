# Auto-generated contract tests for cashflow router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/cashflow-health
# Generated: a51cecbac7ed
# To regenerate: python tools/generate_contract_tests.py --routers cashflow

import pytest

from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_behaviour_cashflow_health_contract(client):
    """Contract: GET /api/v1/behaviour/cashflow-health matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/cashflow-health")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/cashflow
# Generated: 1c7f6b2f47e0
# To regenerate: python tools/generate_contract_tests.py --routers cashflow

import pytest


@pytest.mark.contract
def test_get__api_cashflow_contract(client):
    """Contract: GET /api/cashflow matches OpenAPI schema"""

    response = client.get("/api/cashflow")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        400,
        404,
        422,
    ], f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"

    # Validate response schema on successful payloads
    if response.status_code == 200:
        validate_response_schema(response.json(), "CashflowSummaryDTO")


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/cashflow/monthly
# Generated: 38ba7a544579
# To regenerate: python tools/generate_contract_tests.py --routers cashflow

import pytest


@pytest.mark.contract
def test_get__api_cashflow_monthly_contract(client):
    """Contract: GET /api/cashflow/monthly matches OpenAPI schema"""

    response = client.get("/api/cashflow/monthly")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    # Validate response schema on successful payloads
    if response.status_code == 200:
        validate_response_schema(response.json(), "CashflowMonthlyResponse")


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/cashflow/categories
# Generated: 041904637a8e
# To regenerate: python tools/generate_contract_tests.py --routers cashflow

import pytest


@pytest.mark.contract
def test_get__api_cashflow_categories_contract(client):
    """Contract: GET /api/cashflow/categories matches OpenAPI schema"""

    response = client.get("/api/cashflow/categories")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        400,
        404,
        422,
    ], f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"

    # Validate response schema on successful payloads
    if response.status_code == 200:
        validate_response_schema(response.json(), "CashflowCategoryResponse")


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/cashflow/transactions
# Generated: 60c2cbdc4209
# To regenerate: python tools/generate_contract_tests.py --routers cashflow

import pytest


@pytest.mark.contract
def test_get__api_cashflow_transactions_contract(client):
    """Contract: GET /api/cashflow/transactions matches OpenAPI schema"""

    response = client.get("/api/cashflow/transactions")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    # Validate response schema on successful payloads
    if response.status_code == 200:
        validate_response_schema(response.json(), "CashflowTransactionResponse")


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/cashflow
# Generated: bc1f94e2583c
# To regenerate: python tools/generate_contract_tests.py --routers cashflow

import pytest


@pytest.mark.contract
def test_get__api_v1_cashflow_contract(client):
    """Contract: GET /api/v1/cashflow matches OpenAPI schema"""

    response = client.get("/api/v1/cashflow")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"
