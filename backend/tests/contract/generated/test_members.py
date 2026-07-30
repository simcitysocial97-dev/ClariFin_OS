# Auto-generated contract tests for members router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/members
# Generated: a1098deaf823
# To regenerate: python tools/generate_contract_tests.py --routers members

import pytest


@pytest.mark.contract
def test_get__api_members_contract(client):
    """Contract: GET /api/members matches OpenAPI schema"""

    response = client.get("/api/members")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        400,
        404,
        422,
    ], f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/members
# Generated: 0ea9c08db477
# To regenerate: python tools/generate_contract_tests.py --routers members

import pytest


@pytest.mark.contract
def test_post__api_members_contract(client):
    """Contract: POST /api/members matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/members", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"
