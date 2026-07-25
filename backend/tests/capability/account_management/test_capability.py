"""Smoke tests for Account Management capability."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from tests.golden.builders.normal_household import load_normal_household


class TestAccountManagementCapability:
    """Validate Account Management capability wiring."""

    def test_import_account_engine(self) -> None:
        """Account engine must be importable."""
        from src.engines import account_engine

        assert account_engine is not None

    def test_golden_dataset_account_scenario(self) -> None:
        """Golden dataset must load and validate."""
        data = load_normal_household()
        assert "accounts" in data
