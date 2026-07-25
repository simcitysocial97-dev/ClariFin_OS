"""Schema validation against OpenAPI spec"""

from jsonschema import validate, ValidationError
from typing import Dict

# Cache for OpenAPI schemas
_SCHEMA_CACHE = None


def get_openapi_schemas() -> Dict:
    """Load OpenAPI schemas from app"""
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

        from main import app

        openapi = app.openapi()
        _SCHEMA_CACHE = openapi.get("components", {}).get("schemas", {})
    return _SCHEMA_CACHE


def validate_response_schema(response_data: dict, schema_name: str):
    """Validate response against OpenAPI schema"""
    schemas = get_openapi_schemas()

    if schema_name not in schemas:
        raise ValueError(
            f"Schema '{schema_name}' not found in OpenAPI spec. "
            f"Available: {', '.join(schemas.keys())}"
        )

    schema = schemas[schema_name]

    try:
        validate(instance=response_data, schema=schema)
    except ValidationError as e:
        raise AssertionError(
            f"Response validation failed for schema '{schema_name}':\n"
            f"  Error: {e.message}\n"
            f"  Path: {' -> '.join(str(p) for p in e.path)}"
        )
