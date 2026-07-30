# Auto-generated contract tests for credit-cards router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards
# Generated: 437ffb070b86
# To regenerate: python tools/generate_contract_tests.py --routers credit-cards

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
# Generated: fd8bf2427952
# To regenerate: python tools/generate_contract_tests.py --routers credit-cards

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
# Generated: b642e5cb68f0
# To regenerate: python tools/generate_contract_tests.py --routers credit-cards

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
# Generated: 61e5bc89d026
# To regenerate: python tools/generate_contract_tests.py --routers credit-cards

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
# Generated: f30423f81af0
# To regenerate: python tools/generate_contract_tests.py --routers credit-cards

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
# Generated: 75ab3663b05c
# To regenerate: python tools/generate_contract_tests.py --routers credit-cards

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
# Generated: c577a14dbe3c
# To regenerate: python tools/generate_contract_tests.py --routers credit-cards

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
# Generated: 0382118983d2
# To regenerate: python tools/generate_contract_tests.py --routers credit-cards

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
# Generated: 3ebf51672f5d
# To regenerate: python tools/generate_contract_tests.py --routers credit-cards

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
# Generated: ec583460a93b
# To regenerate: python tools/generate_contract_tests.py --routers credit-cards

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
# Generated: 2ead793279f3
# To regenerate: python tools/generate_contract_tests.py --routers credit-cards

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
# Generated: f66dc7d43775
# To regenerate: python tools/generate_contract_tests.py --routers credit-cards

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
# Generated: 85be249c2d97
# To regenerate: python tools/generate_contract_tests.py --routers credit-cards

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
# Generated: 139aea4d8d38
# To regenerate: python tools/generate_contract_tests.py --routers credit-cards

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
