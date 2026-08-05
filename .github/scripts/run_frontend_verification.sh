#!/usr/bin/env bash
# .github/scripts/run_frontend_verification.sh
# Frontend verification: ESLint, TypeScript typecheck, Vitest unit tests.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT/frontend" || { echo "frontend/ not found"; exit 1; }

fail=0
echo ">> npx eslint ."
npx eslint . --ext .ts,.tsx --quiet 2>&1 || fail=1
echo ">> npx tsc --noEmit"
npx tsc --noEmit 2>&1 || fail=1
if [ -d "tests" ] || [ -d "src" ]; then
  echo ">> npx vitest run"
  npx vitest run --no-header 2>&1 || fail=1
fi
exit $fail
