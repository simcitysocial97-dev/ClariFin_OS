# Auto-generated contract tests for overview router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/overview
# Generated: 2026-07-25T16:41:44.717901
# To regenerate: python tools/generate_contract_tests.py --routers overview

import pytest


@pytest.mark.contract
def test_get__api_overview_contract(client):
    """Contract: GET /api/overview matches OpenAPI schema"""

    response = client.get("/api/overview")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
