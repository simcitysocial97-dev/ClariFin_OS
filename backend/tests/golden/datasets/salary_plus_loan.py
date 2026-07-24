"""Loader for salary_plus_loan golden dataset."""
from __future__ import annotations

import json
from pathlib import Path


def load_salary_plus_loan() -> dict[str, object]:
    """Load salary plus loan golden dataset."""
    dataset_path = Path(__file__).parent / "salary_plus_loan.json"
    with open(dataset_path) as f:
        return json.load(f)  # type: ignore[no-any-return]
