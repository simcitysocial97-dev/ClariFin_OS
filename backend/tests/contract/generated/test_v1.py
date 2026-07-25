# Auto-generated contract tests for v1 router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts
# Generated: 2026-07-25T16:41:44.787284
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.791034
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.794655
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.799629
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.804852
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.808375
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.811748
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.814991
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.818265
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.821733
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.827005
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.830894
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Source: GET /api/v1/institutions
# Generated: 2026-07-25T16:41:44.834281
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_institutions_contract(client):
    """Contract: GET /api/v1/institutions matches OpenAPI schema"""

    response = client.get("/api/v1/institutions")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/institutions
# Generated: 2026-07-25T16:41:44.838268
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_v1_institutions_contract(client):
    """Contract: POST /api/v1/institutions matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/InstitutionCreateRequest"}
            }
        },
        "required": True,
    }
    response = client.post("/api/v1/institutions", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/institutions/{institution_id}
# Generated: 2026-07-25T16:41:44.841501
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_institutions_institution_id_contract(client):
    """Contract: GET /api/v1/institutions/{institution_id} matches OpenAPI schema"""

    response = client.get("/api/v1/institutions/{institution_id}")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/v1/institutions/{institution_id}
# Generated: 2026-07-25T16:41:44.844684
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_put__api_v1_institutions_institution_id_contract(client):
    """Contract: PUT /api/v1/institutions/{institution_id} matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/InstitutionUpdateRequest"}
            }
        },
    }
    response = client.put("/api/v1/institutions/{institution_id}", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/accounts/{account_id}/links
# Generated: 2026-07-25T16:41:44.847799
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.853138
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.857075
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.860280
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.863342
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 2026-07-25T16:41:44.866350
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_accounts_type_breakdown_contract(client):
    """Contract: GET /api/v1/accounts/type-breakdown matches OpenAPI schema"""

    response = client.get("/api/v1/accounts/type-breakdown")

    # Validate status code
    assert response.status_code in [200], f"Expected [200], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/profile
# Generated: 2026-07-25T16:41:44.869455
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_behaviour_profile_contract(client):
    """Contract: GET /api/v1/behaviour/profile matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/profile")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/wellness-score
# Generated: 2026-07-25T16:41:44.872449
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_behaviour_wellness_score_contract(client):
    """Contract: GET /api/v1/behaviour/wellness-score matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/wellness-score")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/debt-health
# Generated: 2026-07-25T16:41:44.875399
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_behaviour_debt_health_contract(client):
    """Contract: GET /api/v1/behaviour/debt-health matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/debt-health")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/cashflow-health
# Generated: 2026-07-25T16:41:44.878328
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_behaviour_cashflow_health_contract(client):
    """Contract: GET /api/v1/behaviour/cashflow-health matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/cashflow-health")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/patterns
# Generated: 2026-07-25T16:41:44.881184
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_behaviour_patterns_contract(client):
    """Contract: GET /api/v1/behaviour/patterns matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/patterns")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/recommendations
# Generated: 2026-07-25T16:41:44.884172
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_behaviour_recommendations_contract(client):
    """Contract: GET /api/v1/behaviour/recommendations matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/recommendations")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/monthly-report
# Generated: 2026-07-25T16:41:44.887196
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_behaviour_monthly_report_contract(client):
    """Contract: GET /api/v1/behaviour/monthly-report matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/monthly-report")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour
# Generated: 2026-07-25T16:41:44.890060
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_behaviour_contract(client):
    """Contract: GET /api/v1/behaviour matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards
# Generated: 2026-07-25T16:41:44.892976
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_credit_cards_contract(client):
    """Contract: GET /api/v1/credit-cards matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards
# Generated: 2026-07-25T16:41:44.896366
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_v1_credit_cards_contract(client):
    """Contract: POST /api/v1/credit-cards matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/CreditCardCreateRequest"}
            }
        },
    }
    response = client.post("/api/v1/credit-cards", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}
# Generated: 2026-07-25T16:41:44.901375
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id} matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards/{card_id}")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/v1/credit-cards/{card_id}
# Generated: 2026-07-25T16:41:44.906675
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_put__api_v1_credit_cards_card_id_contract(client):
    """Contract: PUT /api/v1/credit-cards/{card_id} matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/CreditCardUpdateRequest"}
            }
        },
    }
    response = client.put("/api/v1/credit-cards/{card_id}", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/v1/credit-cards/{card_id}
# Generated: 2026-07-25T16:41:44.910781
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_delete__api_v1_credit_cards_card_id_contract(client):
    """Contract: DELETE /api/v1/credit-cards/{card_id} matches OpenAPI schema"""

    response = client.delete("/api/v1/credit-cards/{card_id}")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/statements
# Generated: 2026-07-25T16:41:44.916075
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_statements_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/statements matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards/{card_id}/statements")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards/{card_id}/statements
# Generated: 2026-07-25T16:41:44.919355
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_v1_credit_cards_card_id_statements_contract(client):
    """Contract: POST /api/v1/credit-cards/{card_id}/statements matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/StatementGenerateRequest"}
            }
        },
    }
    response = client.post(
        "/api/v1/credit-cards/{card_id}/statements", json=request_body
    )

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/outstanding
# Generated: 2026-07-25T16:41:44.922589
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_outstanding_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/outstanding matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards/{card_id}/outstanding")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/utilization
# Generated: 2026-07-25T16:41:44.925742
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_utilization_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/utilization matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards/{card_id}/utilization")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/metrics
# Generated: 2026-07-25T16:41:44.928855
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_metrics_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/metrics matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards/{card_id}/metrics")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/next-statement-date
# Generated: 2026-07-25T16:41:44.931895
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_next_statement_date_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/next-statement-date matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards/{card_id}/next-statement-date")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards/{card_id}/payments
# Generated: 2026-07-25T16:41:44.935101
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_v1_credit_cards_card_id_payments_contract(client):
    """Contract: POST /api/v1/credit-cards/{card_id}/payments matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/PaymentRecordRequest"}
            }
        },
    }
    response = client.post("/api/v1/credit-cards/{card_id}/payments", json=request_body)

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards/{card_id}/emi-conversion
# Generated: 2026-07-25T16:41:44.938829
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_v1_credit_cards_card_id_emi_conversion_contract(client):
    """Contract: POST /api/v1/credit-cards/{card_id}/emi-conversion matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/EmiConversionRequest"}
            }
        },
    }
    response = client.post(
        "/api/v1/credit-cards/{card_id}/emi-conversion", json=request_body
    )

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards/{card_id}/foreclosure
# Generated: 2026-07-25T16:41:44.941925
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_post__api_v1_credit_cards_card_id_foreclosure_contract(client):
    """Contract: POST /api/v1/credit-cards/{card_id}/foreclosure matches OpenAPI schema"""

    # TODO: Provide valid request body
    request_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ForeclosureRequest"}
            }
        },
    }
    response = client.post(
        "/api/v1/credit-cards/{card_id}/foreclosure", json=request_body
    )

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/cashflow
# Generated: 2026-07-25T16:41:44.944948
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_cashflow_contract(client):
    """Contract: GET /api/v1/cashflow matches OpenAPI schema"""

    response = client.get("/api/v1/cashflow")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/forecast
# Generated: 2026-07-25T16:41:44.948734
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_forecast_contract(client):
    """Contract: GET /api/v1/forecast matches OpenAPI schema"""

    response = client.get("/api/v1/forecast")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/investments
# Generated: 2026-07-25T16:41:44.952253
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_investments_contract(client):
    """Contract: GET /api/v1/investments matches OpenAPI schema"""

    response = client.get("/api/v1/investments")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/loans
# Generated: 2026-07-25T16:41:44.956197
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_loans_contract(client):
    """Contract: GET /api/v1/loans matches OpenAPI schema"""

    response = client.get("/api/v1/loans")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/net-worth
# Generated: 2026-07-25T16:41:44.959398
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_net_worth_contract(client):
    """Contract: GET /api/v1/net-worth matches OpenAPI schema"""

    response = client.get("/api/v1/net-worth")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/reconciliation
# Generated: 2026-07-25T16:41:44.962432
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema


@pytest.mark.contract
def test_get__api_v1_reconciliation_contract(client):
    """Contract: GET /api/v1/reconciliation matches OpenAPI schema"""

    response = client.get("/api/v1/reconciliation")

    # Validate status code
    assert response.status_code in [
        200,
        422,
    ], f"Expected [200, 422], got {response.status_code}"
