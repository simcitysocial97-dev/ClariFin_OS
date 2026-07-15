"""Shared fixtures for contract tests."""

from __future__ import annotations

import json
import re

# Add src to path
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.api import app


@pytest.fixture
def client() -> TestClient:
    """Provide FastAPI TestClient without mocks."""
    return TestClient(app)


@pytest.fixture
def snapshot_dir() -> Path:
    """Return path to snapshot directory."""
    return Path(__file__).parent / "snapshots"


def normalize_response(data: dict[str, Any] | list[Any] | str) -> str:
    """Normalize response for snapshot comparison.

    Handles:
    - UUIDs -> [UUID]
    - Timestamps -> [TIMESTAMP]
    - Generated IDs -> [ID]
    """
    if isinstance(data, str):
        # Normalize timestamps
        data = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?', '[TIMESTAMP]', data)
        # Normalize UUIDs
        data = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '[UUID]', data, flags=re.IGNORECASE)
        return data

    if isinstance(data, dict):
        result = {}
        for k, v in sorted(data.items()):
            result[k] = normalize_response(v)
        return json.dumps(result, sort_keys=True)

    if isinstance(data, list):
        result = [normalize_response(item) for item in data]
        return json.dumps(result, sort_keys=True)

    return str(data)
