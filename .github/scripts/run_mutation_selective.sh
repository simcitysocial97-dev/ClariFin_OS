#!/usr/bin/env bash
# .github/scripts/run_mutation_selective.sh
# Authoritative mutation testing — CI execution only.
#
# Runs the FULL mutation scope defined in backend/pyproject.toml [tool.mutmut].
# The bounded local smoke is in run_mutation_local_smoke.sh and must NOT be
# used as a replacement for this script in CI.
#
# Exit code classification (preserved, not masked):
#   0 — Mutation success: all mutants killed, threshold met.
#   1 — Infrastructure failure: fatal error (config invalid, command failed,
#       process crashed, dependency issue).
#   2 — Mutation failure: one or more mutants survived (below threshold).
#   4 — Mutation failure: one or more mutants timed out.
#   8 — Mutation failure: one or more mutants caused tests to take 2x longer.
#   bit-OR combinations of 2/4/8 are also possible for mutation failures.
#
# IMPORTANT: Output is streamed to stdout AND logged to file so CI logs show progress.

# Allow partial results on infrastructure failures
set -eo pipefail

# Get absolute paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="${1:-$REPO_ROOT/backend}"
TARGET_PATH="${2:-src/engines/}"

echo "================================================"
echo "  ClariFin OS — Authoritative Mutation Testing (CI)"
echo "================================================"
echo ""
echo "Scope     : $TARGET_PATH (full, per [tool.mutmut] in pyproject.toml)"
echo "Runner    : python3 -m pytest (canonical, configured)"
echo "Threshold : 80% (per mutation_config.toml)"
echo ""

cd "$BACKEND_DIR"

MUTATION_OUTPUT_DIR="tests/generated/mutation"
mkdir -p "$MUTATION_OUTPUT_DIR"

# ── Canonical mutmut invocation ──────────────────────────────────────────────
# Uses config from backend/pyproject.toml [tool.mutmut]:
#   source_paths = ["src/engines/"]
#   runner = "python3 -m pytest"
#   pytest_add_cli_args_test_selection = ["tests/unit/", "tests/properties/", "tests/invariants/", "tests/contract/", "tests/integration/"]
#   no_progress = true
#
# NO deprecated CLI flags (--python, --tests-dir, etc.).
# Exit code preserved via PIPESTATUS, never hidden by tee.
echo "Starting canonical mutation run ..."
START_TIME=$(date +%s)
# Stream output to both stdout (for CI logs) and log file
mutmut run 2>&1 | tee "$MUTATION_OUTPUT_DIR/mutation-run.log"
MUTMUT_RC=${PIPESTATUS[0]}
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "Mutation run completed in ${DURATION}s with RC=$MUTMUT_RC"
echo ""

# ── Evidence collection ─────────────────────────────────────────────────────
echo "Collecting mutation evidence ..."

mutmut results > "$MUTATION_OUTPUT_DIR/mutation-results.txt" 2>&1 || true
cat "$MUTATION_OUTPUT_DIR/mutation-results.txt"

mutmut show   > "$MUTATION_OUTPUT_DIR/surviving-mutants.txt" 2>&1 || true
mutmut junitxml 2>/dev/null > "$MUTATION_OUTPUT_DIR/mutation-junit.xml" || true

KILLED=$(grep -oP 'Killed:\s+\K\d+' "$MUTATION_OUTPUT_DIR/mutation-results.txt" 2>/dev/null || echo "0")
SURVIVED=$(grep -oP 'Survived:\s+\K\d+' "$MUTATION_OUTPUT_DIR/mutation-results.txt" 2>/dev/null || echo "0")
TIMEOUT_COUNT=$(grep -oP 'Timeout:\s+\K\d+' "$MUTATION_OUTPUT_DIR/mutation-results.txt" 2>/dev/null || echo "0")
TOTAL=$((KILLED + SURVIVED))

if [ "$TOTAL" -gt 0 ]; then
  SCORE=$(echo "scale=1; $KILLED * 100 / $TOTAL" | bc)
else
  SCORE="N/A"
fi

cat > "$MUTATION_OUTPUT_DIR/mutation-summary.json" <<EOF
{
  "mutmut_version": "$(mutmut --version 2>/dev/null || echo 'unknown')",
  "source_scope": "$TARGET_PATH",
  "test_scope": "tests/unit/, tests/properties/, tests/invariants/, tests/contract/, tests/integration/",
  "git_commit_sha": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "git_tree_hash": "$(git rev-parse HEAD^{tree} 2>/dev/null || echo 'unknown')",
  "dependency_lock_hash": "$(sha256sum backend/requirements.lock 2>/dev/null | cut -d' ' -f1 || echo 'unknown')",
  "killed": $KILLED,
  "survived": $SURVIVED,
  "timeout": $TIMEOUT_COUNT,
  "total": $TOTAL,
  "score_percent": $SCORE,
  "threshold_percent": 80,
  "threshold_met": $([ "$SCORE" != "N/A" ] && [ $(echo "$SCORE >= 80" | bc) -eq 1 ] && echo true || echo false),
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "target": "$TARGET_PATH",
  "duration_seconds": $DURATION,
  "mutmut_rc": $MUTMUT_RC,
  "is_smoke": false,
  "ci_authoritative": true
}
EOF

echo ""
echo "================================================"
echo "  MUTATION RESULTS"
echo "================================================"
echo "  Killed   : $KILLED"
echo "  Survived : $SURVIVED"
echo "  Timeout  : $TIMEOUT_COUNT"
echo "  Score    : ${SCORE}%"
echo "  Duration : ${DURATION}s"
echo "  RC       : $MUTMUT_RC"
echo ""

# ── Print surviving mutants for debugging ────────────────────────────────────
if [ -f "$MUTATION_OUTPUT_DIR/surviving-mutants.txt" ] && [ -s "$MUTATION_OUTPUT_DIR/surviving-mutants.txt" ]; then
    echo "================================================"
    echo "  SURVIVING MUTANTS (first 50 lines)"
    echo "================================================"
    head -50 "$MUTATION_OUTPUT_DIR/surviving-mutants.txt"
    echo ""
fi

# ── Classify result for CI ──────────────────────────────────────────────────
case $MUTMUT_RC in
  0)
    echo "  STATUS: MUTATION SUCCESS — all mutants killed, threshold met."
    RESULT="success"
    EXIT_CODE=0
    ;;
  1)
    echo "  STATUS: INFRASTRUCTURE FAILURE — fatal error in mutmut execution."
    echo "  Check mutation-run.log for details. This is NOT a quality gate failure."
    RESULT="infrastructure_failure"
    EXIT_CODE=1
    ;;
  2|4|8)
    echo "  STATUS: MUTATION FAILURE — score below threshold or timeouts detected."
    RESULT="mutation_failure"
    EXIT_CODE=2
    ;;
  *)
    echo "  STATUS: UNKNOWN exit code $MUTMUT_RC"
    RESULT="unknown"
    EXIT_CODE=1
    ;;
esac

echo ""
echo "  Classification: $RESULT"
echo "================================================"

# ── Generate aggregate report ───────────────────────────────────────────────
python3 "$SCRIPT_DIR/generate_mutation_report.py" || echo "Mutation report generation skipped"

echo ""
echo "Evidence saved to: $MUTATION_OUTPUT_DIR/"

# ── Enforce threshold ───────────────────────────────────────────────────────
if [ "$RESULT" = "success" ] && [ "$(jq -r '.threshold_met' "$MUTATION_OUTPUT_DIR/mutation-summary.json")" = "false" ]; then
  echo "❌ Mutation score below threshold (80%)"
  EXIT_CODE=2
fi

# Preserve the actual exit code for the workflow
exit $EXIT_CODE
