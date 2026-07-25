"""Shared fixtures for contract tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.fixture
def snapshot_dir() -> Path:
    """Return path to snapshot directory."""
    return Path(__file__).parent / "snapshots"
