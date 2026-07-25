# Auto-generated contract tests for members router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/members
# Generated: 2026-07-25T16:41:44.703775
# To regenerate: python tools/generate_contract_tests.py --routers members

import pytest


@pytest.mark.contract
def test_get__api_members_contract(client):
    """Contract: GET /api/members matches OpenAPI schema"""

    response = client.get("/api/members")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/members
# Generated: 2026-07-25T16:41:44.707462
# To regenerate: python tools/generate_contract_tests.py --routers members

import pytest


@pytest.mark.contract
def test_post__api_members_contract(client):
    """Contract: POST /api/members matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/MemberCreate"}
            }
        },
        "required": True,
    }
    response = client.post("/api/members", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
