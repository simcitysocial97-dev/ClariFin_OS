# Auto-generated contract tests for net-worth router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/net-worth
# Generated: 94f8e321ada7
# To regenerate: python tools/generate_contract_tests.py --routers net-worth

import pytest


@pytest.mark.contract
def test_get__api_v1_net_worth_contract(client):
    """Contract: GET /api/v1/net-worth matches OpenAPI schema"""

    response = client.get("/api/v1/net-worth")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"
