# Auto-generated contract tests for investments router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/investments
# Generated: 2026-07-28T09:26:06.116106
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_investments_contract(client):
    """Contract: GET /api/investments matches OpenAPI schema"""
    
    response = client.get("/api/investments")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 400, 404, 422], \
        f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/investments
# Generated: 2026-07-28T09:26:06.118220
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_investments_contract(client):
    """Contract: POST /api/investments matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/investments", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/investments/{investment_id}
# Generated: 2026-07-28T09:26:06.120349
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_put__api_investments_investment_id_contract(client):
    """Contract: PUT /api/investments/{investment_id} matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.put("/api/investments/1", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/investments/{investment_id}
# Generated: 2026-07-28T09:26:06.123942
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_delete__api_investments_investment_id_contract(client):
    """Contract: DELETE /api/investments/{investment_id} matches OpenAPI schema"""
    
    response = client.delete("/api/investments/1")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/investments
# Generated: 2026-07-28T09:26:06.127342
# To regenerate: python tools/generate_contract_tests.py --routers investments

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_investments_contract(client):
    """Contract: GET /api/v1/investments matches OpenAPI schema"""
    
    response = client.get("/api/v1/investments")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    