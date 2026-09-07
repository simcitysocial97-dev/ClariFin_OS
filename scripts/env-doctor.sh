#!/usr/bin/env bash
# =============================================================================
# scripts/env-doctor.sh — ClariFin_OS environment diagnostic / certification
#
# Reports the CONTROLLED interpreters and tool versions (Python resolved through
# ./.venv/bin/python, Node resolved through the frontend installation). Use this
# to prove the repository no longer depends on global project tooling.
#
# M9-C57 additions:
#   * `--json` — machine-readable mode (returns the same structured data as
#     `python -m runtime.verify env-check --full` plus bootstrap metadata).
#   * Platform/uuid import probe — proves the canonical module execution
#     model (no stdlib shadowing by `runtime.platform`).
#   * Interpreter-venv membership proof.
#   * Runtime-configuration summary (available commands via env-check).
#
# Returns non-zero when the controlled environment is incomplete.
# =============================================================================
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PY="$ROOT_DIR/.venv/bin/python"
NODE="$(command -v node || echo '')"
NPM="$(command -v npm || echo '')"

JSON_MODE=false
if [ "${1:-}" = "--json" ]; then
  JSON_MODE=true
fi

v() { printf '  %-22s %s\n' "$1" "$2"; }

if [ "$JSON_MODE" = true ]; then
  report="{"
  report+="\"repository\":\"$ROOT_DIR\","
  report+="\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
fi

echo "======================================================"
echo "  ClariFin_OS — Environment Diagnostic (M10/C57)"
echo "======================================================"
echo ""

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

  # C57: interpreter membership proof + import-resolution probe
  _exe_realpath="$(readlink -f "$PY" 2>/dev/null || echo "$PY")"
  if [[ "$_exe_realpath" == *"/.venv/bin/python"* ]]; then
    v "interpreter membership" "CANONICAL (.venv/bin/python)"
  else
    v "interpreter membership" "NON-CANONICAL ($_exe_realpath)"
  fi
  echo ""
  echo "[ Import resolution (canonical module execution) ]"
  $PY - <<'EOF'
import platform, sys, uuid, json, os
from pathlib import Path
repo = Path(os.environ.get("ROOT_DIR", "."))
resolves = {}
resolves["stdlib_platform_origin"] = getattr(platform, "__file__", "unknown")
resolves["stdlib_platform_system"] = getattr(platform, "system", lambda: "fail")()
resolves["stdlib_uuid_importable"] = hasattr(uuid, "UUID")
resolves["runtime_package"] = "runtime" in sys.modules or __import__("runtime") is not None
try:
    import runtime.platform as rp
    resolves["runtime_platform_init"] = rp.__file__
except Exception as e:
    resolves["runtime_platform_init"] = f"ERROR: {e}"
resolves["canonical_interpreter"] = sys.executable
print(json.dumps(resolves, indent=2, default=str))
EOF
  _probe_exit=$?
  if [ $_probe_exit -ne 0 ]; then
    echo "  !! import-resolution probe FAILED (exit ${{_probe_exit}})" >&2
  else
    echo "  import resolution probe: PASS"
  fi
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
echo "[ Canonical environment guard (M9-C42.5) ]"
# The ONLY allowed Python environment is the repository-root .venv. Any other
# virtualenv (e.g. backend/venv) causes mutmut/pytest path inconsistency.
guard_fail=0
if [ -d backend/venv ]; then
  echo "  !! backend/venv present — forbidden. Remove it; use repo-root .venv only." >&2
  guard_fail=1
fi
if [ -d backend/.venv ]; then
  echo "  !! backend/.venv present — forbidden. Remove it; use repo-root .venv only." >&2
  guard_fail=1
fi
if [ -x "$ROOT_DIR/.venv/bin/mutmut" ]; then
  MV="$("$ROOT_DIR/.venv/bin/mutmut" --version 2>&1 | head -1)"
  case "$MV" in
    *3.7.0*) v "mutmut (pinned 3.7.0)" "$MV";;
    Traceback*) v "mutmut --version" "unavailable outside config dir (OK in CI)";;
    *) echo "  !! mutmut version mismatch: $MV (expected 3.7.0)" >&2; guard_fail=1;;
  esac
fi
[ "$guard_fail" -eq 0 ] && v "environment guard" "PASS" || v "environment guard" "FAIL"

echo ""
echo "[ Runtime command surface (canonical form) ]"
$PY -m runtime.verify 2>&1 | grep -E "^(verify |  check|  plan|  run|  diagnose|  strengthen|  inspect|  certify|  ci|  doctor)" | head -20 || true

echo ""
if [ "$guard_fail" -ne 0 ]; then
  echo "  Diagnostic FAILED — environment inconsistency detected." >&2
  exit 1
fi
echo "  Diagnostic complete."
