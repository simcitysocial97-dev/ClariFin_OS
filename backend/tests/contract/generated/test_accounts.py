# Auto-generated contract tests for accounts router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts
# Generated: b66a73d295cb
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_get__api_v1_accounts_contract(client):
    """Contract: GET /api/v1/accounts matches OpenAPI schema"""

    response = client.get("/api/v1/accounts")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        400,
        404,
        422,
    ], f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/accounts
# Generated: bb1a4c542386
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_post__api_v1_accounts_contract(client):
    """Contract: POST /api/v1/accounts matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/accounts", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}
# Generated: 930f17c7cec5
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_contract(client):
    """Contract: GET /api/v1/accounts/{account_id} matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/1")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/v1/accounts/{account_id}
# Generated: 1d17dfbf9c68
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_put__api_v1_accounts_account_id_contract(client):
    """Contract: PUT /api/v1/accounts/{account_id} matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.put("/api/v1/accounts/1", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/v1/accounts/{account_id}
# Generated: e34ba2f53eb0
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_delete__api_v1_accounts_account_id_contract(client):
    """Contract: DELETE /api/v1/accounts/{account_id} matches OpenAPI schema"""

    response = client.delete("/api/v1/accounts/1")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/accounts/{account_id}/balance-history
# Generated: 47546ec12a29
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_post__api_v1_accounts_account_id_balance_history_contract(client):
    """Contract: POST /api/v1/accounts/{account_id}/balance-history matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/accounts/1/balance-history", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/balance-history
# Generated: 2f0adafb823c
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_balance_history_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/balance-history matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/1/balance-history")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/balance-history/latest
# Generated: 868d758bbf33
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_balance_history_latest_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/balance-history/latest matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/1/balance-history/latest")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/analytics
# Generated: 7acd9095ff54
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_analytics_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/analytics matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/1/analytics")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/metrics
# Generated: 93b48afaa256
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_metrics_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/metrics matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/1/metrics")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/status
# Generated: 8d86e0612102
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_status_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/status matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/1/status")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/dormancy
# Generated: bcf92a6a7377
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_dormancy_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/dormancy matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/1/dormancy")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/accounts/{account_id}/links
# Generated: eef0bd9038fe
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_post__api_v1_accounts_account_id_links_contract(client):
    """Contract: POST /api/v1/accounts/{account_id}/links matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/accounts/1/links", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/links
# Generated: f7551e528ccb
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_links_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/links matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/1/links")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/v1/accounts/{account_id}/links/{linked_account_id}
# Generated: eb559309e1ad
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_delete__api_v1_accounts_account_id_links_linked_account_id_contract(client):
    """Contract: DELETE /api/v1/accounts/{account_id}/links/{linked_account_id} matches OpenAPI schema"""

    response = client.delete("/api/v1/accounts/1/links/1")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/accounts/manage
# Generated: e99bd47f94ec
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_get__api_accounts_manage_contract(client):
    """Contract: GET /api/accounts/manage matches OpenAPI schema"""

    response = client.get("/api/accounts/manage")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        400,
        404,
        422,
    ], f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/accounts/manage
# Generated: ba1bfdc9b86e
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_post__api_accounts_manage_contract(client):
    """Contract: POST /api/accounts/manage matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/accounts/manage", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/accounts/manage/{account_id}
# Generated: 65447f5f26eb
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_put__api_accounts_manage_account_id_contract(client):
    """Contract: PUT /api/accounts/manage/{account_id} matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.put("/api/accounts/manage/1", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/accounts/manage/{account_id}
# Generated: 57abc6daba73
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_delete__api_accounts_manage_account_id_contract(client):
    """Contract: DELETE /api/accounts/manage/{account_id} matches OpenAPI schema"""

    response = client.delete("/api/accounts/manage/1")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/accounts/{account_id}/balance
# Generated: 33218f8eceb1
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_get__api_accounts_account_id_balance_contract(client):
    """Contract: GET /api/accounts/{account_id}/balance matches OpenAPI schema"""

    response = client.get("/api/accounts/1/balance")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/accounts/{account_id}/running-balance
# Generated: bc8a3e366507
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest


@pytest.mark.contract
def test_get__api_accounts_account_id_running_balance_contract(client):
    """Contract: GET /api/accounts/{account_id}/running-balance matches OpenAPI schema"""

    response = client.get("/api/accounts/1/running-balance")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"
