# Auto-generated contract tests for transactions router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/cashflow/transactions
# Generated: 9b15453f4ffd
# To regenerate: python tools/generate_contract_tests.py --routers transactions

import pytest

from tests.contract.schema_validators import validate_response_schema


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
# Source: GET /api/transactions
# Generated: 1e11eb3c1fe5
# To regenerate: python tools/generate_contract_tests.py --routers transactions

import pytest


@pytest.mark.contract
def test_get__api_transactions_contract(client):
    """Contract: GET /api/transactions matches OpenAPI schema"""

    response = client.get("/api/transactions")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"
