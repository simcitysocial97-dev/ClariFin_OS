# Auto-generated contract tests for upload router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/upload
# Generated: 2026-07-25T16:41:44.782789
# To regenerate: python tools/generate_contract_tests.py --routers upload

import pytest


@pytest.mark.contract
def test_post__api_upload_contract(client):
    """Contract: POST /api/upload matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "content": {
            "multipart/form-data": {
                "schema": {
                    "$ref": "#/components/schemas/Body_upload_statement_api_upload_post"
                }
            }
        },
        "required": True,
    }
    response = client.post("/api/upload", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
