#!/usr/bin/env bash
# .github/scripts/run_mutation_local_smoke.sh
#
# M9-C42.5 — Bounded local mutation smoke (thin wrapper).
#
# Delegates to the single canonical runner:
#   python -m runtime.verify mutation --smoke
# which runs the clean-room fixture in backend/tests/mutation_infra/ and proves
# the mutation pipeline produces killed / survived / no-tests classifications.
# It is NOT a mutation score. The authoritative full campaign runs in CI.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
  PY="$REPO_ROOT/.venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi

exec "$PY" -m runtime.verify mutation --smoke "$@"
