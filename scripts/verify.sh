#!/usr/bin/env bash
# =============================================================================
# scripts/verify.sh — ClariFin_OS repository-owned verification dispatcher (M10)
#
# All repository verification must be invoked through this wrapper (or the
# underlying ./.venv/bin/python -m runtime.verify). Commands resolve through the
# controlled ./.venv interpreter — never through whatever is first on PATH.
#
# Usage:
#   ./scripts/verify.sh bootstrap       (alias to scripts/bootstrap.sh)
#   ./scripts/verify.sh doctor          (alias to scripts/env-doctor.sh)
#   ./scripts/verify.sh quick           -> -m runtime.verify quick
#   ./scripts/verify.sh backend         -> -m runtime.verify backend
#   ./scripts/verify.sh runtime         -> -m runtime.verify runtime
#   ./scripts/verify.sh frontend        -> -m runtime.verify frontend
#   ./scripts/verify.sh contract        -> -m runtime.verify contracts
#   ./scripts/verify.sh golden          -> -m runtime.verify golden
#   ./scripts/verify.sh e2e             -> -m runtime.verify playwright
#   ./scripts/verify.sh mutation-smoke  -> bash .github/scripts/run_mutation_local_smoke.sh
#   ./scripts/verify.sh mutation        -> -m runtime.verify mutation
#   ./scripts/verify.sh <any>           -> -m runtime.verify <any>
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CMD="${1:-help}"
shift 1 || true

export PATH="$ROOT_DIR/.venv/bin:$PATH"
# Canonical Python for Playwright/backend subprocesses
export CLARIFIN_PYTHON="$ROOT_DIR/.venv/bin/python"

case "$CMD" in
  bootstrap)
    bash "$ROOT_DIR/scripts/bootstrap.sh";;
  doctor|env|env-doctor)
    bash "$ROOT_DIR/scripts/env-doctor.sh";;
  quick)          exec "$ROOT_DIR/.venv/bin/python" -m runtime.verify quick "$@";;
  backend)        exec "$ROOT_DIR/.venv/bin/python" -m runtime.verify backend "$@";;
  runtime)        exec "$ROOT_DIR/.venv/bin/python" -m runtime.verify runtime "$@";;
  frontend)       exec "$ROOT_DIR/.venv/bin/python" -m runtime.verify frontend "$@";;
  contract)       exec "$ROOT_DIR/.venv/bin/python" -m runtime.verify contracts "$@";;
  golden)         exec "$ROOT_DIR/.venv/bin/python" -m runtime.verify golden "$@";;
  e2e)            exec "$ROOT_DIR/.venv/bin/python" -m runtime.verify playwright "$@";;
  mutation-smoke)
    exec "$ROOT_DIR/.venv/bin/python" -m runtime.verify mutation --smoke "$@";;
  mutation)       exec "$ROOT_DIR/.venv/bin/python" -m runtime.verify mutation "$@";;
  help|--help|-h)
    sed -n '1,32p' "$0";;
  *)
    exec "$ROOT_DIR/.venv/bin/python" -m runtime.verify "$CMD" "$@";;
esac
