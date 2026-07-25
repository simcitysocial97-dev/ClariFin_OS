# Auto-generated contract tests for dashboard router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/dashboard/summary
# Generated: 2026-07-25T16:41:44.570670
# To regenerate: python tools/generate_contract_tests.py --routers dashboard

import pytest

from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_dashboard_summary_contract(client):
    """Contract: GET /api/dashboard/summary matches OpenAPI schema"""

    response = client.get("/api/dashboard/summary")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"

    # Validate response schema
    if response.status_code == 200:
        validate_response_schema(response.json(), "DashboardSummaryDTO")
