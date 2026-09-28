#!/usr/bin/env bash
# .github/scripts/run_frontend_verification.sh
# Frontend verification: ESLint, TypeScript typecheck, production build, Vitest.
#
# VEA-2 Phase 1.5 (FW-2/FW-3): each phase is recorded independently.
#
# Previously every phase was collapsed into a single `fail` flag and one exit
# code. A run could exit 1 with *zero* TypeScript errors, which repeatedly led
# agents into "fix the TypeScript errors" loops against a compiler that was
# already clean. Per-phase status is now emitted as machine-readable JSON so the
# failing phase is unambiguous.
#
# The overall exit-code contract is unchanged: 0 when every phase passes,
# 1 when any phase fails.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT/frontend" || { echo "frontend/ not found"; exit 1; }

# Canonical Python resolver (venv-first) - for final JSON summary
if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
  PY="$REPO_ROOT/.venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi

BACKEND_LOG="$REPO_ROOT/runtime/generated/frontend-contract-backend.log"
STARTED_BACKEND=false
BACKEND_PID=""

cleanup() {
  if [ "$STARTED_BACKEND" = true ] && [ -n "$BACKEND_PID" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if ! curl --fail --silent http://127.0.0.1:8000/platform/v1/health >/dev/null 2>&1; then
  mkdir -p "$(dirname "$BACKEND_LOG")"
  (
    cd "$REPO_ROOT/backend"
    exec "$PY" -m uvicorn src.api:app --host 127.0.0.1 --port 8000
  ) >"$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!
  STARTED_BACKEND=true
  ready=false
  for _ in $(seq 1 60); do
    if curl --fail --silent http://127.0.0.1:8000/platform/v1/health >/dev/null 2>&1; then
      ready=true
      break
    fi
    sleep 1
  done
  if [ "$ready" != true ]; then
    echo "Backend did not become ready" >&2
    tail -50 "$BACKEND_LOG" >&2 || true
    exit 1
  fi
fi

EVIDENCE_DIR="${FRONTEND_EVIDENCE_DIR:-$REPO_ROOT/runtime/generated/evidence/frontend}"
mkdir -p "$EVIDENCE_DIR"

# VEA-2 Phase 2 (M4): the verification unit this execution belongs to, so the
# evidence self-identifies. Empty (rather than a guessed value) when the caller
# does not supply one.
VERIFICATION_UNIT_ID="${VERIFICATION_UNIT_ID:-}"

fail=0
phase_json=""

# run_phase <name> <command...>
# Runs one phase, tees its output to a per-phase log, and records its status.
run_phase() {
  local name="$1"; shift
  local log="$EVIDENCE_DIR/${name}.log"
  local start end duration status

  echo ">> $name: $*"
  start=$(date +%s)
  "$@" > "$log" 2>&1
  local code=$?
  end=$(date +%s)
  duration=$((end - start))

  cat "$log"

  if [ "$code" -eq 0 ]; then
    status="pass"
  else
    status="fail"
    fail=1
  fi

  echo "<< $name: $status (exit=$code, ${duration}s)"

  if [ -n "$phase_json" ]; then
    phase_json="$phase_json,"
  fi
  phase_json="$phase_json{\"phase\":\"$name\",\"status\":\"$status\",\"exit_code\":$code,\"duration_seconds\":$duration,\"log\":\"$log\"}"
}

run_phase lint npx eslint . --ext .ts,.tsx --quiet
run_phase typecheck npx tsc --noEmit
run_phase build npm run build

if [ -d "tests" ] || [ -d "src" ] || [ -d "__tests__" ]; then
  run_phase test npx vitest run
fi

overall="pass"
if [ "$fail" -ne 0 ]; then
  overall="fail"
fi

cat > "$EVIDENCE_DIR/frontend-verification.json" <<JSON
{
  "schema": "frontend-verification/v1",
  "overall_status": "$overall",
  "unit_id": "$VERIFICATION_UNIT_ID",
  "phases": [$phase_json]
}
JSON

echo
echo "Phase summary: $EVIDENCE_DIR/frontend-verification.json"
"$PY" - "$EVIDENCE_DIR/frontend-verification.json" <<'PY' 2>/dev/null || true
import json, sys
with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)
for phase in data["phases"]:
    print(f"  {phase['phase']:<10} {phase['status']:<5} exit={phase['exit_code']} {phase['duration_seconds']}s")
PY

exit $fail
