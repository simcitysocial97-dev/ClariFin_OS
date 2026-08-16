#!/usr/bin/env bash
# =============================================================================
# scripts/bootstrap.sh — ClariFin_OS reproducible environment bootstrap (M10)
#
# Creates/repairs the SINGLE repository Python environment (./.venv) and
# installs frontend dependencies deterministically (npm ci). Bootstrap consumes
# the SAME contract as CI (.github/actions/setup-python-runtime): `pip install
# -e ".[all]"` from root pyproject.toml.
#
# Fails loudly when requirements cannot be satisfied. No global project tooling
# is required (only a base python3 >= 3.12 to create the venv).
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
say()  { echo -e "${GREEN}[bootstrap]${NC} $*"; }
warn() { echo -e "${YELLOW}[bootstrap]${NC} $*"; }
die()  { echo -e "${RED}[bootstrap] ERROR: $*${NC}" >&2; exit 1; }

require_python() {
  local py=""
  for cand in python3 python; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null; then
      py="$cand"; break
    fi
  done
  [ -n "$py" ] || die "Python >= 3.12 required. None found on PATH. Install Python 3.12+ first."
  echo "$py"
}

PY_SRC="$(require_python)"
say "Creating repository virtual environment at ./.venv ..."
"$PY_SRC" -m venv .venv
VENV_PY="$ROOT_DIR/.venv/bin/python"
[ -x "$VENV_PY" ] || die "Failed to create ./.venv"

say "Upgrading pip ..."
"$VENV_PY" -m pip install --upgrade pip

say "Installing canonical dependencies (pip install -e '.[all]') ..."
"$VENV_PY" -m pip install --timeout 300 --retries 10 -e ".[all]"

say "Resolving frontend dependencies (npm ci) ..."
if [ -f frontend/package-lock.json ]; then
  ( cd frontend && npm ci )
else
  warn "frontend/package-lock.json not found — running npm install"
  ( cd frontend && npm install )
fi

say "Validating environment ..."
bash "$ROOT_DIR/scripts/env-doctor.sh" || die "environment validation failed"

say "Environment smoke test: import backend + runtime core ..."
"$VENV_PY" -c "import fastapi, pydantic, pandas, httpx; import runtime; print('imports OK')"

say "Bootstrap complete. Use ./scripts/verify.sh to run verification."
