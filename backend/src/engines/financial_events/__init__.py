"""Financial Events Engine - Pure calculation library.

Handles lineage detection and event relationships.
No database access - all data is passed as parameters.
"""

from .lineage_walker import (
    DEFAULT_ROLLOVER_LOOKBACK_DAYS,
    LineageProposal,
    detect_rollover_scenarios,
    walk_lineage,
)

__all__ = [
    # Constants
    "DEFAULT_ROLLOVER_LOOKBACK_DAYS",
    # Types
    "LineageProposal",
    # Functions
    "walk_lineage",
    "detect_rollover_scenarios",
]