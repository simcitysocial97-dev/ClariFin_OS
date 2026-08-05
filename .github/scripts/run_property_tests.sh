#!/usr/bin/env bash
# .github/scripts/run_property_tests.sh
# Property-based (hypothesis) tests for loan engine and reconciliation.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT/backend" || { echo "backend/ not found"; exit 1; }

fail=0
for tdir in tests/properties tests/unit/engines/loan tests/unit/engines/reconciliation; do
  if [ -d "$tdir" ]; then
    echo ">> pytest $tdir"
    python3 -m pytest "$tdir" -q --no-header --tb=short
    rc=$?
    [ "$rc" -eq 5 ] && rc=0
    [ "$rc" -ne 0 ] && fail=1
  fi
done
exit $fail
