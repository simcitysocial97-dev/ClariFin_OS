#!/usr/bin/env bash
# =============================================================================
# scripts/verify.sh — ClariFin_OS repository-owned verification dispatcher (M10)
#
# All repository verification must be invoked through this wrapper (or the
# underlying ./.venv/bin/python runtime/verify.py). Commands resolve through the
# controlled ./.venv interpreter — never through whatever is first on PATH.
#
# Usage:
#   ./scripts/verify.sh bootstrap       (alias to scripts/bootstrap.sh)
#   ./scripts/verify.sh doctor          (alias to scripts/env-doctor.sh)
#   ./scripts/verify.sh quick           -> runtime/verify.py quick
#   ./scripts/verify.sh backend         -> runtime/verify.py backend
#   ./scripts/verify.sh runtime         -> runtime/verify.py runtime
#   ./scripts/verify.sh frontend        -> runtime/verify.py frontend
#   ./scripts/verify.sh contract        -> runtime/verify.py contracts
#   ./scripts/verify.sh golden          -> runtime/verify.py golden
#   ./scripts/verify.sh e2e             -> runtime/verify.py playwright
#   ./scripts/verify.sh mutation-smoke  -> bash .github/scripts/run_mutation_local_smoke.sh
#   ./scripts/verify.sh mutation        -> runtime/verify.py mutation
#   ./scripts/verify.sh <any>           -> runtime/verify.py <any>
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CMD="${1:-help}"
shift 1 || true

export PATH="$ROOT_DIR/.venv/bin:$PATH"

case "$CMD" in
  bootstrap)
    bash "$ROOT_DIR/scripts/bootstrap.sh";;
  doctor|env|env-doctor)
    bash "$ROOT_DIR/scripts/env-doctor.sh";;
  quick)          exec "$ROOT_DIR/.venv/bin/python" runtime/verify.py quick "$@";;
  backend)        exec "$ROOT_DIR/.venv/bin/python" runtime/verify.py backend "$@";;
  runtime)        exec "$ROOT_DIR/.venv/bin/python" runtime/verify.py runtime "$@";;
  frontend)       exec "$ROOT_DIR/.venv/bin/python" runtime/verify.py frontend "$@";;
  contract)       exec "$ROOT_DIR/.venv/bin/python" runtime/verify.py contracts "$@";;
  golden)         exec "$ROOT_DIR/.venv/bin/python" runtime/verify.py golden "$@";;
  e2e)            exec "$ROOT_DIR/.venv/bin/python" runtime/verify.py playwright "$@";;
  mutation-smoke)
    exec bash "$ROOT_DIR/.github/scripts/run_mutation_local_smoke.sh" "$@";;
  mutation)       exec "$ROOT_DIR/.venv/bin/python" runtime/verify.py mutation "$@";;
  help|--help|-h)
    sed -n '1,32p' "$0";;
  *)
    exec "$ROOT_DIR/.venv/bin/python" runtime/verify.py "$CMD" "$@";;
esac
