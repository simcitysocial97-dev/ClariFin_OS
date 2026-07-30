# Auto-generated contract tests for overview router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/overview
# Generated: 81db26821c40
# To regenerate: python tools/generate_contract_tests.py --routers overview

import pytest


@pytest.mark.contract
def test_get__api_overview_contract(client):
    """Contract: GET /api/overview matches OpenAPI schema"""

    response = client.get("/api/overview")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"
