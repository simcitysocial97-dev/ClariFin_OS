#!/usr/bin/env bash
# .github/scripts/run_migration_verification.sh
# Database migration integrity: validate alembic heads resolve and run
# migration-specific tests.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT/backend" || { echo "backend/ not found"; exit 1; }

fail=0
if [ -f "alembic.ini" ]; then
  echo ">> alembic heads (dry-run resolution)"
  python3 -c "
from alembic.config import Config
from alembic.script import ScriptDirectory
cfg = Config('alembic.ini')
ScriptDirectory.from_config(cfg).get_heads()
print('migrations OK')
" 2>&1 || fail=1
else
  echo ">> alembic.ini not found — skipping structural migration check"
fi

if [ -d tests ]; then
  echo ">> pytest tests (migration tagged)"
  python3 -m pytest tests/ -k "migration or alembic" -q --no-header --tb=short
  rc=$?
  [ "$rc" -eq 5 ] && rc=0
  [ "$rc" -ne 0 ] && fail=1
fi
exit $fail
