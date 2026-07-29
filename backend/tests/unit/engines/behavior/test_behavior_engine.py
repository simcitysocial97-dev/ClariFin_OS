"""Unit tests for the main behavior_engine.py file.

This test ensures the core behavior engine file is included in coverage
and exercises its key utility functions.
"""

import pytest

from src.engines.behavior_engine import (
    _normalize_score,
    _coefficient_of_variation,
    _moving_average,
    invalidate_behavior_cache,
    get_cached_behavior_profile,
    set_cached_behavior_profile,
)

class TestBehaviorEngineCore:
    """Test the core behavior engine functions."""

    def test_normalize_score_bounds(self) -> None:
        """Test _normalize_score with various inputs."""
        # Test default bounds (0.0 to 1.0)
        assert _normalize_score(0.5) == 0.5
        assert _normalize_score(0.0) == 0.0
        assert _normalize_score(1.0) == 1.0

        # Test custom bounds
        assert _normalize_score(50, 0, 100) == 0.5
        assert _normalize_score(25, 0, 100) == 0.25
        assert _normalize_score(75, 0, 100) == 0.75

        # Test clamping
        assert _normalize_score(-10, 0, 100) == 0.0
        assert _normalize_score(110, 0, 100) == 1.0

        # Test equal min/max
        assert _normalize_score(50, 50, 50) == 0.5

    def test_coefficient_of_variation(self) -> None:
        """Test _coefficient_of_variation with various inputs."""
        # Test basic case
        assert _coefficient_of_variation([10, 20, 30]) == pytest.approx(0.408248, rel=1e-5)

        # Test single value
        assert _coefficient_of_variation([10]) == 0.0

        # Test empty list
        assert _coefficient_of_variation([]) == 0.0

        # Test zero mean
        assert _coefficient_of_variation([0, 0, 0]) == 0.0

    def test_moving_average(self) -> None:
        """Test _moving_average with various inputs."""
        # Test basic case
        assert _moving_average([1, 2, 3, 4, 5], 2) == [1.0, 1.5, 2.5, 3.5, 4.5]

        # Test empty list
        assert _moving_average([], 2) == []

        # Test window larger than list
        assert _moving_average([1, 2, 3], 5) == [1.0, 1.5, 2.0]

        # Test window size 1
        assert _moving_average([1, 2, 3], 1) == [1.0, 2.0, 3.0]

    def test_cache_functions(self) -> None:
        """Test the cache functions."""
        # Test cache operations
        invalidate_behavior_cache()

        # Test get/set cache
        test_profile = {"test": "data"}
        set_cached_behavior_profile("test_db", test_profile)
        cached_profile = get_cached_behavior_profile("test_db")
        assert cached_profile == test_profile

        # Test cache invalidation
        invalidate_behavior_cache()
        assert get_cached_behavior_profile("test_db") is None

    def test_date_parsing(self) -> None:
        """Test the _parse_date function."""
        from src.engines.behavior_engine import _parse_date

        # Test various date formats
        assert _parse_date("2023-01-15") is not None
        assert _parse_date("15/01/2023") is not None
        assert _parse_date("15-01-2023") is not None
        assert _parse_date("15/01/23") is not None
        assert _parse_date("15 01 2023") is None  # Not supported format

        # Test empty string
        assert _parse_date("") is None
        assert _parse_date(None) is None