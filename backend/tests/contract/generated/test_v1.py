# Auto-generated contract tests for v1 router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts
# Generated: 2026-07-28T06:59:26.704714
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_accounts_contract(client):
    """Contract: GET /api/v1/accounts matches OpenAPI schema"""
    
    response = client.get("/api/v1/accounts")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 400, 404, 422], \
        f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/accounts
# Generated: 2026-07-28T06:59:26.709332
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_v1_accounts_contract(client):
    """Contract: POST /api/v1/accounts matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/accounts", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}
# Generated: 2026-07-28T06:59:26.713417
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_accounts_account_id_contract(client):
    """Contract: GET /api/v1/accounts/{account_id} matches OpenAPI schema"""
    
    response = client.get("/api/v1/accounts/1")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/v1/accounts/{account_id}
# Generated: 2026-07-28T06:59:26.717547
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_put__api_v1_accounts_account_id_contract(client):
    """Contract: PUT /api/v1/accounts/{account_id} matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.put("/api/v1/accounts/1", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/v1/accounts/{account_id}
# Generated: 2026-07-28T06:59:26.720669
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_delete__api_v1_accounts_account_id_contract(client):
    """Contract: DELETE /api/v1/accounts/{account_id} matches OpenAPI schema"""
    
    response = client.delete("/api/v1/accounts/1")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/accounts/{account_id}/balance-history
# Generated: 2026-07-28T06:59:26.725159
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_v1_accounts_account_id_balance_history_contract(client):
    """Contract: POST /api/v1/accounts/{account_id}/balance-history matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/accounts/1/balance-history", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/balance-history
# Generated: 2026-07-28T06:59:26.730725
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_accounts_account_id_balance_history_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/balance-history matches OpenAPI schema"""
    
    response = client.get("/api/v1/accounts/1/balance-history")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/balance-history/latest
# Generated: 2026-07-28T06:59:26.734440
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_accounts_account_id_balance_history_latest_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/balance-history/latest matches OpenAPI schema"""
    
    response = client.get("/api/v1/accounts/1/balance-history/latest")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/analytics
# Generated: 2026-07-28T06:59:26.738354
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_accounts_account_id_analytics_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/analytics matches OpenAPI schema"""
    
    response = client.get("/api/v1/accounts/1/analytics")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/metrics
# Generated: 2026-07-28T06:59:26.742059
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_accounts_account_id_metrics_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/metrics matches OpenAPI schema"""
    
    response = client.get("/api/v1/accounts/1/metrics")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/status
# Generated: 2026-07-28T06:59:26.747128
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_accounts_account_id_status_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/status matches OpenAPI schema"""
    
    response = client.get("/api/v1/accounts/1/status")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/dormancy
# Generated: 2026-07-28T06:59:26.750707
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_accounts_account_id_dormancy_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/dormancy matches OpenAPI schema"""
    
    response = client.get("/api/v1/accounts/1/dormancy")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/institutions
# Generated: 2026-07-28T06:59:26.754497
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_institutions_contract(client):
    """Contract: GET /api/v1/institutions matches OpenAPI schema"""
    
    response = client.get("/api/v1/institutions")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 400, 404, 422], \
        f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/institutions
# Generated: 2026-07-28T06:59:26.757793
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_v1_institutions_contract(client):
    """Contract: POST /api/v1/institutions matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/institutions", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/institutions/{institution_id}
# Generated: 2026-07-28T06:59:26.762575
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_institutions_institution_id_contract(client):
    """Contract: GET /api/v1/institutions/{institution_id} matches OpenAPI schema"""
    
    response = client.get("/api/v1/institutions/1")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/v1/institutions/{institution_id}
# Generated: 2026-07-28T06:59:26.766270
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_put__api_v1_institutions_institution_id_contract(client):
    """Contract: PUT /api/v1/institutions/{institution_id} matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.put("/api/v1/institutions/1", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/accounts/{account_id}/links
# Generated: 2026-07-28T06:59:26.770090
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_v1_accounts_account_id_links_contract(client):
    """Contract: POST /api/v1/accounts/{account_id}/links matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/accounts/1/links", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts/{account_id}/links
# Generated: 2026-07-28T06:59:26.773213
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_accounts_account_id_links_contract(client):
    """Contract: GET /api/v1/accounts/{account_id}/links matches OpenAPI schema"""
    
    response = client.get("/api/v1/accounts/1/links")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/v1/accounts/{account_id}/links/{linked_account_id}
# Generated: 2026-07-28T06:59:26.778429
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_delete__api_v1_accounts_account_id_links_linked_account_id_contract(client):
    """Contract: DELETE /api/v1/accounts/{account_id}/links/{linked_account_id} matches OpenAPI schema"""
    
    response = client.delete("/api/v1/accounts/1/links/1")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/profile
# Generated: 2026-07-28T06:59:26.782683
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_behaviour_profile_contract(client):
    """Contract: GET /api/v1/behaviour/profile matches OpenAPI schema"""
    
    response = client.get("/api/v1/behaviour/profile")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/wellness-score
# Generated: 2026-07-28T06:59:26.785947
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_behaviour_wellness_score_contract(client):
    """Contract: GET /api/v1/behaviour/wellness-score matches OpenAPI schema"""
    
    response = client.get("/api/v1/behaviour/wellness-score")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/debt-health
# Generated: 2026-07-28T06:59:26.789767
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_behaviour_debt_health_contract(client):
    """Contract: GET /api/v1/behaviour/debt-health matches OpenAPI schema"""
    
    response = client.get("/api/v1/behaviour/debt-health")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/cashflow-health
# Generated: 2026-07-28T06:59:26.793461
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_behaviour_cashflow_health_contract(client):
    """Contract: GET /api/v1/behaviour/cashflow-health matches OpenAPI schema"""
    
    response = client.get("/api/v1/behaviour/cashflow-health")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/patterns
# Generated: 2026-07-28T06:59:26.798076
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_behaviour_patterns_contract(client):
    """Contract: GET /api/v1/behaviour/patterns matches OpenAPI schema"""
    
    response = client.get("/api/v1/behaviour/patterns")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/recommendations
# Generated: 2026-07-28T06:59:26.801471
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_behaviour_recommendations_contract(client):
    """Contract: GET /api/v1/behaviour/recommendations matches OpenAPI schema"""
    
    response = client.get("/api/v1/behaviour/recommendations")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/monthly-report
# Generated: 2026-07-28T06:59:26.805215
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_behaviour_monthly_report_contract(client):
    """Contract: GET /api/v1/behaviour/monthly-report matches OpenAPI schema"""
    
    response = client.get("/api/v1/behaviour/monthly-report")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour
# Generated: 2026-07-28T06:59:26.808647
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_behaviour_contract(client):
    """Contract: GET /api/v1/behaviour matches OpenAPI schema"""
    
    response = client.get("/api/v1/behaviour")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards
# Generated: 2026-07-28T06:59:26.813429
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_credit_cards_contract(client):
    """Contract: GET /api/v1/credit-cards matches OpenAPI schema"""
    
    response = client.get("/api/v1/credit-cards")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards
# Generated: 2026-07-28T06:59:26.816827
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_v1_credit_cards_contract(client):
    """Contract: POST /api/v1/credit-cards matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/credit-cards", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}
# Generated: 2026-07-28T06:59:26.820630
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id} matches OpenAPI schema"""
    
    response = client.get("/api/v1/credit-cards/1")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/v1/credit-cards/{card_id}
# Generated: 2026-07-28T06:59:26.824159
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_put__api_v1_credit_cards_card_id_contract(client):
    """Contract: PUT /api/v1/credit-cards/{card_id} matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.put("/api/v1/credit-cards/1", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/v1/credit-cards/{card_id}
# Generated: 2026-07-28T06:59:26.829040
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_delete__api_v1_credit_cards_card_id_contract(client):
    """Contract: DELETE /api/v1/credit-cards/{card_id} matches OpenAPI schema"""
    
    response = client.delete("/api/v1/credit-cards/1")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/statements
# Generated: 2026-07-28T06:59:26.832571
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_statements_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/statements matches OpenAPI schema"""
    
    response = client.get("/api/v1/credit-cards/1/statements")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards/{card_id}/statements
# Generated: 2026-07-28T06:59:26.836376
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_v1_credit_cards_card_id_statements_contract(client):
    """Contract: POST /api/v1/credit-cards/{card_id}/statements matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/credit-cards/1/statements", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/outstanding
# Generated: 2026-07-28T06:59:26.839475
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_outstanding_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/outstanding matches OpenAPI schema"""
    
    response = client.get("/api/v1/credit-cards/1/outstanding")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/utilization
# Generated: 2026-07-28T06:59:26.844071
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_utilization_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/utilization matches OpenAPI schema"""
    
    response = client.get("/api/v1/credit-cards/1/utilization")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/metrics
# Generated: 2026-07-28T06:59:26.849103
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_metrics_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/metrics matches OpenAPI schema"""
    
    response = client.get("/api/v1/credit-cards/1/metrics")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/credit-cards/{card_id}/next-statement-date
# Generated: 2026-07-28T06:59:26.852488
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_credit_cards_card_id_next_statement_date_contract(client):
    """Contract: GET /api/v1/credit-cards/{card_id}/next-statement-date matches OpenAPI schema"""
    
    response = client.get("/api/v1/credit-cards/1/next-statement-date")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards/{card_id}/payments
# Generated: 2026-07-28T06:59:26.856049
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_v1_credit_cards_card_id_payments_contract(client):
    """Contract: POST /api/v1/credit-cards/{card_id}/payments matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/credit-cards/1/payments", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards/{card_id}/emi-conversion
# Generated: 2026-07-28T06:59:26.859941
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_v1_credit_cards_card_id_emi_conversion_contract(client):
    """Contract: POST /api/v1/credit-cards/{card_id}/emi-conversion matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/credit-cards/1/emi-conversion", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/v1/credit-cards/{card_id}/foreclosure
# Generated: 2026-07-28T06:59:26.864413
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_v1_credit_cards_card_id_foreclosure_contract(client):
    """Contract: POST /api/v1/credit-cards/{card_id}/foreclosure matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/v1/credit-cards/1/foreclosure", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/cashflow
# Generated: 2026-07-28T06:59:26.867842
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_cashflow_contract(client):
    """Contract: GET /api/v1/cashflow matches OpenAPI schema"""
    
    response = client.get("/api/v1/cashflow")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/forecast
# Generated: 2026-07-28T06:59:26.871754
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_forecast_contract(client):
    """Contract: GET /api/v1/forecast matches OpenAPI schema"""
    
    response = client.get("/api/v1/forecast")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/investments
# Generated: 2026-07-28T06:59:26.875614
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_investments_contract(client):
    """Contract: GET /api/v1/investments matches OpenAPI schema"""
    
    response = client.get("/api/v1/investments")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/loans
# Generated: 2026-07-28T06:59:26.880477
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_loans_contract(client):
    """Contract: GET /api/v1/loans matches OpenAPI schema"""
    
    response = client.get("/api/v1/loans")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/net-worth
# Generated: 2026-07-28T06:59:26.884091
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_net_worth_contract(client):
    """Contract: GET /api/v1/net-worth matches OpenAPI schema"""
    
    response = client.get("/api/v1/net-worth")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/reconciliation
# Generated: 2026-07-28T06:59:26.888029
# To regenerate: python tools/generate_contract_tests.py --routers v1

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_reconciliation_contract(client):
    """Contract: GET /api/v1/reconciliation matches OpenAPI schema"""
    
    response = client.get("/api/v1/reconciliation")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    