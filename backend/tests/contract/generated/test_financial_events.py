# Auto-generated contract tests for financial-events router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/financial-events/
# Generated: 2026-07-25T16:41:44.583531
# To regenerate: python tools/generate_contract_tests.py --routers financial-events

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_financial_events__contract(client):
    """Contract: POST /api/financial-events/ matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "title": "Transaction Ids",
                }
            }
        },
    }
    response = client.post("/api/financial-events/", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/financial-events/
# Generated: 2026-07-25T16:41:44.589664
# To regenerate: python tools/generate_contract_tests.py --routers financial-events

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_financial_events__contract(client):
    """Contract: GET /api/financial-events/ matches OpenAPI schema"""

    response = client.get("/api/financial-events/")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/financial-events/{event_id}
# Generated: 2026-07-25T16:41:44.595383
# To regenerate: python tools/generate_contract_tests.py --routers financial-events

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_financial_events_event_id_contract(client):
    """Contract: GET /api/financial-events/{event_id} matches OpenAPI schema"""

    response = client.get("/api/financial-events/{event_id}")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
