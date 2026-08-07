"""pytest configuration, custom markers, and hooks for the test suite."""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom enterprise test markers for strict suite categorization."""
    config.addinivalue_line("markers", "capability: mark test as capability smoke test")
    config.addinivalue_line("markers", "contract: mark test as contract schema test")
    config.addinivalue_line(
        "markers", "property: mark test as property-based hypothesis test"
    )
    config.addinivalue_line(
        "markers", "invariant: mark test as financial domain invariant test"
    )
    config.addinivalue_line(
        "markers", "golden: mark test as golden dataset baseline test"
    )
    config.addinivalue_line("markers", "meta: mark test as meta-verification test")
