"""Transaction invariant tests."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from invariant.transaction import *  # noqa: F401,F403


def test_transaction_invariant_module_exists() -> None:
    """Verify transaction invariant module is importable."""
    assert True
