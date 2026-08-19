"""Tests for BehaviourService.

Verifies:
- Engine delegation (service calls correct engine functions)
- Repository integration (service uses repositories correctly)
- Error handling (service handles errors appropriately)
- Response formatting (service returns correct DTOs)
"""

from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.errors import AppError, NotFoundError
from src.models.behaviour import (
    CashflowHealthResponse,
    DebtHealthResponse,
    FinancialPattern,
    FinancialProfileResponse,
    MonthlySummaryResponse,
    WellnessScoreResponse,
)
from src.services.behaviour_service import BehaviourService

# ============================================================
# Test Fixtures
# ============================================================


@pytest.fixture
def mock_repositories() -> dict[str, Any]:
    """Create mock repositories for testing."""
    return {
        "transaction_repo": MagicMock(),
        "account_repo": MagicMock(),
        "loan_repo": MagicMock(),
        "credit_card_repo": MagicMock(),
        "behaviour_repo": MagicMock(),
        "pattern_repo": MagicMock(),
    }


@pytest.fixture
def behaviour_service(mock_repositories: dict[str, Any]) -> BehaviourService:
    """Create BehaviourService with mock repositories."""
    return BehaviourService(
        transaction_repo=mock_repositories["transaction_repo"],
        account_repo=mock_repositories["account_repo"],
        loan_repo=mock_repositories["loan_repo"],
        credit_card_repo=mock_repositories["credit_card_repo"],
        behaviour_repo=mock_repositories["behaviour_repo"],
        pattern_repo=mock_repositories["pattern_repo"],
    )


@pytest.fixture
def sample_transactions() -> list[dict[str, Any]]:
    """Sample transactions for testing."""
    return [
        {
            "id": 1,
            "date_iso": "2023-01-15",
            "description": "Salary credit",
            "amount_paise": 5000000,
            "type": "credit",
            "category": "income",
        },
        {
            "id": 2,
            "date_iso": "2023-01-16",
            "description": "Rent payment",
            "amount_paise": 2000000,
            "type": "debit",
            "category": "rent",
        },
        {
            "id": 3,
            "date_iso": "2023-01-17",
            "description": "Grocery shopping",
            "amount_paise": 500000,
            "type": "debit",
            "category": "groceries",
        },
    ]


@pytest.fixture
def sample_snapshot() -> dict[str, Any]:
    """Sample behaviour snapshot for testing - matches repository output format.

    Repository _map_snapshot_row returns scores multiplied by 100 for all fields.
    For stability scores (0-1 range models), we need to provide values in 0-100 range
    because the repository converts bps to decimal * 100.
    """
    return {
        "id": 1,
        "snapshot_date": "2023-01-15",
        "household_id": "default",
        "version": 1,
        "created_at": "2023-01-15",
        # Repository returns Decimal values times 100
        # For wellness_score (0-100 model range), this is correct
        # For cashflow_stability_score (0-1 model range), this needs adjustment in service
        "savings_discipline_score": Decimal("72.00"),  # 0-100 range for model
        "cashflow_stability_score": Decimal(
            "80.00"
        ),  # Repository returns * 100, but model expects 0-1
        "salary_dependence_ratio": Decimal("90.00"),
        "lifestyle_inflation_rate": Decimal("5.00"),
        "subscription_burn_rate": Decimal("10.00"),
        "resilience_index": Decimal("65.00"),
        "wellness_score": Decimal("80.00"),  # 80 for "Healthy" band (>= 75)
        "debt_cycle_score": 40,
        "credit_dependency_ratio": Decimal("50.00"),
        "credit_revolver_ratio": Decimal("20.00"),
        "income_stability_score": Decimal("80.00"),  # Repository returns * 100
        "expense_stability_score": Decimal("75.00"),  # Repository returns * 100
    }


@pytest.fixture
def sample_patterns() -> list[dict[str, Any]]:
    """Sample financial patterns for testing."""
    return [
        {
            "id": 1,
            "pattern_type": "IMPULSE",
            "pattern_key": "Amazon",
            "strength_bps": 8000,
            "transaction_count": 5,
            "total_amount_paise": 250000,
            "first_observed": "2023-01-01",
            "last_observed": "2023-01-15",
        }
    ]


# ============================================================
# Tests: Financial Profile
# ============================================================


def test_compute_financial_profile_success(
    behaviour_service: BehaviourService,
    mock_repositories: dict[str, Any],
    sample_transactions: list[dict[str, Any]],
) -> None:
    """Test successful financial profile computation."""
    # Setup mocks
    mock_repositories["transaction_repo"].get_all_transactions.return_value = (
        sample_transactions
    )
    mock_repositories["account_repo"].get_all_accounts.return_value = [
        {"id": 1, "balance_paise": 1000000, "account_type": "savings"}
    ]
    mock_repositories["loan_repo"].list_loans.return_value = []
    mock_repositories["credit_card_repo"].list_cards.return_value = []
    mock_repositories["behaviour_repo"].create_snapshot.return_value = {
        "id": 1,
        "snapshot_date": "2023-01-15",
    }

    # Mock behaviour engine functions
    with patch(
        "src.services.behaviour_service.classify_financial_personality"
    ) as mock_classify:
        mock_classify.return_value = (
            "SAVER",
            Decimal("0.85"),
            "High savings rate detected",
        )

        # Call service method
        result = behaviour_service.compute_financial_profile()

        # Verify result
        assert isinstance(result, FinancialProfileResponse)
        assert result.profile_type == "SAVER"
        assert result.confidence == Decimal("0.85")
        # snapshot_date is dynamically generated, just check it's a valid date string
        assert result.snapshot_date is not None
        assert len(result.snapshot_date) == 10  # YYYY-MM-DD format

        # Verify repository calls
        mock_repositories["transaction_repo"].get_all_transactions.assert_called_once()
        mock_repositories["account_repo"].get_all_accounts.assert_called_once()
        mock_repositories["loan_repo"].list_loans.assert_called_once()
        mock_repositories["credit_card_repo"].list_cards.assert_called_once()
        mock_repositories["behaviour_repo"].create_snapshot.assert_called_once()


def test_compute_financial_profile_insufficient_data(
    behaviour_service: BehaviourService, mock_repositories: dict[str, Any]
) -> None:
    """Test financial profile computation with insufficient data."""
    # Setup mocks
    mock_repositories["transaction_repo"].get_all_transactions.return_value = []

    # Call service method
    result = behaviour_service.compute_financial_profile()

    # Verify result
    assert isinstance(result, FinancialProfileResponse)
    assert result.profile_type == "INSUFFICIENT_DATA"
    assert result.confidence == Decimal("0")
    assert "Insufficient transaction data" in result.explanation


def test_compute_financial_profile_error(
    behaviour_service: BehaviourService,
    mock_repositories: dict[str, Any],
    sample_transactions: list[dict[str, Any]],
) -> None:
    """Test financial profile computation with engine error."""
    # Setup mocks
    mock_repositories["transaction_repo"].get_all_transactions.return_value = (
        sample_transactions
    )
    mock_repositories["account_repo"].get_all_accounts.return_value = []

    # Mock behaviour engine to raise error
    with patch(
        "src.services.behaviour_service.compute_true_savings_rate",
        side_effect=ValueError("Test error"),
    ):
        # Call service method and verify error
        with pytest.raises(AppError) as exc_info:
            behaviour_service.compute_financial_profile()

        assert "Failed to compute financial profile" in str(exc_info.value.message)


def test_get_wellness_score_success(
    behaviour_service: BehaviourService,
    mock_repositories: dict[str, Any],
    sample_snapshot: dict[str, Any],
) -> None:
    """Test successful wellness score retrieval."""
    # Setup mocks - use wellness_score 80.00 for "Healthy" band
    mock_repositories["behaviour_repo"].get_latest_snapshot.return_value = {
        **sample_snapshot,
        "wellness_score": Decimal("80.00"),  # Healthy band: 75-89
    }

    # Call service method
    result = behaviour_service.get_wellness_score()

    # Verify result
    assert isinstance(result, WellnessScoreResponse)
    assert result.score == Decimal("80.00")
    assert result.band == "Healthy"
    assert "cashflow_health" in result.components
    assert result.snapshot_date == "2023-01-15"
    assert result.version == 1


def test_get_wellness_score_not_found(
    behaviour_service: BehaviourService, mock_repositories: dict[str, Any]
) -> None:
    """Test wellness score retrieval when no snapshot exists — falls back to on-demand computation."""
    # Setup mocks: no snapshot, empty transactions
    mock_repositories["behaviour_repo"].get_latest_snapshot.return_value = None
    mock_repositories["transaction_repo"].get_all_transactions.return_value = []
    mock_repositories["account_repo"].get_all_accounts.return_value = []
    mock_repositories["loan_repo"].list_loans.return_value = []
    mock_repositories["credit_card_repo"].list_cards.return_value = []

    # Call service method — should compute on-demand, not raise NotFoundError
    result = behaviour_service.get_wellness_score()

    # Verify result has default/fallback values when no data
    assert result is not None
    assert hasattr(result, 'score')


def test_get_debt_health_success(
    behaviour_service: BehaviourService,
    mock_repositories: dict[str, Any],
    sample_snapshot: dict[str, Any],
    sample_transactions: list[dict[str, Any]],
) -> None:
    """Test successful debt health retrieval."""
    # Setup mocks
    mock_repositories["behaviour_repo"].get_latest_snapshot.return_value = (
        sample_snapshot
    )
    mock_repositories["transaction_repo"].get_all_transactions.return_value = (
        sample_transactions
    )
    mock_repositories["credit_card_repo"].list_cards.return_value = []
    mock_repositories["loan_repo"].list_loans.return_value = []

    # Mock behaviour engine functions
    with patch("src.services.behaviour_service.compute_foir") as mock_foir:
        mock_foir.return_value = (Decimal("0.35"), "MODERATE")

        # Call service method
        result = behaviour_service.get_debt_health()

        # Verify result
        assert isinstance(result, DebtHealthResponse)
        assert result.foir == Decimal("0.35")
        assert result.band == "MODERATE"
        assert result.snapshot_date == "2023-01-15"


def test_get_cashflow_health_success(
    behaviour_service: BehaviourService,
    mock_repositories: dict[str, Any],
    sample_snapshot: dict[str, Any],
    sample_transactions: list[dict[str, Any]],
) -> None:
    """Test successful cashflow health retrieval."""
    # Setup mocks
    mock_repositories["behaviour_repo"].get_latest_snapshot.return_value = (
        sample_snapshot
    )
    mock_repositories["transaction_repo"].get_all_transactions.return_value = (
        sample_transactions
    )

    # Call service method
    result = behaviour_service.get_cashflow_health()

    # Verify result - cashflow_stability_score is returned as * 100 by repository
    assert isinstance(result, CashflowHealthResponse)
    assert result.cashflow_stability_index == Decimal(
        "80.00"
    )  # Repository returns * 100
    assert result.snapshot_date == "2023-01-15"


def test_get_patterns_success(
    behaviour_service: BehaviourService,
    mock_repositories: dict[str, Any],
    sample_patterns: list[dict[str, Any]],
) -> None:
    """Test successful pattern retrieval."""
    # Setup mocks
    mock_repositories["pattern_repo"].get_recent_patterns.return_value = sample_patterns

    # Call service method
    result = behaviour_service.get_patterns()

    # Verify result
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], FinancialPattern)
    assert result[0].pattern_type == "IMPULSE"
    assert result[0].pattern_key == "Amazon"
    assert result[0].strength == Decimal("0.80")


def test_generate_monthly_summary_success(
    behaviour_service: BehaviourService,
    mock_repositories: dict[str, Any],
    sample_snapshot: dict[str, Any],
    sample_patterns: list[dict[str, Any]],
) -> None:
    """Test successful monthly summary generation."""
    # Setup mocks
    mock_repositories["behaviour_repo"].get_snapshots_by_date_range.return_value = [
        sample_snapshot
    ]
    mock_repositories["pattern_repo"].get_recent_patterns.return_value = sample_patterns
    mock_repositories["transaction_repo"].get_all_transactions.return_value = [
        {
            "id": 1,
            "date_iso": "2023-01-15",
            "description": "Salary credit",
            "amount_paise": 5000000,
            "type": "credit",
        },
        {
            "id": 2,
            "date_iso": "2023-01-16",
            "description": "Rent payment",
            "amount_paise": 2000000,
            "type": "debit",
        },
    ]

    # Call service method
    result = behaviour_service.generate_monthly_summary("2023-01")

    # Verify result
    assert isinstance(result, MonthlySummaryResponse)
    assert result.period == "2023-01"
    assert isinstance(result.wellness_score, WellnessScoreResponse)
    assert isinstance(result.debt_health, DebtHealthResponse)
    assert isinstance(result.cashflow_health, CashflowHealthResponse)
    assert len(result.top_patterns) == 1
    assert result.total_income_paise == 5000000
    assert result.total_expenses_paise == 2000000


def test_dependency_injection() -> None:
    """Test that repositories can be injected."""
    mock_transaction_repo = MagicMock()
    mock_behaviour_repo = MagicMock()

    service = BehaviourService(
        transaction_repo=mock_transaction_repo,
        behaviour_repo=mock_behaviour_repo,
    )

    assert service.transaction_repo == mock_transaction_repo
    assert service.behaviour_repo == mock_behaviour_repo


def test_snapshot_versioning(
    behaviour_service: BehaviourService,
    mock_repositories: dict[str, Any],
    sample_transactions: list[dict[str, Any]],
) -> None:
    """Test that snapshots are created with version 1."""
    # Setup mocks
    mock_repositories["transaction_repo"].get_all_transactions.return_value = (
        sample_transactions
    )
    mock_repositories["account_repo"].get_all_accounts.return_value = []
    mock_repositories["loan_repo"].list_loans.return_value = []
    mock_repositories["credit_card_repo"].list_cards.return_value = []
    mock_repositories["behaviour_repo"].create_snapshot.return_value = {"id": 1}

    # Mock behaviour engine functions
    with patch(
        "src.services.behaviour_service.classify_financial_personality"
    ) as mock_classify:
        mock_classify.return_value = ("SAVER", Decimal("0.85"), "High savings rate")

        # Call service method
        behaviour_service.compute_financial_profile()

        # Verify snapshot creation with version 1
        snapshot_data = mock_repositories["behaviour_repo"].create_snapshot.call_args[
            0
        ][0]
        assert snapshot_data["version"] == 1


def test_error_handling(
    behaviour_service: BehaviourService,
    mock_repositories: dict[str, Any],
    sample_transactions: list[dict[str, Any]],
) -> None:
    """Test error handling in service methods."""
    # Test repository error
    mock_repositories["transaction_repo"].get_all_transactions.side_effect = Exception(
        "DB error"
    )

    with pytest.raises(AppError) as exc_info:
        behaviour_service.compute_financial_profile()

    assert "Failed to compute financial profile" in str(exc_info.value.message)
