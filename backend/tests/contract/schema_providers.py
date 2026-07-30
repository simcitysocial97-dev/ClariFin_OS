"""Schema providers for contract validation.

Provides access to OpenAPI schemas from the live FastAPI application.
No mandatory Schemathesis dependency - uses manual generation when unavailable.
"""

from __future__ import annotations

# Add src to path
from typing import Any


def get_openapi_schema() -> dict[str, Any]:
    """Get OpenAPI schema from live FastAPI application."""
    try:
        from src.api import app

        return app.openapi()
    except ImportError as e:
        raise RuntimeError(f"Cannot load FastAPI app: {e}") from e


def get_path_schema(path: str, method: str) -> dict[str, Any]:
    """Get schema for a specific endpoint path/method."""
    schema = get_openapi_schema()
    paths = schema.get("paths", {})

    path_spec = paths.get(path, {})
    method_spec = path_spec.get(method.lower(), {})

    return method_spec


def get_request_body_schema(path: str, method: str) -> dict[str, Any]:
    """Get request body schema for an endpoint."""
    method_spec = get_path_schema(path, method)
    request_body = method_spec.get("requestBody", {})

    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    return json_content.get("schema", {})


def get_response_schema(
    path: str, method: str, status_code: str = "200"
) -> dict[str, Any]:
    """Get response schema for an endpoint."""
    method_spec = get_path_schema(path, method)
    responses = method_spec.get("responses", {})

    response = responses.get(status_code, {})
    content = response.get("content", {})
    json_content = content.get("application/json", {})
    return json_content.get("schema", {})


def get_parameters(path: str, method: str) -> list[dict[str, Any]]:
    """Get parameters for an endpoint (path, query, header)."""
    method_spec = get_path_schema(path, method)
    return method_spec.get("parameters", [])


def generate_test_cases_from_schema(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate basic test cases from a schema.

    Returns:
        - Valid payloads (minimal required fields)
        - Boundary values (min/max for integers)
        - Invalid payloads (wrong types)
    """
    test_cases = []

    if not schema:
        return test_cases

    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Generate valid minimal payload
    valid = {}
    for prop, prop_schema in properties.items():
        if prop in required:
            valid[prop] = _get_example_value(prop_schema)
    if valid:
        test_cases.append(
            {"name": "valid_minimal", "payload": valid, "expected_status": "200"}
        )

    # Generate missing required field cases
    for prop in required:
        missing = {k: v for k, v in valid.items() if k != prop}
        test_cases.append(
            {"name": f"missing_{prop}", "payload": missing, "expected_status": "422"}
        )

    # Generate type violation cases
    for prop, prop_schema in properties.items():
        if prop in required:
            type_violation = dict(valid)
            type_violation[prop] = _get_invalid_type_value(prop_schema)
            test_cases.append(
                {
                    "name": f"type_violation_{prop}",
                    "payload": type_violation,
                    "expected_status": "422",
                }
            )

    # Generate boundary cases for integer fields
    for prop, prop_schema in properties.items():
        if prop in required:
            boundaries = _get_boundary_values(prop, prop_schema)
            test_cases.extend(boundaries)

    return test_cases


def _get_example_value(prop_schema: dict[str, Any]) -> Any:
    """Get example value for a property schema."""
    if "example" in prop_schema:
        return prop_schema["example"]

    prop_type = prop_schema.get("type", "string")

    if prop_type == "string":
        return "test_value"
    if prop_type == "integer":
        return 0
    if prop_type == "number":
        return 0.0
    if prop_type == "boolean":
        return False
    if prop_type == "array":
        return []
    if prop_type == "object":
        return {}

    return None


def _get_invalid_type_value(prop_schema: dict[str, Any]) -> Any:
    """Get a value with wrong type for a property."""
    prop_type = prop_schema.get("type", "string")

    if prop_type == "string":
        return 12345  # integer instead of string
    if prop_type == "integer":
        return "not_a_number"  # string instead of integer
    if prop_type == "boolean":
        return "true"  # string instead of boolean
    if prop_type == "array":
        return "not_an_array"  # string instead of array
    if prop_type == "object":
        return "not_an_object"  # string instead of object

    return "invalid_type"


def _get_boundary_values(
    prop: str, prop_schema: dict[str, Any]
) -> list[dict[str, Any]]:
    """Generate boundary value test cases."""
    test_cases = []

    if prop_schema.get("type") == "integer":
        minimum = prop_schema.get("minimum")
        maximum = prop_schema.get("maximum")

        if minimum is not None:
            test_cases.append(
                {
                    "name": f"boundary_min_{prop}",
                    "payload": {
                        "_target": prop,
                        "value": minimum - 1,
                        "expected_status": "422",
                    },
                }
            )

        if maximum is not None:
            test_cases.append(
                {
                    "name": f"boundary_max_{prop}",
                    "payload": {
                        "_target": prop,
                        "value": maximum + 1,
                        "expected_status": "422",
                    },
                }
            )

    return test_cases
