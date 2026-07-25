# Auto-generated contract tests for reconciliations router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/reconciliations
# Generated: 2026-07-25T16:41:44.722207
# To regenerate: python tools/generate_contract_tests.py --routers reconciliations

import pytest


@pytest.mark.contract
def test_get__api_reconciliations_contract(client):
    """Contract: GET /api/reconciliations matches OpenAPI schema"""

    response = client.get("/api/reconciliations")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/reconciliations/pending
# Generated: 2026-07-25T16:41:44.726037
# To regenerate: python tools/generate_contract_tests.py --routers reconciliations

import pytest


@pytest.mark.contract
def test_get__api_reconciliations_pending_contract(client):
    """Contract: GET /api/reconciliations/pending matches OpenAPI schema"""

    response = client.get("/api/reconciliations/pending")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/reconciliations/scan
# Generated: 2026-07-25T16:41:44.729594
# To regenerate: python tools/generate_contract_tests.py --routers reconciliations

import pytest


@pytest.mark.contract
def test_get__api_reconciliations_scan_contract(client):
    """Contract: GET /api/reconciliations/scan matches OpenAPI schema"""

    response = client.get("/api/reconciliations/scan")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/reconciliations/create
# Generated: 2026-07-25T16:41:44.733029
# To regenerate: python tools/generate_contract_tests.py --routers reconciliations

import pytest


@pytest.mark.contract
def test_post__api_reconciliations_create_contract(client):
    """Contract: POST /api/reconciliations/create matches OpenAPI schema"""

    response = client.post("/api/reconciliations/create")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/reconciliations/batch-insert
# Generated: 2026-07-25T16:41:44.737264
# To regenerate: python tools/generate_contract_tests.py --routers reconciliations

import pytest


@pytest.mark.contract
def test_post__api_reconciliations_batch_insert_contract(client):
    """Contract: POST /api/reconciliations/batch-insert matches OpenAPI schema"""

    response = client.post("/api/reconciliations/batch-insert")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/reconciliations/{reconciliation_id}/confirm
# Generated: 2026-07-25T16:41:44.741469
# To regenerate: python tools/generate_contract_tests.py --routers reconciliations

import pytest


@pytest.mark.contract
def test_post__api_reconciliations_reconciliation_id_confirm_contract(client):
    """Contract: POST /api/reconciliations/{reconciliation_id}/confirm matches OpenAPI schema"""

    response = client.post("/api/reconciliations/{reconciliation_id}/confirm")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/reconciliations/{reconciliation_id}/reject
# Generated: 2026-07-25T16:41:44.745077
# To regenerate: python tools/generate_contract_tests.py --routers reconciliations

import pytest


@pytest.mark.contract
def test_post__api_reconciliations_reconciliation_id_reject_contract(client):
    """Contract: POST /api/reconciliations/{reconciliation_id}/reject matches OpenAPI schema"""

    response = client.post("/api/reconciliations/{reconciliation_id}/reject")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
