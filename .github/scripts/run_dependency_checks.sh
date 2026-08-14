#!/usr/bin/env bash
# .github/scripts/run_dependency_checks.sh
# Dependency health checks for Python (pip-audit) and Node (npm audit).
# Invoked by the dependency-update workflow. Exit 0 = healthy (warnings ok).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo "================================================"
echo "  ClariFin OS — Dependency Health Check"
echo "================================================"

mkdir -p dependency-reports

# ── Python dependency audit ───────────────────────
echo -e "\n[1/2] Python dependency security audit..."
pip install --quiet pip-audit 2>/dev/null || true
# M10: the single dependency authority is root pyproject.toml (no more
# backend/requirements.txt). Audit the resolved environment lock/deps directly.
if [ -f requirements.lock ]; then
  pip-audit -r requirements.lock 2>&1 | tee dependency-reports/python-audit.txt || echo "python audit completed with findings"
elif [ -f pyproject.toml ]; then
  pip-audit 2>&1 | tee dependency-reports/python-audit.txt || echo "python audit completed with findings"
else
  echo "No dependency authority found — skipping pip-audit" > dependency-reports/python-audit.txt
fi

# ── Node dependency audit ─────────────────────────
echo -e "\n[2/2] Node.js dependency audit..."
cd frontend
npm audit --audit-level=moderate 2>&1 | tee "$REPO_ROOT/dependency-reports/npm-audit.txt" || echo "npm audit completed with findings"
npm outdated --json > "$REPO_ROOT/dependency-reports/npm-outdated.json" 2>/dev/null || echo '{"outdated":false}' > "$REPO_ROOT/dependency-reports/npm-outdated.json"
cd "$REPO_ROOT"

# ── Health summary ────────────────────────────────
cat > dependency-reports/dependency-health.md <<EOF
# Dependency Health Report

## Summary
- Python: security audit completed (see python-audit.txt)
- Node: npm audit completed (see npm-audit.txt)

## Recommendations
- Review pip-audit output for security vulnerabilities.
- Review npm audit output for dependency updates.
- Consider updating minor/patch versions safely.

Generated at $(date -u +"%Y-%m-%d %H:%M:%S UTC")
EOF

echo ""
echo "Dependency reports saved to: dependency-reports/"
echo "================================================"
