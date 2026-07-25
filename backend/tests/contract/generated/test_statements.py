# Auto-generated contract tests for statements router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/statements
# Generated: 2026-07-25T16:41:44.749275
# To regenerate: python tools/generate_contract_tests.py --routers statements

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_statements_contract(client):
    """Contract: GET /api/statements matches OpenAPI schema"""

    response = client.get("/api/statements")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/statements/{statement_id}/validate
# Generated: 2026-07-25T16:41:44.753493
# To regenerate: python tools/generate_contract_tests.py --routers statements

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_statements_statement_id_validate_contract(client):
    """Contract: GET /api/statements/{statement_id}/validate matches OpenAPI schema"""

    response = client.get("/api/statements/{statement_id}/validate")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/statements
# Generated: 2026-07-25T16:41:44.757282
# To regenerate: python tools/generate_contract_tests.py --routers statements

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_statements_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/statements matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards/{card_id}/statements")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards/{card_id}/statements
# Generated: 2026-07-25T16:41:44.761224
# To regenerate: python tools/generate_contract_tests.py --routers statements

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_v1_credit_cards_card_id_statements_contract(client):
    """Contract: POST /api/v1/credit-cards/{card_id}/statements matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/StatementGenerateRequest"}
            }
        },
    }
    response = client.post(
        "/api/v1/credit-cards/{card_id}/statements", json=request_body
    )

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
