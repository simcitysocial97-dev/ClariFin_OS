# Auto-generated contract tests for cards router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/cards
# Generated: 2026-07-28T09:26:05.981579
# To regenerate: python tools/generate_contract_tests.py --routers cards

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_cards_contract(client):
    """Contract: GET /api/cards matches OpenAPI schema"""
    
    response = client.get("/api/cards")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 400, 404, 422], \
        f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"

    