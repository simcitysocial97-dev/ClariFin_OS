#!/usr/bin/env bash
# =============================================================================
# scripts/bootstrap.sh — ClariFin_OS reproducible environment bootstrap (M10/C57)
#
# Creates/repairs the SINGLE repository Python environment (./.venv) and
# installs frontend dependencies deterministically (npm ci). Bootstrap consumes
# the SAME contract as CI (.github/actions/setup-python-runtime): pip install
# -e '.[all]' from root pyproject.toml.
#
# M9-C57 (Canonical Runtime & Reproducible Environment Convergence):
#   * Validates prerequisites (Python >= 3.12, Node >= 24) BEFORE touching .venv.
#   * Recreates .venv when the system interpreter version diverges from the
#     existing venv — prevents stale/ambiguous interpreters from lingering.
#   * After install, runs an import-resolution smoke test proving that under
#     canonical module execution `import platform` resolves to the stdlib and
#     `import uuid` works, and that `runtime.platform` is reachable via its
#     explicit package path.
#   * Prints a READY / NOT-READY verdict with exit code.
#
# Fails loudly when requirements cannot be satisfied. No global project tooling
# is required (only base python3/node).
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
say()  { echo -e "${GREEN}[bootstrap]${NC} $*"; }
warn() { echo -e "${YELLOW}[bootstrap]${NC} $*"; }
info() { echo -e "${CYAN}[bootstrap]${NC} $*"; }
die()  { echo -e "${RED}[bootstrap] ERROR: $*${NC}" >&2; exit 1; }

# ── Prerequisites ──────────────────────────────────────────────────────────────

require_python() {
  local py=""
  for cand in python3 python; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null; then
      py="$cand"; break
    fi
  done
  [ -n "$py" ] || die "Python >= 3.12 required. None found on PATH."
  echo "$py"
}

require_node() {
  local node=""
  if command -v node >/dev/null 2>&1; then
    if node --version 2>/dev/null | grep -qE '^v(2[4-9]|[3-9][0-9])\.'; then
      node="node"
    fi
  fi
  # Node < 24 is permitted only for informational warning; npm ci still works.
  # Some WSL2 installations ship older node without rootfs replacement.
  if [ -z "$node" ]; then
    warn "Node.js >= 24 not found on PATH — frontend provisioning may require manual attention"
  fi
  echo "${node:-node}"
}

PY_SRC="$(require_python)"
NODE="$(require_node)"
say "Python   : $PY_SRC $( "$PY_SRC" --version 2>&1 )"
if command -v node >/dev/null 2>&1; then
  say "Node     : $NODE $( node --version 2>&1 )"
else
  say "Node     : $NODE (not on PATH)"
fi

# ── Venv lifecycle ─────────────────────────────────────────────────────────────

VENV_PY="$ROOT_DIR/.venv/bin/python"
RECREATE_VENV=false

if [ -x "$VENV_PY" ]; then
  EXISTING_PY=$( "$VENV_PY" -c 'import sys; print("%d.%d"%(sys.version_info[:2]))' 2>/dev/null || echo unknown )
  NEW_PY=$( "$PY_SRC" -c 'import sys; print("%d.%d"%(sys.version_info[:2]))' 2>/dev/null || echo unknown )
  if [ "$EXISTING_PY" != "$NEW_PY" ]; then
    warn "Interpreter version drift detected: .venv has $EXISTING_PY, system has $NEW_PY"
    warn "Recreating .venv to avoid cross-interpreter dependency pollution ..."
    rm -rf "$ROOT_DIR/.venv"
    RECREATE_VENV=true
  else
    info "Existing .venv uses matching Python $EXISTING_PY — reusing."
  fi
else
  say "Creating repository virtual environment at ./.venv ..."
fi

"$PY_SRC" -m venv .venv
[ -x "$VENV_PY" ] || die "Failed to create ./.venv"

# ── Dependency install (canonical contract) ───────────────────────────────────

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

# ── Validation ─────────────────────────────────────────────────────────────────

say "Validating environment ..."
bash "$ROOT_DIR/scripts/env-doctor.sh" || die "environment validation failed"

say "Import-resolution smoke test (canonical module execution from repo root) ..."
# Under canonical execution (python -m runtime.verify), sys.path[0] = cwd =
# repo root, so stdlib platform cannot be shadowed by runtime/platform.
"$VENV_PY" - <<'PYEOF'
import platform, sys, uuid, json, os
from pathlib import Path
resolves = {}
resolves["stdlib_platform_origin"] = getattr(platform, "__file__", "unknown")
resolves["stdlib_platform_system"] = getattr(platform, "system", lambda: "fail")()
resolves["stdlib_uuid_importable"] = hasattr(uuid, "UUID")
resolves["runtime_package"] = "runtime" in sys.modules or __import__("runtime") is not None
try:
    import runtime.platform as rp
    resolves["runtime_platform_init"] = rp.__file__
except Exception as e:
    resolves["runtime_platform_init"] = "ERROR: " + str(e)
resolves["canonical_interpreter"] = sys.executable
print(json.dumps(resolves, indent=2, default=str))
PYEOF
_probe_exit=$?
if [ $_probe_exit -ne 0 ]; then
  die "import-resolution smoke test FAILED (exit ${_probe_exit})"
fi

say "Bootstrap complete."
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  READY — canonical environment established.${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Canonical invocation:"
echo "    python -m runtime.verify <command>         (from repo root)"
echo "  Verify before mutation/CI-critical work:"
echo "    python -m runtime.verify env-check"
echo "    bash scripts/env-doctor.sh"
echo "  Launcher:"
echo "    ./scripts/launch.sh start                  (backend + frontend)"
echo ""
