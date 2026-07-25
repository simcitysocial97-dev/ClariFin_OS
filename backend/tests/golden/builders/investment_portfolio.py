"""Loader for investment_portfolio golden dataset."""
from __future__ import annotations

import json
from pathlib import Path


def load_investment_portfolio() -> dict[str, object]:
    """Load investment portfolio golden dataset."""
    dataset_path = Path(__file__).parent.parent / "datasets" / "investment_portfolio.json"
    with open(dataset_path) as f:
        return json.load(f)  # type: ignore[no-any-return]
