"""Loader for credit_card_revolver golden dataset."""

from __future__ import annotations

import json
from pathlib import Path


def load_credit_card_revolver() -> dict[str, object]:
    """Load credit card revolver golden dataset."""
    dataset_path = (
        Path(__file__).parent.parent / "datasets" / "credit_card_revolver.json"
    )
    with open(dataset_path) as f:
        return json.load(f)  # type: ignore[no-any-return]
