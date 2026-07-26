"""Shared fixtures for contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest

# Add src to path


@pytest.fixture
def snapshot_dir() -> Path:
    """Return path to snapshot directory."""
    return Path(__file__).parent / "snapshots"
