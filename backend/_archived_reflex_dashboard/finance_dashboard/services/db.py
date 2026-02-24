"""Database service wrapper.

Provides clean import path to FinanceDB from the src module.
"""

import sys
from pathlib import Path

# Add src directory to path for imports
_SRC_DIR = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from db import FinanceDB as _FinanceDB

# Re-export
FinanceDB = _FinanceDB


def get_db_path() -> str:
    """Return the path to the finance database."""
    return str(Path(__file__).resolve().parent.parent.parent.parent / "data" / "finance.db")