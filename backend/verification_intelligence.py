"""Thin shim so ``python -m verification_intelligence`` works from backend/."""
from tools.verification_intelligence import main

if __name__ == "__main__":
    main()
