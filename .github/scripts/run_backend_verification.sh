#!/usr/bin/env bash
# .github/scripts/run_backend_verification.sh
# Backend verification: contract, invariant and property-based tests.
# (Lint + unit are covered by the quick/fast-checks gate, so this focuses on
#  backend-specific test suites.)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT/backend" || { echo "backend/ not found"; exit 1; }

fail=0
for tdir in tests/contract tests/invariants tests/properties tests/unit/engines; do
  if [ -d "$tdir" ]; then
    echo ">> pytest $tdir"
    python3 -m pytest "$tdir" -q --no-header --tb=short
    rc=$?
    # 5 = no tests collected (acceptable)
    [ "$rc" -eq 5 ] && rc=0
    [ "$rc" -ne 0 ] && fail=1
  fi
done
exit $fail
