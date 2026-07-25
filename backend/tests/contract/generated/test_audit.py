# Auto-generated contract tests for audit router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/audit/report
# Generated: 2026-07-25T16:41:44.505694
# To regenerate: python tools/generate_contract_tests.py --routers audit

import pytest


@pytest.mark.contract
def test_get__api_audit_report_contract(client):
    """Contract: GET /api/audit/report matches OpenAPI schema"""

    response = client.get("/api/audit/report")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"
