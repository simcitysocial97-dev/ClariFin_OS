# Auto-generated contract tests for transactions router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/transactions
# Generated: 2026-07-25T16:41:44.767761
# To regenerate: python tools/generate_contract_tests.py --routers transactions

import pytest

from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_transactions_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/transactions matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/{account_id}/transactions")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"

    # Validate response schema
    if response.status_code == 200:
        validate_response_schema(response.json(), "AccountsTransactionsResponse")


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/cashflow/transactions
# Generated: 2026-07-25T16:41:44.773081
# To regenerate: python tools/generate_contract_tests.py --routers transactions

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
# Source: GET /api/transactions
# Generated: 2026-07-25T16:41:44.778601
# To regenerate: python tools/generate_contract_tests.py --routers transactions

import pytest


@pytest.mark.contract
def test_get__api_transactions_contract(client):
    """Contract: GET /api/transactions matches OpenAPI schema"""

    response = client.get("/api/transactions")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
