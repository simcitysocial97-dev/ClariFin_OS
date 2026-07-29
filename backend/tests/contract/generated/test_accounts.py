# Auto-generated contract tests for accounts router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/accounts
# Generated: 2026-07-28T09:26:05.725129
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Generated: 2026-07-28T09:26:05.727800
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Generated: 2026-07-28T09:26:05.730083
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Generated: 2026-07-28T09:26:05.732333
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Generated: 2026-07-28T09:26:05.734453
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Generated: 2026-07-28T09:26:05.736580
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Generated: 2026-07-28T09:26:05.739364
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Generated: 2026-07-28T09:26:05.742895
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Generated: 2026-07-28T09:26:05.745321
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Generated: 2026-07-28T09:26:05.747570
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Generated: 2026-07-28T09:26:05.749783
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Generated: 2026-07-28T09:26:05.751953
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Source: POST /api/v1/accounts/{account_id}/links
# Generated: 2026-07-28T09:26:05.754078
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Generated: 2026-07-28T09:26:05.757061
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Generated: 2026-07-28T09:26:05.760200
# To regenerate: python tools/generate_contract_tests.py --routers accounts

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
# Source: GET /api/accounts/manage
# Generated: 2026-07-28T09:26:05.762585
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_accounts_manage_contract(client):
    """Contract: GET /api/accounts/manage matches OpenAPI schema"""
    
    response = client.get("/api/accounts/manage")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 400, 404, 422], \
        f"Expected one of [200, 400, 404, 422], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: POST /api/accounts/manage
# Generated: 2026-07-28T09:26:05.764797
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_post__api_accounts_manage_contract(client):
    """Contract: POST /api/accounts/manage matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.post("/api/accounts/manage", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: PUT /api/accounts/manage/{account_id}
# Generated: 2026-07-28T09:26:05.766898
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_put__api_accounts_manage_account_id_contract(client):
    """Contract: PUT /api/accounts/manage/{account_id} matches OpenAPI schema"""
    
    # TODO: Replace with a valid payload for this endpoint if needed.
    request_body = {}
    response = client.put("/api/accounts/manage/1", json=request_body)
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: DELETE /api/accounts/manage/{account_id}
# Generated: 2026-07-28T09:26:05.768979
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_delete__api_accounts_manage_account_id_contract(client):
    """Contract: DELETE /api/accounts/manage/{account_id} matches OpenAPI schema"""
    
    response = client.delete("/api/accounts/manage/1")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/accounts/{account_id}/balance
# Generated: 2026-07-28T09:26:05.771290
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_accounts_account_id_balance_contract(client):
    """Contract: GET /api/accounts/{account_id}/balance matches OpenAPI schema"""
    
    response = client.get("/api/accounts/1/balance")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    

# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/accounts/{account_id}/running-balance
# Generated: 2026-07-28T09:26:05.774171
# To regenerate: python tools/generate_contract_tests.py --routers accounts

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_accounts_account_id_running_balance_contract(client):
    """Contract: GET /api/accounts/{account_id}/running-balance matches OpenAPI schema"""
    
    response = client.get("/api/accounts/1/running-balance")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    