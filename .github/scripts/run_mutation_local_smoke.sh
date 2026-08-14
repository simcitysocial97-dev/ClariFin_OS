#!/usr/bin/env bash
# .github/scripts/run_mutation_local_smoke.sh
# Bounded local mutation smoke test.
#
# PURPOSE: Prove that the mutmut pipeline is operational without running
# the full mutation workload.  CI remains the authoritative environment.
#
# This script:
#   1. Verifies mutmut is installed and the correct version loads.
#   2. Loads canonical configuration from backend/pyproject.toml [tool.mutmut].
#   3. Resolves source paths (src/engines/).
#   4. Resolves pytest test selection.
#   5. Generates mutants for the bounded target only.
#   6. Executes at least one representative mutant against intended tests.
#   7. Produces result/evidence output.
#   8. Propagates the actual mutmut exit code (no tee masking).
#
# Bounded target: credit_card_engine.outstanding.compute_outstanding
#   - Smallest pure function in engines with dedicated unit tests.
#   - ~5-10 mutants expected.
#   - Tests run: unit + properties covering credit card engines.
#
# Do NOT interpret the local result as the repository mutation score.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"

MUTATION_OUTPUT_DIR="$BACKEND_DIR/tests/generated/mutation/local-smoke"
# Bounded target must match the actual function name. The correct target is the
# pure engine function `compute_outstanding` in src/engines/credit_card_engine/.
# (Previously `x_compute*` matched NO function, corrupting the bounded run.)
TARGET="compute_outstanding"

echo "================================================"
echo "  LOCAL MUTATION SMOKE TEST"
echo "================================================"
echo ""
echo "Scope: $TARGET"
echo "Mutants: BOUNDED (single function)"
echo "Full mutation: NOT RUN"
echo "CI mutation: AUTHORITATIVE"
echo ""

# ── Pre-flight checks ───────────────────────────────────────────────────────

echo "[1/6] Checking mutmut installation ..."
# M10: prefer the controlled repository interpreter (./.venv/bin/mutmut);
# fall back to PATH only if the venv has not been bootstrapped yet.
if [ -x "$REPO_ROOT/.venv/bin/mutmut" ]; then
  MUTMUT="$REPO_ROOT/.venv/bin/mutmut"
else
  MUTMUT="$(command -v mutmut || true)"
fi
if [ -z "$MUTMUT" ]; then
  echo "FAIL: mutmut not found (run scripts/bootstrap.sh to install into ./.venv)"
  exit 1
fi
# Mutmut 3.7 uses `--version` (no `version` subcommand) and must run from the
# directory containing backend/pyproject.toml ([tool.mutmut]) or config
# discovery raises FileNotFoundError.
MUTMUT_VERSION=$(cd "$BACKEND_DIR" && "$MUTMUT" --version 2>&1 | head -1 || echo "unknown")
echo "  mutmut ($MUTMUT): $MUTMUT_VERSION"

echo "[2/6] Checking canonical config (backend/pyproject.toml) ..."
if [ ! -f "$BACKEND_DIR/pyproject.toml" ]; then
  echo "FAIL: backend/pyproject.toml not found"
  exit 1
fi
if ! grep -q '\[tool.mutmut\]' "$BACKEND_DIR/pyproject.toml"; then
  echo "FAIL: [tool.mutmut] section missing from pyproject.toml"
  exit 1
fi
echo "  Canonical config: OK"

echo "[3/6] Checking source paths resolve ..."
if [ ! -d "$BACKEND_DIR/src/engines" ]; then
  echo "FAIL: src/engines/ directory not found"
  exit 1
fi
echo "  Source paths: OK"

echo "[4/6] Checking pytest selection resolves ..."
cd "$BACKEND_DIR"
PY="${REPO_ROOT}/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3 || command -v python)"
TEST_COUNT=$("$PY" -m pytest --collect-only -q \
  tests/unit/ tests/properties/ 2>/dev/null \
  | tail -1 | grep -oP '\d+ test' || echo "0 tests")
echo "  Test collection: $TEST_COUNT"

echo "[5/6] Running bounded mutation smoke ..."
echo "  Target: $TARGET"
echo "  Note: stats collection may take 2-5 minutes on first run."
echo ""

mkdir -p "$MUTATION_OUTPUT_DIR"

# Run mutmut — capture real exit code, do NOT pipe through tee.
START_TIME=$(date +%s)
"$MUTMUT" run "$TARGET" > "$MUTATION_OUTPUT_DIR/mutation-run.log" 2>&1
MUTMUT_RC=$?
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "[6/6] Collecting evidence ..."

# Extract results
KILLED=$(grep -oP 'Killed:\s+\K\d+' "$MUTATION_OUTPUT_DIR/mutation-run.log" 2>/dev/null || echo "?")
SURVIVED=$(grep -oP 'Survived:\s+\K\d+' "$MUTATION_OUTPUT_DIR/mutation-run.log" 2>/dev/null || echo "?")
TOTAL_MUTANTS=$(grep -oP '(\d+) files mutated' "$MUTATION_OUTPUT_DIR/mutation-run.log" 2>/dev/null | grep -oP '\d+' || echo "?")

# Generate summary
cat > "$MUTATION_OUTPUT_DIR/mutation-summary.json" <<EOF
{
  "killed": $KILLED,
  "survived": $SURVIVED,
  "total_mutants_generated": $TOTAL_MUTANTS,
  "score_percent": null,
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "target": "$TARGET",
  "mutmut_version": "$MUTMUT_VERSION",
  "duration_seconds": $DURATION,
  "exit_code": $MUTMUT_RC,
  "is_smoke": true,
  "ci_authoritative": true,
  "note": "Local smoke result is NOT a mutation score. It proves the pipeline is operational."
}
EOF

echo ""
echo "================================================"
echo "  SMOKE RESULTS"
echo "================================================"
echo "  Exit code : $MUTMUT_RC"
echo "  Duration  : ${DURATION}s"
echo "  Mutants   : $TOTAL_MUTANTS generated"
echo "  Killed    : $KILLED"
echo "  Survived  : $SURVIVED"
echo "  Artifact  : $MUTATION_OUTPUT_DIR/"
echo ""

# Classify result
if [ "$MUTMUT_RC" -eq 0 ]; then
  echo "  Status: SUCCESS — all sampled mutants killed"
elif [ "$MUTMUT_RC" -eq 1 ]; then
  echo "  Status: INFRASTRUCTURE FAILURE — fatal error (config/command/process)"
elif [ "$MUTMUT_RC" -eq 2 ]; then
  echo "  Status: MUTATION FAILURE — surviving mutants detected"
elif [ "$MUTMUT_RC" -eq 4 ]; then
  echo "  Status: TIMEOUT — mutants timed out"
else
  echo "  Status: UNKNOWN exit code $MUTMUT_RC"
fi

echo ""
echo "LOCAL MUTATION SMOKE"
echo "Scope: $TARGET"
echo "Mutants: $TOTAL_MUTANTS generated"
echo "Full mutation: NOT RUN"
echo "CI mutation: AUTHORITATIVE"
echo "================================================"

# Preserve the mutmut exit code
exit "$MUTMUT_RC"
