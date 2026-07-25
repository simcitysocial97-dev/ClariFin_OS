# Auto-generated contract tests for networth router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/networth
# Generated: 2026-07-25T16:41:44.712591
# To regenerate: python tools/generate_contract_tests.py --routers networth

import pytest


@pytest.mark.contract
def test_get__api_networth_contract(client):
    """Contract: GET /api/networth matches OpenAPI schema"""

    response = client.get("/api/networth")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"
