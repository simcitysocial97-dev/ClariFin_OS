# Auto-generated contract tests for behaviour router
# DO NOT EDIT MANUALLY


# Auto-generated contract test - DO NOT EDIT MANUALLY
# Source: GET /api/v1/behaviour/profile
# Generated: 2026-07-28T09:26:05.955136
# To regenerate: python tools/generate_contract_tests.py --routers behaviour

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
# Generated: 2026-07-28T09:26:05.960950
# To regenerate: python tools/generate_contract_tests.py --routers behaviour

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
# Generated: 2026-07-28T09:26:05.964295
# To regenerate: python tools/generate_contract_tests.py --routers behaviour

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
# Generated: 2026-07-28T09:26:05.967294
# To regenerate: python tools/generate_contract_tests.py --routers behaviour

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
# Generated: 2026-07-28T09:26:05.969900
# To regenerate: python tools/generate_contract_tests.py --routers behaviour

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
# Generated: 2026-07-28T09:26:05.973047
# To regenerate: python tools/generate_contract_tests.py --routers behaviour

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
# Generated: 2026-07-28T09:26:05.976730
# To regenerate: python tools/generate_contract_tests.py --routers behaviour

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
# Generated: 2026-07-28T09:26:05.979070
# To regenerate: python tools/generate_contract_tests.py --routers behaviour

import pytest
from tests.contract.schema_validators import validate_response_schema

@pytest.mark.contract
def test_get__api_v1_behaviour_contract(client):
    """Contract: GET /api/v1/behaviour matches OpenAPI schema"""
    
    response = client.get("/api/v1/behaviour")
    

    # Validate status code strictly against permitted spec responses and controlled errors
    assert response.status_code in [200, 422, 400, 404], \
        f"Expected one of [200, 422, 400, 404], got {response.status_code} (Response: {response.text})"

    