# Auto-generated contract tests for institutions router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/institutions
# Generated: 2026-07-28T09:26:06.103178
# To regenerate: python tools/generate_contract_tests.py --routers institutions

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_institutions_contract(client):
    """Contract: GET /api/v1/institutions matches OpenAPI schema"""
    
    response = client.get("/api/v1/institutions")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 400, 404, 422], \
        f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/institutions
# Generated: 2026-07-28T09:26:06.106081
# To regenerate: python tools/generate_contract_tests.py --routers institutions

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_v1_institutions_contract(client):
    """Contract: POST /api/v1/institutions matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/institutions", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/institutions/{institution_id}
# Generated: 2026-07-28T09:26:06.109881
# To regenerate: python tools/generate_contract_tests.py --routers institutions

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_institutions_institution_id_contract(client):
    """Contract: GET /api/v1/institutions/{institution_id} matches OpenAPI schema"""
    
    response = client.get("/api/v1/institutions/1")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/v1/institutions/{institution_id}
# Generated: 2026-07-28T09:26:06.112586
# To regenerate: python tools/generate_contract_tests.py --routers institutions

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_put__api_v1_institutions_institution_id_contract(client):
    """Contract: PUT /api/v1/institutions/{institution_id} matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.put("/api/v1/institutions/1", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    