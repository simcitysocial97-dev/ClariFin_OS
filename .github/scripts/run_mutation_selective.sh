#!/usr/bin/env bash
# .github/scripts/run_mutation_selective.sh
# Runs mutation testing only on changed files
# This keeps CI fast by not mutating everything

set -euo pipefail

BACKEND_DIR="${1:-backend}"
# Comma-separated list of files to mutate
# If empty, uses a default small set
TARGET_FILES="${2:-}"

echo "================================================"
echo "  ClariFin OS — Selective Mutation Testing"
echo "================================================"

cd "$BACKEND_DIR"

# Output directory for mutation results
MUTATION_OUTPUT_DIR="tests/generated/mutation"
mkdir -p "$MUTATION_OUTPUT_DIR"

if [ -z "$TARGET_FILES" ]; then
  echo "No specific targets — running mutation on engines only"
  # Default: mutate the engines directory (most critical)
  TARGET_PATH="src/engines/"
else
  TARGET_PATH="$TARGET_FILES"
fi

echo "Mutation target: $TARGET_PATH"
echo "Test runner: pytest tests/unit/ tests/properties/"
echo ""

# Run mutmut with specific path
# --no-progress prevents cluttering CI logs
mutmut run \
  --paths-to-mutate "$TARGET_PATH" \
  --tests-dir "tests/" \
  --runner "python -m pytest tests/unit/ tests/properties/ -x -q --timeout=30" \
  2>&1 | tee "$MUTATION_OUTPUT_DIR/mutation-run.log"

# Generate results
echo ""
echo "Generating mutation results..."

# Get mutation score
mutmut results 2>&1 | tee "$MUTATION_OUTPUT_DIR/mutation-results.txt"

# Get surviving mutants (the important ones to fix)
mutmut show 2>&1 | tee "$MUTATION_OUTPUT_DIR/surviving-mutants.txt" || true

# Generate junitxml report if possible
mutmut junitxml 2>/dev/null > "$MUTATION_OUTPUT_DIR/mutation-junit.xml" || true

echo ""
echo "Mutation results saved to: $MUTATION_OUTPUT_DIR/"

# Extract and display the score
KILLED=$(grep -oP 'Killed:\s+\K\d+' "$MUTATION_OUTPUT_DIR/mutation-results.txt" 2>/dev/null || echo "0")
SURVIVED=$(grep -oP 'Survived:\s+\K\d+' "$MUTATION_OUTPUT_DIR/mutation-results.txt" 2>/dev/null || echo "0")
TOTAL=$((KILLED + SURVIVED))

if [ "$TOTAL" -gt 0 ]; then
  SCORE=$(echo "scale=1; $KILLED * 100 / $TOTAL" | bc)
  echo ""
  echo "Mutation Score: ${SCORE}% (${KILLED}/${TOTAL} killed)"
  
  # Save score for artifact
  cat > "$MUTATION_OUTPUT_DIR/mutation-summary.json" <<EOF
{
  "killed": $KILLED,
  "survived": $SURVIVED,
  "total": $TOTAL,
  "score_percent": $SCORE,
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "target": "$TARGET_PATH"
}
EOF
else
  echo "Could not parse mutation score"
fi
