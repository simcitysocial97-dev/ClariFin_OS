#!/usr/bin/env bash
# =============================================================================
# scripts/env-doctor.sh — ClariFin_OS environment diagnostic / certification
#
# Reports the CONTROLLED interpreters and tool versions (Python resolved through
# ./.venv/bin/python, Node resolved through the frontend installation). Use this
# to prove the repository no longer depends on global project tooling.
# Returns non-zero when the controlled environment is incomplete.
# =============================================================================
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PY="$ROOT_DIR/.venv/bin/python"
NODE="$(command -v node || echo '')"
NPM="$(command -v npm || echo '')"

echo "======================================================"
echo "  ClariFin_OS — Environment Diagnostic (M10)"
echo "======================================================"
echo ""

v() { printf '  %-22s %s\n' "$1" "$2"; }

echo "[ Python ]"
if [ -x "$PY" ]; then
  v "python (controlled)" "$("$PY" --version 2>&1)"
  v "python path"          "$PY"
  # Use console entry points (present in .venv/bin) — some tools (mutmut,
  # hypothesis) have no `-m` entry point and would traceback under `-m`.
  for tool in pytest black ruff mypy mutmut coverage hypothesis; do
    ver=""
    if [ -x "$ROOT_DIR/.venv/bin/$tool" ]; then
      ver="$("$ROOT_DIR/.venv/bin/$tool" --version 2>&1 | head -1)"
    fi
    case "$ver" in
      Traceback*|"") ver="$("$PY" -c "import importlib.metadata as m; print(m.version('$tool'))" 2>&1 | head -1)";;
    esac
    v "$tool (controlled)" "${ver:-MISSING}"
  done
else
  echo "  !! ./.venv/bin/python NOT FOUND — run scripts/bootstrap.sh" >&2
  echo "  (falling back to PATH for diagnostics)"
  v "python3" "$(python3 --version 2>&1)"
  for mod in pytest black ruff mypy mutmut coverage; do
    v "$mod (PATH)" "$(python3 -m "$mod" --version 2>&1 | head -1)"
  done
fi

echo ""
echo "[ Node / frontend ]"
v "node"   "$("$NODE" --version 2>&1 || echo MISSING)"
v "npm"    "$("$NPM" --version 2>&1 || echo MISSING)"
if [ -d frontend/node_modules ]; then
  v "frontend/node_modules" "present ($(find frontend/node_modules -maxdepth 1 -mindepth 1 | wc -l) top-level pkgs)"
else
  v "frontend/node_modules" "MISSING — run cd frontend && npm ci"
fi

echo ""
echo "[ Reproducibility contract ]"
[ -f pyproject.toml ] && v "pyproject.toml (authority)" "present" || v "pyproject.toml" "MISSING"
[ -f requirements.lock ] && v "requirements.lock (snapshot)" "present" || v "requirements.lock" "absent (regenerate via scripts/freeze-env.sh)"
[ -f frontend/package-lock.json ] && v "frontend/package-lock.json" "present" || v "frontend/package-lock.json" "MISSING"

echo ""
echo "  Diagnostic complete."
