"""Schema validation against OpenAPI spec"""

import copy
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

_SCHEMA_CACHE = None


def get_openapi_schemas() -> dict[str, Any]:
    """Load OpenAPI schemas from app"""
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        from src.api import app

        openapi = app.openapi()
        _SCHEMA_CACHE = openapi.get("components", {}).get("schemas", {})
    return _SCHEMA_CACHE


def _inline_refs(
    obj: Any, schemas: dict[str, Any], visited: set[str] | None = None
) -> Any:
    """Recursively inline $ref references inside a schema fragment."""
    if visited is None:
        visited = set()

    if isinstance(obj, dict):
        if "$ref" in obj:
            ref = obj["$ref"]
            if ref.startswith("#/components/schemas/"):
                name = ref.split("/")[-1]
                if name in schemas and name not in visited:
                    visited.add(name)
                    return _inline_refs(copy.deepcopy(schemas[name]), schemas, visited)
            return obj

        result = {}
        for key, value in obj.items():
            result[key] = _inline_refs(value, schemas, visited)
        return result

    if isinstance(obj, list):
        return [_inline_refs(item, schemas, visited) for item in obj]

    return obj


def validate_response_schema(response_data: dict[str, Any], schema_name: str):
    """Validate response against OpenAPI schema"""
    schemas = get_openapi_schemas()

    if schema_name not in schemas:
        raise ValueError(
            f"Schema '{schema_name}' not found in OpenAPI spec. "
            f"Available: {', '.join(schemas.keys())}"
        )

    schema = _inline_refs(copy.deepcopy(schemas[schema_name]), schemas)
    validator = Draft202012Validator(schema)

    try:
        validator.validate(response_data)
    except ValidationError as e:
        raise AssertionError(
            f"Response validation failed for schema '{schema_name}':\n"
            f"  Error: {e.message}\n"
            f"  Path: {' -> '.join(str(p) for p in e.path)}"
        ) from e
