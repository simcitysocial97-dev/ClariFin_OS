# Auto-generated contract tests for cashflow router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/cashflow-health
# Generated: 2026-07-25T16:41:44.524633
# To regenerate: python tools/generate_contract_tests.py --routers cashflow

import pytest

from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_behaviour_cashflow_health_contract(client):
    """Contract: GET /api/v1/behaviour/cashflow-health matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/cashflow-health")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/cashflow
# Generated: 2026-07-25T16:41:44.530174
# To regenerate: python tools/generate_contract_tests.py --routers cashflow

import pytest


@pytest.mark.contract
def test_get__api_cashflow_contract(client):
    """Contract: GET /api/cashflow matches OpenAPI schema"""

    response = client.get("/api/cashflow")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"

    # Validate response schema
    if response.status_code == 200:
        validate_response_schema(response.json(), "CashflowSummaryDTO")


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/cashflow/monthly
# Generated: 2026-07-25T16:41:44.536181
# To regenerate: python tools/generate_contract_tests.py --routers cashflow

import pytest


@pytest.mark.contract
def test_get__api_cashflow_monthly_contract(client):
    """Contract: GET /api/cashflow/monthly matches OpenAPI schema"""

    response = client.get("/api/cashflow/monthly")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"

    # Validate response schema
    if response.status_code == 200:
        validate_response_schema(response.json(), "CashflowMonthlyResponse")


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/cashflow/categories
# Generated: 2026-07-25T16:41:44.539958
# To regenerate: python tools/generate_contract_tests.py --routers cashflow

import pytest


@pytest.mark.contract
def test_get__api_cashflow_categories_contract(client):
    """Contract: GET /api/cashflow/categories matches OpenAPI schema"""

    response = client.get("/api/cashflow/categories")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"

    # Validate response schema
    if response.status_code == 200:
        validate_response_schema(response.json(), "CashflowCategoryResponse")


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/cashflow/transactions
# Generated: 2026-07-25T16:41:44.544253
# To regenerate: python tools/generate_contract_tests.py --routers cashflow

import pytest


@pytest.mark.contract
def test_get__api_cashflow_transactions_contract(client):
    """Contract: GET /api/cashflow/transactions matches OpenAPI schema"""

    response = client.get("/api/cashflow/transactions")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"

    # Validate response schema
    if response.status_code == 200:
        validate_response_schema(response.json(), "CashflowTransactionResponse")


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/cashflow
# Generated: 2026-07-25T16:41:44.547666
# To regenerate: python tools/generate_contract_tests.py --routers cashflow

import pytest


@pytest.mark.contract
def test_get__api_v1_cashflow_contract(client):
    """Contract: GET /api/v1/cashflow matches OpenAPI schema"""

    response = client.get("/api/v1/cashflow")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
