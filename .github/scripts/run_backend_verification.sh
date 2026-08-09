#!/usr/bin/env bash
# .github/scripts/run_backend_verification.sh
# Backend verification: contract, invariant and property-based tests.
# (Lint + unit are covered by the quick/fast-checks gate, so this focuses on
#  backend-specific test suites.)
#
# The four test directories are independent and run in parallel to reduce
# wall-clock time. Each directory uses its own isolated test database via
# the session-scoped pristine template.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT/backend" || { echo "backend/ not found"; exit 1; }

fail=0
pids=()
outputs=()

for tdir in tests/contract tests/invariants tests/properties tests/unit/engines; do
  if [ -d "$tdir" ]; then
    out="$(mktemp)"
    echo ">> pytest $tdir (parallel)"
    python3 -m pytest "$tdir" -q --no-header --tb=short > "$out" 2>&1 &
    pids+=($!)
    outputs+=("$out")
  fi
done

for pid in "${pids[@]}"; do
  wait "$pid" || fail=1
done

for out in "${outputs[@]}"; do
  cat "$out"
  rm -f "$out"
done

exit $fail
