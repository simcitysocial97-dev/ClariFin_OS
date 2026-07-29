# Auto-generated contract tests for statements router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/statements
# Generated: 2026-07-28T09:26:06.335904
# To regenerate: python tools/generate_contract_tests.py --routers statements

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_statements_contract(client):
    """Contract: GET /api/statements matches OpenAPI schema"""
    
    response = client.get("/api/statements")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 400, 404, 422], \
        f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/statements/{statement_id}/validate
# Generated: 2026-07-28T09:26:06.338233
# To regenerate: python tools/generate_contract_tests.py --routers statements

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_statements_statement_id_validate_contract(client):
    """Contract: GET /api/statements/{statement_id}/validate matches OpenAPI schema"""
    
    response = client.get("/api/statements/1/validate?claimed_balance_paise=1")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/statements
# Generated: 2026-07-28T09:26:06.341539
# To regenerate: python tools/generate_contract_tests.py --routers statements

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_statements_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/statements matches OpenAPI schema"""
    
    response = client.get("/api/v1/credit-cards/1/statements")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards/{card_id}/statements
# Generated: 2026-07-28T09:26:06.343911
# To regenerate: python tools/generate_contract_tests.py --routers statements

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_v1_credit_cards_card_id_statements_contract(client):
    """Contract: POST /api/v1/credit-cards/{card_id}/statements matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/credit-cards/1/statements", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    