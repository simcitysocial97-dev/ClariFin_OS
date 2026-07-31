"""Thin shim so ``python -m verification_intelligence`` works from backend/."""

import sys
from pathlib import Path

# Ensure src is in path for the stub
sys.path.insert(0, str(Path(__file__).parent / "src"))

from verification_intelligence import main as _stub_main

if __name__ == "__main__":
    sys.exit(_stub_main())
