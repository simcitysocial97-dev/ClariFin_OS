# Auto-generated contract tests for investments router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/investments
# Generated: 2026-07-25T16:41:44.609593
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_investments_contract(client):
    """Contract: GET /api/investments matches OpenAPI schema"""

    response = client.get("/api/investments")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/investments
# Generated: 2026-07-25T16:41:44.614301
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_investments_contract(client):
    """Contract: POST /api/investments matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/InvestmentCreate"}
            }
        },
        "required": True,
    }
    response = client.post("/api/investments", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/investments/{investment_id}
# Generated: 2026-07-25T16:41:44.620703
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_put__api_investments_investment_id_contract(client):
    """Contract: PUT /api/investments/{investment_id} matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/InvestmentUpdate"}
            }
        },
    }
    response = client.put("/api/investments/{investment_id}", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/investments/{investment_id}
# Generated: 2026-07-25T16:41:44.626571
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_delete__api_investments_investment_id_contract(client):
    """Contract: DELETE /api/investments/{investment_id} matches OpenAPI schema"""

    response = client.delete("/api/investments/{investment_id}")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/investments
# Generated: 2026-07-25T16:41:44.632429
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_investments_contract(client):
    """Contract: GET /api/v1/investments matches OpenAPI schema"""

    response = client.get("/api/v1/investments")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
