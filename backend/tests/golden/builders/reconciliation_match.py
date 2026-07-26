"""Loader for reconciliation_match golden dataset."""

from __future__ import annotations

import json
from pathlib import Path


def load_reconciliation_match() -> dict[str, object]:
    """Load reconciliation match golden dataset."""
    dataset_path = (
        Path(__file__).parent.parent / "datasets" / "reconciliation_match.json"
    )
    with open(dataset_path) as f:
        return json.load(f)  # type: ignore[no-any-return]