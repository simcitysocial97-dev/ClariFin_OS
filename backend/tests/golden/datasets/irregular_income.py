"""Loader for irregular_income golden dataset."""
from __future__ import annotations

import json
from pathlib import Path


def load_irregular_income() -> dict[str, object]:
    """Load irregular income golden dataset."""
    dataset_path = Path(__file__).parent / "irregular_income.json"
    with open(dataset_path) as f:
        return json.load(f)  # type: ignore[no-any-return]
