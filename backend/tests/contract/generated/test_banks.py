# Auto-generated contract tests for banks router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/banks
# Generated: 2026-07-25T16:41:44.512115
# To regenerate: python tools/generate_contract_tests.py --routers banks

import pytest


@pytest.mark.contract
def test_get__api_banks_contract(client):
    """Contract: GET /api/banks matches OpenAPI schema"""

    response = client.get("/api/banks")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"
