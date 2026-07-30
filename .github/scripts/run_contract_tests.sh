#!/usr/bin/env bash
# .github/scripts/run_contract_tests.sh
# Runs contract tests and uploads results as artifacts
# Arguments:
#   $1 = backend directory (default: backend)
#   $2 = changed files list (optional, for selective runs)

set -euo pipefail

BACKEND_DIR="${1:-backend}"
CHANGED_FILES="${2:-}"

echo "================================================"
echo "  ClariFin OS — Contract Tests"
echo "================================================"

cd "$BACKEND_DIR"

# Determine which contract tests to run
if [ -n "$CHANGED_FILES" ]; then
  echo "Running selective contract tests based on changed files"
  
  # Extract router names from changed files
  # Example: src/routers/accounts.py → tests/contract/generated/test_accounts.py
  SPECIFIC_TESTS=""
  while IFS= read -r file; do
    # Extract basename without extension
    basename=$(basename "$file" .py)
    test_file="tests/contract/generated/test_${basename}.py"
    if [ -f "$test_file" ]; then
      SPECIFIC_TESTS="$SPECIFIC_TESTS $test_file"
    fi
  done <<< "$CHANGED_FILES"
  
  if [ -n "$SPECIFIC_TESTS" ]; then
    echo "Running specific contract tests: $SPECIFIC_TESTS"
    TEST_PATH="$SPECIFIC_TESTS"
  else
    echo "No specific contract tests found, running all"
    TEST_PATH="tests/contract/"
  fi
else
  echo "Running all contract tests"
  TEST_PATH="tests/contract/"
fi

# Run contract tests with coverage
pytest $TEST_PATH \
  --timeout=60 \
  --tb=short \
  -v \
  --no-header \
  --cov=. \
  --cov-report=json:tests/generated/contract-coverage.json \
  --cov-report=term-missing \
  -n auto

echo ""
echo "Contract tests complete"
echo "Coverage report: tests/generated/contract-coverage.json"
