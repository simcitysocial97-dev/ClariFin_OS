#!/usr/bin/env python3
"""
ClariFin OS — Autonomous Verification Runtime (Program 7B)
M9-C49: Control Plane Consolidation

This is the THIN COMPATIBILITY SHIM for the verification runtime.
All operator/AI commands flow through the SINGLE canonical control plane
defined in runtime/foundation/verification/canonical_control_plane.py.

Legacy commands (~97 tokens) are routed through the canonical control plane
with explicit deprecation warnings — no second semantic authority exists.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification.control_plane_facade import (
    main as canonical_main,
)


def main() -> int:
    """Single dispatcher: all commands flow through the canonical control plane."""
    return canonical_main()


if __name__ == "__main__":
    sys.exit(main())
