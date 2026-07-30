# Auto-generated contract tests for reconciliation router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/reconciliations
# Generated: 700b2a0f92f2
# To regenerate: python tools/generate_contract_tests.py --routers reconciliation

import pytest


@pytest.mark.contract
def test_get__api_reconciliations_contract(client):
    """Contract: GET /api/reconciliations matches OpenAPI schema"""

    response = client.get("/api/reconciliations")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/reconciliations/pending
# Generated: de4b54b4a48c
# To regenerate: python tools/generate_contract_tests.py --routers reconciliation

import pytest


@pytest.mark.contract
def test_get__api_reconciliations_pending_contract(client):
    """Contract: GET /api/reconciliations/pending matches OpenAPI schema"""

    response = client.get("/api/reconciliations/pending")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        400,
        404,
        422,
    ], f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/reconciliations/scan
# Generated: 22ed75441631
# To regenerate: python tools/generate_contract_tests.py --routers reconciliation

import pytest


@pytest.mark.contract
def test_get__api_reconciliations_scan_contract(client):
    """Contract: GET /api/reconciliations/scan matches OpenAPI schema"""

    response = client.get("/api/reconciliations/scan")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        400,
        404,
        422,
    ], f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/reconciliations/create
# Generated: 33209cdd2c0f
# To regenerate: python tools/generate_contract_tests.py --routers reconciliation

import pytest


@pytest.mark.contract
def test_post__api_reconciliations_create_contract(client):
    """Contract: POST /api/reconciliations/create matches OpenAPI schema"""

    response = client.post("/api/reconciliations/create")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/reconciliations/batch-insert
# Generated: d90f0f20fa87
# To regenerate: python tools/generate_contract_tests.py --routers reconciliation

import pytest


@pytest.mark.contract
def test_post__api_reconciliations_batch_insert_contract(client):
    """Contract: POST /api/reconciliations/batch-insert matches OpenAPI schema"""

    response = client.post("/api/reconciliations/batch-insert")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        400,
        404,
        422,
    ], f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/reconciliations/{reconciliation_id}/confirm
# Generated: 9de7ce94fe19
# To regenerate: python tools/generate_contract_tests.py --routers reconciliation

import pytest


@pytest.mark.contract
def test_post__api_reconciliations_reconciliation_id_confirm_contract(client):
    """Contract: POST /api/reconciliations/{reconciliation_id}/confirm matches OpenAPI schema"""

    response = client.post("/api/reconciliations/1/confirm")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/reconciliations/{reconciliation_id}/reject
# Generated: e3071e7feeb8
# To regenerate: python tools/generate_contract_tests.py --routers reconciliation

import pytest


@pytest.mark.contract
def test_post__api_reconciliations_reconciliation_id_reject_contract(client):
    """Contract: POST /api/reconciliations/{reconciliation_id}/reject matches OpenAPI schema"""

    response = client.post("/api/reconciliations/1/reject")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/reconciliation
# Generated: 1b10308164d1
# To regenerate: python tools/generate_contract_tests.py --routers reconciliation

import pytest


@pytest.mark.contract
def test_get__api_v1_reconciliation_contract(client):
    """Contract: GET /api/v1/reconciliation matches OpenAPI schema"""

    response = client.get("/api/v1/reconciliation")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"
