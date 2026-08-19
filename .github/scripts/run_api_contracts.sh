#!/usr/bin/env bash
# .github/scripts/run_api_contracts.sh
#
# M9-C27 — API Contract Integrity & Drift-Proofing gate.
#
# Runs the canonical `api-contracts` verification capability:
#   STRUCTURAL  — live OpenAPI vs committed frontend/backend artifacts
#   GENERATED   — frontend/types/api-generated.ts reproducible from live OpenAPI
#   CONSUMER    — frontend hooks/capabilities mapped to live backend operations
#   WIRE        — live backend responses validated against authoritative contracts
#
# A contract break fails this gate cheaply ( targeted, deterministic, ~seconds )
# instead of after 1,392 Playwright instances. This is a precondition for
# frontend/E2E certification. Does NOT modify the working tree as a permanent
# side effect (generated-type check uses a temp file).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT" || { echo "repo root not found"; exit 1; }

EVIDENCE_DIR="${API_CONTRACTS_EVIDENCE_DIR:-$REPO_ROOT/runtime/generated/evidence/api-contracts}"
mkdir -p "$EVIDENCE_DIR"

echo "================================================"
echo "  M9-C27 — API Contract Integrity Gate"
echo "================================================"

python3 runtime/verify.py api-contracts
rc=$?

# Persist the human summary as evidence
python3 runtime/verify.py api-contracts > "$EVIDENCE_DIR/api-contracts.log" 2>&1 || true

if [ "$rc" -eq 0 ]; then
  echo ""
  echo "API CONTRACT INTEGRITY: PASS"
  echo "Evidence: $EVIDENCE_DIR/api-contracts.log"
  exit 0
else
  echo ""
  echo "API CONTRACT INTEGRITY: FAIL"
  echo "Evidence: $EVIDENCE_DIR/api-contracts.log"
  exit 1
fi
