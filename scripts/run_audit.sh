#!/bin/bash
#
# ClariFin_OS Audit Script
# ========================
# Runs comprehensive checks on the codebase and generates a report
#
# Usage: ./scripts/run_audit.sh [options]
# Options:
#   --full      Run full test suite (slower)
#   --quick     Run quick checks only (default)
#   --output    Save report to file
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
FULL_AUDIT=false
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            FULL_AUDIT=true
            shift
            ;;
        --quick)
            FULL_AUDIT=false
            shift
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./scripts/run_audit.sh [options]"
            echo "Options:"
            echo "  --full      Run full test suite (slower)"
            echo "  --quick     Run quick checks only (default)"
            echo "  --output    Save report to file"
            echo "  --help      Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create output function
output() {
    if [[ -n "$OUTPUT_FILE" ]]; then
        echo "$@" >> "$OUTPUT_FILE"
    else
        echo -e "$@"
    fi
}

# Clear output file if specified
if [[ -n "$OUTPUT_FILE" ]]; then
    > "$OUTPUT_FILE"
fi

output "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
output "${BLUE}║           ClariFin_OS - Automated Audit Script                 ║${NC}"
output "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
output ""
output "Audit Date: $(date)"
output "Mode: $([ "$FULL_AUDIT" = true ] && echo 'Full' || echo 'Quick')"
output ""

# ============================================
# Backend Checks
# ============================================
output "${BLUE}▶ Backend Checks${NC}"
output "─────────────────────────────────────────────────────────────────"

cd "$PROJECT_ROOT/backend"

# Check Python environment
output ""
output "Checking Python environment..."
if command -v ./venv/bin/python &> /dev/null; then
    PYTHON_VERSION=$(./venv/bin/python --version 2>&1)
    output "  ${GREEN}✓${NC} Python: $PYTHON_VERSION"
else
    output "  ${RED}✗${NC} Python virtual environment not found"
    exit 1
fi

# Run doctor
output ""
output "Running environment doctor..."
if ./venv/bin/python scripts/doctor.py > /tmp/doctor_output.txt 2>&1; then
    output "  ${GREEN}✓${NC} Environment healthy"
else
    output "  ${YELLOW}⚠${NC} Environment issues detected"
    cat /tmp/doctor_output.txt | while read line; do
        output "    $line"
    done
fi

# Run validation
output ""
output "Running pipeline validation..."
if ./venv/bin/python -m src.validate_pipeline > /tmp/validate_output.txt 2>&1; then
    WARNINGS=$(grep -c "warning" /tmp/validate_output.txt || true)
    ERRORS=$(grep -c "error" /tmp/validate_output.txt || true)
    if [ "$ERRORS" -eq 0 ]; then
        output "  ${GREEN}✓${NC} Validation passed ($WARNINGS warnings)"
    else
        output "  ${YELLOW}⚠${NC} Validation passed with issues ($ERRORS errors, $WARNINGS warnings)"
    fi
else
    output "  ${RED}✗${NC} Validation failed"
fi

# Check test count
output ""
output "Checking test suite..."
if $FULL_AUDIT; then
    output "  Running full test suite (this may take a while)..."
    if ./venv/bin/python -m pytest tests/ --tb=no -q > /tmp/test_output.txt 2>&1; then
        TEST_SUMMARY=$(tail -1 /tmp/test_output.txt)
        output "  ${GREEN}✓${NC} Tests: $TEST_SUMMARY"
    else
        TEST_SUMMARY=$(tail -1 /tmp/test_output.txt)
        output "  ${YELLOW}⚠${NC} Tests: $TEST_SUMMARY"
    fi
else
    # Quick test - just count tests
    TEST_COUNT=$(./venv/bin/python -m pytest tests/ --collect-only -q 2>/dev/null | tail -1 | grep -o '[0-9]\+' | head -1)
    output "  ${GREEN}✓${NC} Test collection: $TEST_COUNT tests found"
fi

# Check database
output ""
output "Checking database..."
if [ -f "data/finance.db" ]; then
    DB_SIZE=$(du -h data/finance.db | cut -f1)
    output "  ${GREEN}✓${NC} Database exists ($DB_SIZE)"
else
    output "  ${YELLOW}⚠${NC} Database not found (will be created on first run)"
fi

# ============================================
# Frontend Checks
# ============================================
output ""
output ""
output "${BLUE}▶ Frontend Checks${NC}"
output "─────────────────────────────────────────────────────────────────"

cd "$PROJECT_ROOT/frontend"

# Check Node.js
output ""
output "Checking Node.js environment..."
if command -v npm &> /dev/null; then
    NODE_VERSION=$(node --version 2>&1)
    NPM_VERSION=$(npm --version 2>&1)
    output "  ${GREEN}✓${NC} Node.js: $NODE_VERSION"
    output "  ${GREEN}✓${NC} npm: $NPM_VERSION"
else
    output "  ${RED}✗${NC} Node.js/npm not found"
    exit 1
fi

# Check dependencies
output ""
output "Checking dependencies..."
if [ -d "node_modules" ]; then
    PKG_COUNT=$(ls node_modules | wc -l)
    output "  ${GREEN}✓${NC} Dependencies installed ($PKG_COUNT packages)"
else
    output "  ${YELLOW}⚠${NC} node_modules not found - run npm ci"
fi

# Run TypeScript check
output ""
output "Running TypeScript type check..."
if npx tsc --noEmit > /tmp/tsc_output.txt 2>&1; then
    output "  ${GREEN}✓${NC} TypeScript compilation clean"
else
    ERROR_COUNT=$(grep -c "error TS" /tmp/tsc_output.txt || true)
    output "  ${RED}✗${NC} TypeScript errors found: $ERROR_COUNT"
fi

# Run ESLint (quick mode only counts issues)
output ""
output "Running ESLint..."
if npm run lint > /tmp/eslint_output.txt 2>&1; then
    output "  ${GREEN}✓${NC} ESLint passed"
else
    ERROR_COUNT=$(grep -c "error" /tmp/eslint_output.txt || true)
    WARNING_COUNT=$(grep -c "warning" /tmp/eslint_output.txt || true)
    output "  ${YELLOW}⚠${NC} ESLint issues: $ERROR_COUNT errors, $WARNING_COUNT warnings"
fi

# Try build (skip in quick mode if it takes too long)
if $FULL_AUDIT; then
    output ""
    output "Running production build..."
    if timeout 120 npm run build > /tmp/build_output.txt 2>&1; then
        output "  ${GREEN}✓${NC} Build successful"
    else
        output "  ${RED}✗${NC} Build failed"
        # Show last few lines of error
        tail -5 /tmp/build_output.txt | while read line; do
            output "    $line"
        done
    fi
fi

# ============================================
# V2 Pipeline Checks
# ============================================
output ""
output ""
output "${BLUE}▶ V2 Pipeline Checks${NC}"
output "─────────────────────────────────────────────────────────────────"

cd "$PROJECT_ROOT"

# Check V2 files exist
output ""
output "Checking V2 pipeline files..."
V2_FILES=(
    "backend/src/routers/imports.py"
    "backend/src/routers/quarantine.py"
    "backend/src/routers/jobs.py"
    "backend/src/engines/statement_validator.py"
    "backend/src/engines/auto_heal_engine.py"
    "frontend/app/quarantine/page.tsx"
    "frontend/app/quarantine/[id]/page.tsx"
    "frontend/components/import/v2-import-status.tsx"
)

for file in "${V2_FILES[@]}"; do
    if [ -f "$file" ]; then
        output "  ${GREEN}✓${NC} $file"
    else
        output "  ${RED}✗${NC} $file (missing)"
    fi
done

# Check docling integration
output ""
output "Checking docling integration..."
if [ -f "backend/src/extraction/docling_extractor.py" ]; then
    output "  ${GREEN}✓${NC} Docling extractor present"
else
    output "  ${YELLOW}⚠${NC} Docling extractor not found"
fi

if [ -f "backend/src/extraction/factory.py" ]; then
    output "  ${GREEN}✓${NC} Extraction factory present"
else
    output "  ${YELLOW}⚠${NC} Extraction factory not found"
fi

# ============================================
# Summary
# ============================================
output ""
output ""
output "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
output "${BLUE}║                        Audit Summary                           ║${NC}"
output "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
output ""

# Count critical files
BACKEND_FILES=$(find "$PROJECT_ROOT/backend/src" -name "*.py" | wc -l)
FRONTEND_FILES=$(find "$PROJECT_ROOT/frontend" -name "*.tsx" -o -name "*.ts" | wc -l)
TEST_FILES=$(find "$PROJECT_ROOT/backend/tests" -name "test_*.py" | wc -l)

output "Code Statistics:"
output "  Backend Python files: $BACKEND_FILES"
output "  Frontend TypeScript files: $FRONTEND_FILES"
output "  Test files: $TEST_FILES"
output ""

output "Key Findings:"
output "  1. Review PROJECT_AUDIT_REPORT.md for detailed findings"
output "  2. Critical: Fix frontend build (missing generateStaticParams)"
output "  3. Important: 4 auto-heal tests are failing"
output "  4. Important: 21 unused backend routes detected"
output "  5. Warning: 242 ESLint errors in frontend"
output ""

output "Next Steps:"
output "  1. Run 'cd frontend && npm run build' to check build status"
output "  2. Run 'cd backend && make test' for full test results"
output "  3. Run 'cd backend && make validate' for API validation"
output "  4. Review PROJECT_AUDIT_REPORT.md for detailed recommendations"
output ""

if [[ -n "$OUTPUT_FILE" ]]; then
    output "Report saved to: $OUTPUT_FILE"
fi

output "${GREEN}Audit completed at $(date)${NC}"
