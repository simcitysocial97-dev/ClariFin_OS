# Auto-generated contract tests for import router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/import/detect
# Generated: 2026-07-28T09:26:06.098615
# To regenerate: python tools/generate_contract_tests.py --routers import

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_import_detect_contract(client):
    """Contract: POST /api/import/detect matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/import/detect", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/import/execute
# Generated: 2026-07-28T09:26:06.100729
# To regenerate: python tools/generate_contract_tests.py --routers import

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_import_execute_contract(client):
    """Contract: POST /api/import/execute matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/import/execute", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    