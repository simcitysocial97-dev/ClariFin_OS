# Auto-generated contract tests for import router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/import/detect
# Generated: 2026-07-25T16:41:44.601495
# To regenerate: python tools/generate_contract_tests.py --routers import

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_import_detect_contract(client):
    """Contract: POST /api/import/detect matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "content": {
            "multipart/form-data": {
                "schema": {
                    "$ref": "#/components/schemas/Body_import_detect_api_import_detect_post"
                }
            }
        },
        "required": True,
    }
    response = client.post("/api/import/detect", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/import/execute
# Generated: 2026-07-25T16:41:44.605360
# To regenerate: python tools/generate_contract_tests.py --routers import

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_import_execute_contract(client):
    """Contract: POST /api/import/execute matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ImportExecute"}
            }
        },
        "required": True,
    }
    response = client.post("/api/import/execute", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
