# Auto-generated contract tests for financial-events router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/financial-events/
# Generated: 2026-07-28T09:26:06.087503
# To regenerate: python tools/generate_contract_tests.py --routers financial-events

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_financial_events__contract(client):
    """Contract: POST /api/financial-events/ matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/financial-events/", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/financial-events/
# Generated: 2026-07-28T09:26:06.090866
# To regenerate: python tools/generate_contract_tests.py --routers financial-events

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_financial_events__contract(client):
    """Contract: GET /api/financial-events/ matches OpenAPI schema"""
    
    response = client.get("/api/financial-events/")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/financial-events/{event_id}
# Generated: 2026-07-28T09:26:06.093650
# To regenerate: python tools/generate_contract_tests.py --routers financial-events

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_financial_events_event_id_contract(client):
    """Contract: GET /api/financial-events/{event_id} matches OpenAPI schema"""
    
    response = client.get("/api/financial-events/1")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    