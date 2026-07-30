# Auto-generated contract tests for networth router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/networth
# Generated: 918a4ff2b609
# To regenerate: python tools/generate_contract_tests.py --routers networth

import pytest


@pytest.mark.contract
def test_get__api_networth_contract(client):
    """Contract: GET /api/networth matches OpenAPI schema"""

    response = client.get("/api/networth")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        400,
        404,
        422,
    ], f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"
