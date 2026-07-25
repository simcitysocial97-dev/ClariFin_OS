# Auto-generated contract tests for accounts router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts
# Generated: 2026-07-25T16:41:44.408454
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_accounts_contract(client):
    """Contract: GET /api/v1/accounts matches OpenAPI schema"""

    response = client.get("/api/v1/accounts")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"

    # Validate response schema
    if response.status_code == 200:
        validate_response_schema(response.json(), "AccountsDTO")


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/accounts
# Generated: 2026-07-25T16:41:44.411700
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_v1_accounts_contract(client):
    """Contract: POST /api/v1/accounts matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/AccountCreateRequest"}
            }
        },
    }
    response = client.post("/api/v1/accounts", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}
# Generated: 2026-07-25T16:41:44.414845
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_contract(client):
    """Contract: GET /api/v1/accounts/{account_id} matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/{account_id}")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"

    # Validate response schema
    if response.status_code == 200:
        validate_response_schema(response.json(), "AccountDetailDTO")


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/v1/accounts/{account_id}
# Generated: 2026-07-25T16:41:44.418207
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_put__api_v1_accounts_account_id_contract(client):
    """Contract: PUT /api/v1/accounts/{account_id} matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/AccountUpdateRequest"}
            }
        },
    }
    response = client.put("/api/v1/accounts/{account_id}", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/v1/accounts/{account_id}
# Generated: 2026-07-25T16:41:44.422095
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_delete__api_v1_accounts_account_id_contract(client):
    """Contract: DELETE /api/v1/accounts/{account_id} matches OpenAPI schema"""

    response = client.delete("/api/v1/accounts/{account_id}")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/accounts/{account_id}/balance-history
# Generated: 2026-07-25T16:41:44.425813
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_v1_accounts_account_id_balance_history_contract(client):
    """Contract: POST /api/v1/accounts/{account_id}/balance-history matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/BalanceSnapshotRequest"}
            }
        },
    }
    response = client.post(
        "/api/v1/accounts/{account_id}/balance-history", json=request_body
    )

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/balance-history
# Generated: 2026-07-25T16:41:44.429019
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_balance_history_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/balance-history matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/{account_id}/balance-history")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"

    # Validate response schema
    if response.status_code == 200:
        validate_response_schema(response.json(), "AccountsHistoryResponse")


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/balance-history/latest
# Generated: 2026-07-25T16:41:44.432045
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_balance_history_latest_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/balance-history/latest matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/{account_id}/balance-history/latest")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/analytics
# Generated: 2026-07-25T16:41:44.435961
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_analytics_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/analytics matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/{account_id}/analytics")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/metrics
# Generated: 2026-07-25T16:41:44.439214
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_metrics_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/metrics matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/{account_id}/metrics")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/status
# Generated: 2026-07-25T16:41:44.442385
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_status_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/status matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/{account_id}/status")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/dormancy
# Generated: 2026-07-25T16:41:44.445472
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_dormancy_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/dormancy matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/{account_id}/dormancy")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/accounts/{account_id}/links
# Generated: 2026-07-25T16:41:44.448657
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_v1_accounts_account_id_links_contract(client):
    """Contract: POST /api/v1/accounts/{account_id}/links matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/AccountLinkRequest"}
            }
        },
    }
    response = client.post("/api/v1/accounts/{account_id}/links", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/links
# Generated: 2026-07-25T16:41:44.452609
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_links_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/links matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/{account_id}/links")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/v1/accounts/{account_id}/links/{linked_account_id}
# Generated: 2026-07-25T16:41:44.455792
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_delete__api_v1_accounts_account_id_links_linked_account_id_contract(client):
    """Contract: DELETE /api/v1/accounts/{account_id}/links/{linked_account_id} matches OpenAPI schema"""

    response = client.delete("/api/v1/accounts/{account_id}/links/{linked_account_id}")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/transactions
# Generated: 2026-07-25T16:41:44.458900
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_accounts_account_id_transactions_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/transactions matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/{account_id}/transactions")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"

    # Validate response schema
    if response.status_code == 200:
        validate_response_schema(response.json(), "AccountsTransactionsResponse")


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/summary
# Generated: 2026-07-25T16:41:44.461951
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_accounts_summary_contract(client):
    """Contract: GET /api/v1/accounts/summary matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/summary")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"

    # Validate response schema
    if response.status_code == 200:
        validate_response_schema(response.json(), "AccountsDTO")


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/type-breakdown
# Generated: 2026-07-25T16:41:44.464999
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_accounts_type_breakdown_contract(client):
    """Contract: GET /api/v1/accounts/type-breakdown matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/type-breakdown")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/accounts/manage
# Generated: 2026-07-25T16:41:44.468300
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_accounts_manage_contract(client):
    """Contract: GET /api/accounts/manage matches OpenAPI schema"""

    response = client.get("/api/accounts/manage")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/accounts/manage
# Generated: 2026-07-25T16:41:44.471877
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_accounts_manage_contract(client):
    """Contract: POST /api/accounts/manage matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/AccountCreate"}
            }
        },
        "required": True,
    }
    response = client.post("/api/accounts/manage", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/accounts/manage/{account_id}
# Generated: 2026-07-25T16:41:44.475304
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_put__api_accounts_manage_account_id_contract(client):
    """Contract: PUT /api/accounts/manage/{account_id} matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/AccountUpdate"}
            }
        },
    }
    response = client.put("/api/accounts/manage/{account_id}", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/accounts/manage/{account_id}
# Generated: 2026-07-25T16:41:44.478635
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_delete__api_accounts_manage_account_id_contract(client):
    """Contract: DELETE /api/accounts/manage/{account_id} matches OpenAPI schema"""

    response = client.delete("/api/accounts/manage/{account_id}")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/accounts/{account_id}/balance
# Generated: 2026-07-25T16:41:44.482234
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_accounts_account_id_balance_contract(client):
    """Contract: GET /api/accounts/{account_id}/balance matches OpenAPI schema"""

    response = client.get("/api/accounts/{account_id}/balance")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/accounts/{account_id}/running-balance
# Generated: 2026-07-25T16:41:44.486168
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_accounts_account_id_running_balance_contract(client):
    """Contract: GET /api/accounts/{account_id}/running-balance matches OpenAPI schema"""

    response = client.get("/api/accounts/{account_id}/running-balance")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
