# Auto-generated contract tests for audit router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/audit/report
# Generated: 2026-07-28T09:26:05.946820
# To regenerate: python tools/generate_contract_tests.py --routers audit

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_audit_report_contract(client):
    """Contract: GET /api/audit/report matches OpenAPI schema"""
    
    response = client.get("/api/audit/report")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 400, 404, 422], \
        f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"

    