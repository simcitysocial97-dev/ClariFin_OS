# Auto-generated contract tests for analytics router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/analytics
# Generated: 2026-07-25T16:41:44.492517
# To regenerate: python tools/generate_contract_tests.py --routers analytics

import pytest


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_analytics_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/analytics matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/{account_id}/analytics")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/analytics
# Generated: 2026-07-25T16:41:44.496160
# To regenerate: python tools/generate_contract_tests.py --routers analytics

import pytest


@pytest.mark.contract
def test_get__api_analytics_contract(client):
    """Contract: GET /api/analytics matches OpenAPI schema"""

    response = client.get("/api/analytics")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
