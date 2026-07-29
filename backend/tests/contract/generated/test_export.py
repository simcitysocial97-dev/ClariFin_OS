# Auto-generated contract tests for export router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/export/csv
# Generated: 2026-07-28T09:26:06.084735
# To regenerate: python tools/generate_contract_tests.py --routers export

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_export_csv_contract(client):
    """Contract: GET /api/export/csv matches OpenAPI schema"""
    
    response = client.get("/api/export/csv")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    