"""Tests for BehaviourRepository."""

import os
import tempfile
from decimal import Decimal

import pytest

from src.repositories.behaviour_repository import BehaviourRepository


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name

    # Initialize the database with the required tables
    repo = BehaviourRepository(db_path)
    conn = repo._get_conn()

    # Create tables
    conn.execute("""
        CREATE TABLE behaviour_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date TEXT NOT NULL,
            household_id TEXT NOT NULL DEFAULT 'default',
            savings_discipline_score_bps INTEGER NOT NULL,
            cashflow_stability_score_bps INTEGER NOT NULL,
            salary_dependence_ratio_bps INTEGER NOT NULL,
            lifestyle_inflation_rate_bps INTEGER NOT NULL,
            subscription_burn_rate_bps INTEGER NOT NULL,
            resilience_index_bps INTEGER NOT NULL,
            wellness_score_bps INTEGER NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()

    yield db_path

    # Clean up
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture
def behaviour_repo(temp_db):
    """Create a BehaviourRepository instance for testing."""
    return BehaviourRepository(temp_db)

def test_create_and_get_snapshot(behaviour_repo):
    """Test creating and retrieving a behaviour snapshot."""
    snapshot_data = {
        'snapshot_date': '2023-01-15',
        'savings_discipline_score_bps': 7500,  # 75.00%
        'cashflow_stability_score_bps': 8200,  # 82.00%
        'salary_dependence_ratio_bps': 6500,   # 65.00%
        'lifestyle_inflation_rate_bps': 500,   # 5.00%
        'subscription_burn_rate_bps': 2500,    # 25.00%
        'resilience_index_bps': 6800,          # 68.00%
        'wellness_score_bps': 7200,            # 72.00%
        'version': 1
    }

    # Create snapshot
    created = behaviour_repo.create_snapshot(snapshot_data)
    assert created is not None
    assert created['id'] is not None
    assert created['snapshot_date'] == '2023-01-15'
    assert created['savings_discipline_score'] == Decimal('75.00')
    assert created['cashflow_stability_score'] == Decimal('82.00')
    assert created['wellness_score'] == Decimal('72.00')

    # Get snapshot by ID
    retrieved = behaviour_repo.get_snapshot_by_id(created['id'])
    assert retrieved is not None
    assert retrieved['id'] == created['id']
    assert retrieved['snapshot_date'] == '2023-01-15'
    assert retrieved['savings_discipline_score'] == Decimal('75.00')

def test_get_latest_snapshot(behaviour_repo):
    """Test retrieving the latest snapshot."""
    # Create multiple snapshots
    dates = ['2023-01-01', '2023-01-15', '2023-02-01']
    for i, date in enumerate(dates):
        behaviour_repo.create_snapshot({
            'snapshot_date': date,
            'savings_discipline_score_bps': 7000 + i * 100,
            'cashflow_stability_score_bps': 8000 + i * 100,
            'salary_dependence_ratio_bps': 6000 + i * 100,
            'lifestyle_inflation_rate_bps': 500 + i * 100,
            'subscription_burn_rate_bps': 2000 + i * 100,
            'resilience_index_bps': 6500 + i * 100,
            'wellness_score_bps': 7000 + i * 100,
            'version': 1
        })

    # Get latest snapshot
    latest = behaviour_repo.get_latest_snapshot()
    assert latest is not None
    assert latest['snapshot_date'] == '2023-02-01'
    assert latest['wellness_score'] == Decimal('72.00')

def test_get_snapshots_by_date_range(behaviour_repo):
    """Test retrieving snapshots within a date range."""
    # Create snapshots with different dates
    dates = ['2023-01-01', '2023-01-15', '2023-02-01', '2023-03-01']
    for _i, date in enumerate(dates):
        behaviour_repo.create_snapshot({
            'snapshot_date': date,
            'savings_discipline_score_bps': 7000,
            'cashflow_stability_score_bps': 8000,
            'salary_dependence_ratio_bps': 6000,
            'lifestyle_inflation_rate_bps': 500,
            'subscription_burn_rate_bps': 2000,
            'resilience_index_bps': 6500,
            'wellness_score_bps': 7000,
            'version': 1
        })

    # Get snapshots in range
    snapshots = behaviour_repo.get_snapshots_by_date_range('2023-01-10', '2023-02-10')
    assert len(snapshots) == 2
    assert snapshots[0]['snapshot_date'] == '2023-01-15'
    assert snapshots[1]['snapshot_date'] == '2023-02-01'

def test_get_snapshot_trends(behaviour_repo):
    """Test retrieving trend data for a metric."""
    # Create snapshots with different scores
    dates = ['2023-01-01', '2023-01-15', '2023-02-01']
    for i, date in enumerate(dates):
        behaviour_repo.create_snapshot({
            'snapshot_date': date,
            'savings_discipline_score_bps': 7000 + i * 500,  # 70.00, 75.00, 80.00
            'cashflow_stability_score_bps': 8000,
            'salary_dependence_ratio_bps': 6000,
            'lifestyle_inflation_rate_bps': 500,
            'subscription_burn_rate_bps': 2000,
            'resilience_index_bps': 6500,
            'wellness_score_bps': 7000,
            'version': 1
        })

    # Get trends for savings discipline
    trends = behaviour_repo.get_snapshot_trends('savings_discipline_score_bps', months=2)
    assert len(trends) == 3
    assert trends[0]['metric_value'] == Decimal('70.00')
    assert trends[1]['metric_value'] == Decimal('75.00')
    assert trends[2]['metric_value'] == Decimal('80.00')
    assert trends[0]['metric_name'] == 'savings_discipline_score'

def test_bps_conversion(behaviour_repo):
    """Test basis points conversion methods."""
    # Test decimal to bps
    assert behaviour_repo._decimal_to_bps(Decimal('0.75')) == 7500
    assert behaviour_repo._decimal_to_bps(Decimal('1.00')) == 10000
    assert behaviour_repo._decimal_to_bps(Decimal('0.00')) == 0

    # Test bps to decimal
    assert behaviour_repo._bps_to_decimal(7500) == Decimal('0.75')
    assert behaviour_repo._bps_to_decimal(10000) == Decimal('1.00')
    assert behaviour_repo._bps_to_decimal(0) == Decimal('0.00')

def test_household_id_handling(behaviour_repo):
    """Test handling of household_id parameter."""
    # Create snapshot with default household
    behaviour_repo.create_snapshot({
        'snapshot_date': '2023-01-01',
        'savings_discipline_score_bps': 7000,
        'cashflow_stability_score_bps': 8000,
        'salary_dependence_ratio_bps': 6000,
        'lifestyle_inflation_rate_bps': 500,
        'subscription_burn_rate_bps': 2000,
        'resilience_index_bps': 6500,
        'wellness_score_bps': 7000,
        'version': 1
    })

    # Create snapshot with specific household
    behaviour_repo.create_snapshot({
        'snapshot_date': '2023-01-01',
        'household_id': 'household_123',
        'savings_discipline_score_bps': 7500,
        'cashflow_stability_score_bps': 8500,
        'salary_dependence_ratio_bps': 6500,
        'lifestyle_inflation_rate_bps': 1000,
        'subscription_burn_rate_bps': 2500,
        'resilience_index_bps': 7000,
        'wellness_score_bps': 7500,
        'version': 1
    })

    # Test default household
    default_latest = behaviour_repo.get_latest_snapshot()
    assert default_latest is not None
    assert default_latest['household_id'] == 'default'

    # Test specific household
    household_latest = behaviour_repo.get_latest_snapshot('household_123')
    assert household_latest is not None
    assert household_latest['household_id'] == 'household_123'
    assert household_latest['wellness_score'] == Decimal('75.00')
