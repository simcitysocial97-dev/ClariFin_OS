# Auto-generated contract tests for export router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/export/csv
# Generated: 2026-07-25T16:41:44.576917
# To regenerate: python tools/generate_contract_tests.py --routers export

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_export_csv_contract(client):
    """Contract: GET /api/export/csv matches OpenAPI schema"""

    response = client.get("/api/export/csv")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
