# Auto-generated contract tests for categories router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/cashflow/categories
# Generated: 2026-07-25T16:41:44.554164
# To regenerate: python tools/generate_contract_tests.py --routers categories

import pytest
from tests.contract.schema_validators import validate_response_schema


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
# Source: GET /api/categories
# Generated: 2026-07-25T16:41:44.559970
# To regenerate: python tools/generate_contract_tests.py --routers categories

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_categories_contract(client):
    """Contract: GET /api/categories matches OpenAPI schema"""

    response = client.get("/api/categories")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
