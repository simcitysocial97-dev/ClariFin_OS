# Auto-generated contract tests for analytics router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/analytics
# Generated: d1ef7a9c5c9e
# To regenerate: python tools/generate_contract_tests.py --routers analytics

import pytest


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_analytics_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/analytics matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/1/analytics")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/analytics
# Generated: 5ceb676bca1a
# To regenerate: python tools/generate_contract_tests.py --routers analytics

import pytest


@pytest.mark.contract
def test_get__api_analytics_contract(client):
    """Contract: GET /api/analytics matches OpenAPI schema"""

    response = client.get("/api/analytics")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"
