"""Tests for PatternRepository."""

import os
import tempfile
from decimal import Decimal

import pytest

from src.repositories.pattern_repository import PatternRepository


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name

    # Initialize the database with the required tables
    repo = PatternRepository(db_path)
    conn = repo._get_conn()

    # Create tables
    conn.execute("""
        CREATE TABLE behaviour_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT NOT NULL,
            pattern_key TEXT NOT NULL,
            household_id TEXT NOT NULL DEFAULT 'default',
            strength_bps INTEGER NOT NULL,
            first_observed TEXT NOT NULL,
            last_observed TEXT NOT NULL,
            transaction_count INTEGER NOT NULL,
            total_amount_paise INTEGER NOT NULL,
            config_json TEXT,
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
def pattern_repo(temp_db):
    """Create a PatternRepository instance for testing."""
    return PatternRepository(temp_db)


def test_create_and_get_pattern(pattern_repo):
    """Test creating and retrieving a behaviour pattern."""
    pattern_data = {
        "pattern_type": "IMPULSE",
        "pattern_key": "amazon",
        "strength_bps": 8500,  # 85.00%
        "first_observed": "2023-01-01",
        "last_observed": "2023-01-15",
        "transaction_count": 5,
        "total_amount_paise": 150000,  # ₹1500.00
        "config": {
            "time_window": "weekend",
            "amount_range": [50000, 200000],  # ₹500-₹2000
            "categories": ["Shopping"],
        },
    }

    # Create pattern
    created = pattern_repo.create_pattern(pattern_data)
    assert created is not None
    assert created["id"] is not None
    assert created["pattern_type"] == "IMPULSE"
    assert created["pattern_key"] == "amazon"
    assert created["strength"] == Decimal("85.00")
    assert created["transaction_count"] == 5
    assert created["total_amount"] == Decimal("1500.00")
    assert created["config"]["time_window"] == "weekend"

    # Get pattern by ID
    retrieved = pattern_repo.get_pattern_by_id(created["id"])
    assert retrieved is not None
    assert retrieved["id"] == created["id"]
    assert retrieved["strength"] == Decimal("85.00")
    assert retrieved["config"]["categories"] == ["Shopping"]


def test_get_pattern_by_key(pattern_repo):
    """Test retrieving a pattern by type and key."""
    # Create pattern
    pattern_repo.create_pattern(
        {
            "pattern_type": "SUBSCRIPTION",
            "pattern_key": "netflix",
            "strength_bps": 9500,  # 95.00%
            "first_observed": "2023-01-01",
            "last_observed": "2023-01-15",
            "transaction_count": 3,
            "total_amount_paise": 99900,  # ₹999.00
            "config": {"frequency": "monthly", "amount_variance": 0.05},
        }
    )

    # Get pattern by key
    pattern = pattern_repo.get_pattern_by_key("SUBSCRIPTION", "netflix")
    assert pattern is not None
    assert pattern["pattern_type"] == "SUBSCRIPTION"
    assert pattern["pattern_key"] == "netflix"
    assert pattern["strength"] == Decimal("95.00")
    assert pattern["total_amount"] == Decimal("999.00")


def test_get_patterns_by_type(pattern_repo):
    """Test retrieving patterns by type."""
    # Create patterns of different types
    patterns = [
        {
            "pattern_type": "IMPULSE",
            "pattern_key": "amazon",
            "strength_bps": 8000,  # 80.00%
            "first_observed": "2023-01-01",
            "last_observed": "2023-01-15",
            "transaction_count": 5,
            "total_amount_paise": 150000,
        },
        {
            "pattern_type": "IMPULSE",
            "pattern_key": "flipkart",
            "strength_bps": 7500,  # 75.00%
            "first_observed": "2023-01-05",
            "last_observed": "2023-01-20",
            "transaction_count": 3,
            "total_amount_paise": 120000,
        },
        {
            "pattern_type": "SUBSCRIPTION",
            "pattern_key": "netflix",
            "strength_bps": 9500,  # 95.00%
            "first_observed": "2023-01-01",
            "last_observed": "2023-01-15",
            "transaction_count": 3,
            "total_amount_paise": 99900,
        },
    ]

    for pattern in patterns:
        pattern_repo.create_pattern(pattern)

    # Get patterns by type
    impulse_patterns = pattern_repo.get_patterns_by_type("IMPULSE")
    assert len(impulse_patterns) == 2
    assert all(p["pattern_type"] == "IMPULSE" for p in impulse_patterns)
    assert (
        impulse_patterns[0]["strength"] >= impulse_patterns[1]["strength"]
    )  # Should be sorted by strength


def test_update_pattern_strength(pattern_repo):
    """Test updating pattern strength."""
    # Create pattern
    created = pattern_repo.create_pattern(
        {
            "pattern_type": "NIGHT_SPEND",
            "pattern_key": "swiggy",
            "strength_bps": 7000,  # 70.00%
            "first_observed": "2023-01-01",
            "last_observed": "2023-01-10",
            "transaction_count": 4,
            "total_amount_paise": 80000,
        }
    )

    # Update strength
    result = pattern_repo.update_pattern_strength(created["id"], 8500)  # 85.00%
    assert result is True

    # Verify update
    updated = pattern_repo.get_pattern_by_id(created["id"])
    assert updated["strength"] == Decimal("85.00")


def test_get_recent_patterns(pattern_repo):
    """Test retrieving recent patterns."""
    # Create patterns with different last_observed dates
    # Use current date for testing the date filtering
    from datetime import datetime, timedelta

    # Clear any existing test patterns
    with pattern_repo._get_conn() as conn:
        conn.execute("DELETE FROM behaviour_patterns")
        conn.commit()

    # Create patterns with dates relative to now
    dates = [
        datetime.now() - timedelta(days=60),  # Should be excluded (60 days old)
        datetime.now() - timedelta(days=20),  # Should be included (20 days old)
        datetime.now() - timedelta(days=5),  # Should be included (5 days old)
    ]

    for i, date in enumerate(dates):
        pattern_repo.create_pattern(
            {
                "pattern_type": "WEEKEND_SPEND",
                "pattern_key": f"merchant_{i}",
                "strength_bps": 7000 + i * 500,
                "first_observed": "2023-01-01",
                "last_observed": date.isoformat(),
                "transaction_count": 2 + i,
                "total_amount_paise": 50000 + i * 30000,
            }
        )

    # Get recent patterns (last 30 days)
    recent = pattern_repo.get_recent_patterns(days=30)
    assert len(recent) == 2  # Should exclude the 60-day old pattern


def test_get_patterns_by_strength(pattern_repo):
    """Test retrieving patterns by minimum strength."""
    # Create patterns with different strengths
    strengths = [6000, 7500, 8500, 9000]  # 60%, 75%, 85%, 90%
    for i, strength in enumerate(strengths):
        pattern_repo.create_pattern(
            {
                "pattern_type": "OVERSPEND",
                "pattern_key": f"category_{i}",
                "strength_bps": strength,
                "first_observed": "2023-01-01",
                "last_observed": "2023-01-15",
                "transaction_count": 3,
                "total_amount_paise": 100000,
            }
        )

    # Get patterns with strength >= 80%
    strong_patterns = pattern_repo.get_patterns_by_strength(80.0)
    assert len(strong_patterns) == 2
    assert all(p["strength"] >= Decimal("80.00") for p in strong_patterns)


def test_bps_conversion(pattern_repo):
    """Test basis points conversion methods."""
    # Test decimal to bps
    assert pattern_repo._decimal_to_bps(Decimal("0.85")) == 8500
    assert pattern_repo._decimal_to_bps(Decimal("1.00")) == 10000
    assert pattern_repo._decimal_to_bps(Decimal("0.00")) == 0

    # Test bps to decimal (internal method returns 0-1 range)
    assert pattern_repo._bps_to_decimal(8500) == Decimal("0.85")
    assert pattern_repo._bps_to_decimal(10000) == Decimal("1.00")
    assert pattern_repo._bps_to_decimal(0) == Decimal("0.00")


def test_household_id_handling(pattern_repo):
    """Test handling of household_id parameter."""
    # Create pattern with default household
    pattern_repo.create_pattern(
        {
            "pattern_type": "IMPULSE",
            "pattern_key": "amazon",
            "strength_bps": 8000,  # 80.00%
            "first_observed": "2023-01-01",
            "last_observed": "2023-01-15",
            "transaction_count": 5,
            "total_amount_paise": 150000,
        }
    )

    # Create pattern with specific household
    pattern_repo.create_pattern(
        {
            "pattern_type": "SUBSCRIPTION",
            "pattern_key": "netflix",
            "household_id": "household_123",
            "strength_bps": 9500,  # 95.00%
            "first_observed": "2023-01-01",
            "last_observed": "2023-01-15",
            "transaction_count": 3,
            "total_amount_paise": 99900,
        }
    )

    # Test default household
    default_patterns = pattern_repo.get_patterns_by_type("IMPULSE")
    assert len(default_patterns) == 1
    assert default_patterns[0]["household_id"] == "default"
    assert default_patterns[0]["strength"] == Decimal("80.00")

    # Test specific household
    household_patterns = pattern_repo.get_patterns_by_type(
        "SUBSCRIPTION", "household_123"
    )
    assert len(household_patterns) == 1
    assert household_patterns[0]["household_id"] == "household_123"
    assert household_patterns[0]["pattern_key"] == "netflix"
    assert household_patterns[0]["strength"] == Decimal("95.00")
