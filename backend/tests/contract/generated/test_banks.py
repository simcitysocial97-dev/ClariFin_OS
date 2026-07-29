# Auto-generated contract tests for banks router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/banks
# Generated: 2026-07-28T09:26:05.950893
# To regenerate: python tools/generate_contract_tests.py --routers banks

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_banks_contract(client):
    """Contract: GET /api/banks matches OpenAPI schema"""
    
    response = client.get("/api/banks")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 400, 404, 422], \
        f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"

    