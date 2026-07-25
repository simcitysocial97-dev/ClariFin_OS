"""Loader for normal_household golden dataset."""
from __future__ import annotations

import json
from pathlib import Path


def load_normal_household() -> dict[str, object]:
    """Load normal household golden dataset."""
    dataset_path = Path(__file__).parent.parent / "datasets" / "normal_household.json"
    with open(dataset_path) as f:
        return json.load(f)  # type: ignore[no-any-return]
