"""Loader for financial_forecast golden dataset."""

from __future__ import annotations

import json
from pathlib import Path


def load_financial_forecast() -> dict[str, object]:
    """Load financial forecast golden dataset."""
    dataset_path = Path(__file__).parent.parent / "datasets" / "financial_forecast.json"
    with open(dataset_path) as f:
        return json.load(f)  # type: ignore[no-any-return]
