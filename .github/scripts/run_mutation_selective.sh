#!/usr/bin/env bash
# .github/scripts/run_mutation_selective.sh
#
# M9-C42.5 — Authoritative mutation runner (thin wrapper).
#
# The ONLY mutation executor now lives in
#   runtime/foundation/verification/mutation_runner.py
# invoked via `python runtime/verify.py mutation`. This wrapper exists so the
# existing profile/registry/tier/evidence-contract references keep working and
# route to that single canonical runner. No mutation logic lives here.
#
# The authoritative scope (source_paths=src/engines/, 80% threshold) is defined
# in backend/pyproject.toml [tool.mutmut] and enforced by the runner. It is NOT
# reduced here.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
  PY="$REPO_ROOT/.venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi

exec "$PY" runtime/verify.py mutation "$@"
