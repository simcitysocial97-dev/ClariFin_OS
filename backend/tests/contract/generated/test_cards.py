# Auto-generated contract tests for cards router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/cards
# Generated: 2026-07-25T16:41:44.518536
# To regenerate: python tools/generate_contract_tests.py --routers cards

import pytest


@pytest.mark.contract
def test_get__api_cards_contract(client):
    """Contract: GET /api/cards matches OpenAPI schema"""

    response = client.get("/api/cards")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"
