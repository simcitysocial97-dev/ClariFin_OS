#!/usr/bin/env python3
"""
Auto-generate contract tests from OpenAPI schema.
Run after any API schema change.

Usage:
    python tools/generate_contract_tests.py --routers cashflow,accounts,loans
    python tools/generate_contract_tests.py --all
"""

import argparse
from pathlib import Path

from jinja2 import Template


def get_openapi_schema() -> dict:
    """Extract OpenAPI schema from FastAPI app"""
    import sys

    # Ensure the backend package root is importable as `src.*`
    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        from src.api import app

        return app.openapi()
    except Exception:
        # Fallback to cached frontend schema if backend app import fails
        frontend_schema = (
            Path(__file__).parent.parent.parent / "frontend" / "api-schema.json"
        )
        if frontend_schema.exists():
            import json

            return json.loads(frontend_schema.read_text())
        raise


def generate_test_for_endpoint(
    path: str, method: str, operation: dict, router_name: str
) -> str:
    """Generate pytest test code for one endpoint"""

    template = Template('''
# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: {{ method|upper }} {{ path }}
# Generated: {{ timestamp }}
# To regenerate: python tools/generate_contract_tests.py --routers {{ router_name }}

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_{{ test_name }}_contract(client):
    """Contract: {{ method|upper }} {{ path }} matches OpenAPI schema"""
    {% if request_body %}
    # TODO: Provide valid request body
    request_body = {{ request_body }}
    response = client.{{ method }}("{{ path }}", json=request_body)
    {% else %}
    response = client.{{ method }}("{{ path }}")
    {% endif %}

    # Validate status code
    assert response.status_code in {{ valid_statuses }}, \\
        f"Expected {{ valid_statuses }}, got {response.status_code}"

    {% if response_schema %}
    # Validate response schema
    if response.status_code == 200:
        validate_response_schema(
            response.json(),
            "{{ response_schema }}"
        )
    {% endif %}
''')

    from datetime import datetime

    # Extract response schema
    response_schema = None
    if "responses" in operation and "200" in operation["responses"]:
        content = operation["responses"]["200"].get("content", {})
        if "application/json" in content:
            schema_ref = content["application/json"].get("schema", {}).get("$ref", "")
            if schema_ref:
                response_schema = schema_ref.split("/")[-1]

    # Extract valid status codes
    valid_statuses = list(operation.get("responses", {}).keys())
    valid_statuses = [int(s) for s in valid_statuses if s.isdigit()]

    # Generate test name (sanitize: replace hyphens with underscores)
    test_name = f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '')}"
    test_name = test_name.replace("-", "_")

    return template.render(
        method=method,
        path=path,
        test_name=test_name,
        router_name=router_name,
        timestamp=datetime.now().isoformat(),
        request_body=operation.get("requestBody"),
        response_schema=response_schema,
        valid_statuses=valid_statuses,
    )


def generate_for_router(router_name: str, schema: dict, output_dir: Path):
    """Generate tests for one router"""

    # Sanitize filename: replace hyphens with underscores
    safe_name = router_name.replace("-", "_")
    output_file = output_dir / f"test_{safe_name}.py"
    tests = []

    # Header
    tests.append(f"# Auto-generated contract tests for {router_name} router")
    tests.append("# DO NOT EDIT MANUALLY")
    tests.append("")

    # Generate tests for each endpoint in this router
    for path, methods in schema["paths"].items():
        if f"/{router_name}" in path or path.startswith(f"/api/{router_name}"):
            for method, operation in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    test_code = generate_test_for_endpoint(
                        path, method, operation, router_name
                    )
                    tests.append(test_code)

    output_file.write_text("\n".join(tests))
    print(f"✅ Generated: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate contract tests from OpenAPI")
    parser.add_argument(
        "--routers", help="Comma-separated router names (e.g., cashflow,accounts)"
    )
    parser.add_argument("--all", action="store_true", help="Generate for all routers")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be generated"
    )

    args = parser.parse_args()

    # Get OpenAPI schema
    print("📖 Reading OpenAPI schema...")
    schema = get_openapi_schema()

    # Determine routers
    if args.all:
        # Extract unique router names from paths
        routers = set()
        for path in schema["paths"]:
            parts = path.strip("/").split("/")
            if len(parts) >= 2 and parts[0] == "api":
                routers.add(parts[1])
        routers = sorted(routers)
    elif args.routers:
        routers = [r.strip() for r in args.routers.split(",")]
    else:
        print("❌ Specify --routers or --all")
        return

    print(f"📝 Generating tests for: {', '.join(routers)}")

    # Output directory
    output_dir = Path("tests/contract/generated")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        print("🔍 DRY RUN - would generate:")
        for router in routers:
            print(f"   - tests/contract/generated/test_{router}.py")
        return

    # Generate tests
    for router in routers:
        generate_for_router(router, schema, output_dir)

    print(f"\n✅ Generated {len(routers)} contract test files")
    print(f"📁 Location: {output_dir}")
    print("\n▶️  Run: pytest tests/contract/generated/ -v")


if __name__ == "__main__":
    main()
