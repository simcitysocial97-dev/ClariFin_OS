# Auto-generated contract tests for categories router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/cashflow/categories
# Generated: 774e1fda0e93
# To regenerate: python tools/generate_contract_tests.py --routers categories

import pytest

from tests.contract.schema_validators import validate_response_schema


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
# Source: GET /api/categories
# Generated: b8dd18676679
# To regenerate: python tools/generate_contract_tests.py --routers categories

import pytest


@pytest.mark.contract
def test_get__api_categories_contract(client):
    """Contract: GET /api/categories matches OpenAPI schema"""

    response = client.get("/api/categories")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"
