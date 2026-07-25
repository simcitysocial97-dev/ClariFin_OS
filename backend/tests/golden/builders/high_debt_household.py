"""Loader for high_debt_household golden dataset."""
from __future__ import annotations

import json
from pathlib import Path


def load_high_debt_household() -> dict[str, object]:
    """Load high debt household golden dataset."""
    dataset_path = Path(__file__).parent.parent / "datasets" / "high_debt_household.json"
    with open(dataset_path) as f:
        return json.load(f)  # type: ignore[no-any-return]
