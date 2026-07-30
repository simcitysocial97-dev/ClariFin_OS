# Auto-generated contract tests for v1 router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts
# Generated: 32cd56ba4ddc
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: b5f647513b01
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: d79d4df2e15e
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: c9663c3bf0dd
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 00535360a655
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 93f7c528569e
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 37578128277a
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 003b5d690622
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 444a2a37f9b9
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: dc07adfa6d76
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 93016bfec9a1
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: f3e8bf0ea75f
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Source: GET /api/v1/institutions
# Generated: c3ced56b3e41
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_institutions_contract(client):
    """Contract: GET /api/v1/institutions matches OpenAPI schema"""

    response = client.get("/api/v1/institutions")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        400,
        404,
        422,
    ], f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/institutions
# Generated: f45b71beb7c8
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_post__api_v1_institutions_contract(client):
    """Contract: POST /api/v1/institutions matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/institutions", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/institutions/{institution_id}
# Generated: de923cd2eef0
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_institutions_institution_id_contract(client):
    """Contract: GET /api/v1/institutions/{institution_id} matches OpenAPI schema"""

    response = client.get("/api/v1/institutions/1")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/v1/institutions/{institution_id}
# Generated: fcec305644e0
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_put__api_v1_institutions_institution_id_contract(client):
    """Contract: PUT /api/v1/institutions/{institution_id} matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.put("/api/v1/institutions/1", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/accounts/{account_id}/links
# Generated: 37080e654857
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: 3d37cd705ef4
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Generated: fa7ad90df203
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
# Source: GET /api/v1/behaviour/profile
# Generated: 9e30b622bb69
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_behaviour_profile_contract(client):
    """Contract: GET /api/v1/behaviour/profile matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/profile")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/wellness-score
# Generated: f93470777353
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_behaviour_wellness_score_contract(client):
    """Contract: GET /api/v1/behaviour/wellness-score matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/wellness-score")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/debt-health
# Generated: 7e6a160e0e58
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_behaviour_debt_health_contract(client):
    """Contract: GET /api/v1/behaviour/debt-health matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/debt-health")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/cashflow-health
# Generated: f2a627cf36b7
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_behaviour_cashflow_health_contract(client):
    """Contract: GET /api/v1/behaviour/cashflow-health matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/cashflow-health")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/patterns
# Generated: b4253af0d9a9
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_behaviour_patterns_contract(client):
    """Contract: GET /api/v1/behaviour/patterns matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/patterns")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/recommendations
# Generated: 5875e881f3e9
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_behaviour_recommendations_contract(client):
    """Contract: GET /api/v1/behaviour/recommendations matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/recommendations")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/monthly-report
# Generated: 282da661ef9c
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_behaviour_monthly_report_contract(client):
    """Contract: GET /api/v1/behaviour/monthly-report matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour/monthly-report")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour
# Generated: 6d554748441e
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_behaviour_contract(client):
    """Contract: GET /api/v1/behaviour matches OpenAPI schema"""

    response = client.get("/api/v1/behaviour")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards
# Generated: c5d59fda28d4
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_credit_cards_contract(client):
    """Contract: GET /api/v1/credit-cards matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards
# Generated: 89497eb4c262
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_post__api_v1_credit_cards_contract(client):
    """Contract: POST /api/v1/credit-cards matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/credit-cards", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}
# Generated: c5049d82edbc
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id} matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards/1")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/v1/credit-cards/{card_id}
# Generated: 761f5c853979
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_put__api_v1_credit_cards_card_id_contract(client):
    """Contract: PUT /api/v1/credit-cards/{card_id} matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.put("/api/v1/credit-cards/1", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/v1/credit-cards/{card_id}
# Generated: 271c796e1135
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_delete__api_v1_credit_cards_card_id_contract(client):
    """Contract: DELETE /api/v1/credit-cards/{card_id} matches OpenAPI schema"""

    response = client.delete("/api/v1/credit-cards/1")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/statements
# Generated: 2bea87f3cab9
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_statements_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/statements matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards/1/statements")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards/{card_id}/statements
# Generated: 904ecc0f1b4b
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_post__api_v1_credit_cards_card_id_statements_contract(client):
    """Contract: POST /api/v1/credit-cards/{card_id}/statements matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/credit-cards/1/statements", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/outstanding
# Generated: daf085c1ed22
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_outstanding_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/outstanding matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards/1/outstanding")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/utilization
# Generated: 10c03ecbca1e
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_utilization_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/utilization matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards/1/utilization")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/metrics
# Generated: 48972e6d4974
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_metrics_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/metrics matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards/1/metrics")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/next-statement-date
# Generated: 99085dcfdb7b
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_next_statement_date_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/next-statement-date matches OpenAPI schema"""

    response = client.get("/api/v1/credit-cards/1/next-statement-date")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards/{card_id}/payments
# Generated: ba2df60bcaad
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_post__api_v1_credit_cards_card_id_payments_contract(client):
    """Contract: POST /api/v1/credit-cards/{card_id}/payments matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/credit-cards/1/payments", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards/{card_id}/emi-conversion
# Generated: c880f9a6e356
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_post__api_v1_credit_cards_card_id_emi_conversion_contract(client):
    """Contract: POST /api/v1/credit-cards/{card_id}/emi-conversion matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/credit-cards/1/emi-conversion", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards/{card_id}/foreclosure
# Generated: 23ece60a0853
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_post__api_v1_credit_cards_card_id_foreclosure_contract(client):
    """Contract: POST /api/v1/credit-cards/{card_id}/foreclosure matches OpenAPI schema"""

    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/credit-cards/1/foreclosure", json=request_body)

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/cashflow
# Generated: 7820da7392c8
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_cashflow_contract(client):
    """Contract: GET /api/v1/cashflow matches OpenAPI schema"""

    response = client.get("/api/v1/cashflow")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/forecast
# Generated: 53d8a5f681f2
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_forecast_contract(client):
    """Contract: GET /api/v1/forecast matches OpenAPI schema"""

    response = client.get("/api/v1/forecast")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/investments
# Generated: f376d10a5ea7
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_investments_contract(client):
    """Contract: GET /api/v1/investments matches OpenAPI schema"""

    response = client.get("/api/v1/investments")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/loans
# Generated: f491e96681d1
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_loans_contract(client):
    """Contract: GET /api/v1/loans matches OpenAPI schema"""

    response = client.get("/api/v1/loans")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/net-worth
# Generated: 74914c298732
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest


@pytest.mark.contract
def test_get__api_v1_net_worth_contract(client):
    """Contract: GET /api/v1/net-worth matches OpenAPI schema"""

    response = client.get("/api/v1/net-worth")

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [
        200,
        422,
        400,
        404,
    ], f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/reconciliation
# Generated: da76d3da9f1c
# To regenerate: python tools/generate_contract_tests.py --routers v1

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
