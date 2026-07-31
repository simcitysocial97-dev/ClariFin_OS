# ClariFin_OS Repository Architecture Consolidation — Final Migration Plan (LOCK v1.0)

## Executive Summary

This is the **final, locked architecture** for ClariFin_OS. No future reorganizations are planned. Every future runtime, feature, engine, UI module, test, and document must follow this structure.

**Key principle:** Move one runtime at a time. Validate after each. Never delete originals until new location passes all tests.

---

## 1. Final Repository Tree (LOCKED)

```
ClariFin_OS/
├── backend/
│   ├── (existing backend structure - DO NOT MOVE)
│   └── tests/                    # KEEP IN PLACE - pytest discovery
├── frontend/
│   ├── (existing frontend structure - DO NOT MOVE)
│   ├── tests/                    # KEEP IN PLACE - vitest/playwright discovery
│   └── __tests__/                # KEEP IN PLACE
├── runtime/
│   ├── foundation/
│   │   ├── repository/
│   │   │   ├── api/
│   │   │   ├── builder/
│   │   │   ├── graph/
│   │   │   ├── scanner/
│   │   │   ├── query/
│   │   │   ├── analysis/
│   │   │   ├── validation/
│   │   │   ├── cli/
│   │   │   └── models/
│   │   └── verification/
│   │       ├── api/
│   │       ├── planner/
│   │       ├── registry/
│   │       ├── models/
│   │       ├── validation/
│   │       └── cli/
│   ├── system/
│   │   ├── context/
│   │   │   └── src/
│   │   │       ├── workspace/
│   │   │       ├── history/
│   │   │       ├── selection/
│   │   │       ├── navigation/
│   │   │       ├── serialization/
│   │   │       ├── validation/
│   │   │       └── models/
│   │   ├── evidence/
│   │   │   └── README.md         # STUB: Program 4
│   │   ├── financial/
│   │   │   └── README.md         # STUB: Program 5
│   │   ├── intelligence/
│   │   │   └── README.md         # STUB: Program 8
│   │   ├── graph/
│   │   │   └── README.md         # STUB: Future
│   │   ├── timeline/
│   │   │   └── README.md         # STUB: Future
│   │   └── command/
│   │       └── README.md         # STUB: Future
│   └── generated/
│       ├── repository/
│       │   ├── index.json        # COMMITTED
│       │   ├── graph.json
│       │   └── cache/            # GITIGNORED
│       └── verification/
├── testing/
│   ├── backend/                   # KEEP IN PLACE (backend/tests)
│   ├── frontend/                  # KEEP IN PLACE (frontend/tests, frontend/__tests__)
│   ├── runtime/
│   │   ├── foundation/
│   │   │   ├── repository/
│   │   │   └── verification/
│   │   └── system/
│   │       └── context/
│   ├── integration/
│   ├── fixtures/
│   └── generated/
├── docs/
│   ├── architecture/
│   ├── runtimes/
│   │   ├── foundation/
│   │   │   ├── repository/
│   │   │   └── verification/
│   │   └── system/
│   │       └── context/
│   ├── audits/
│   ├── decisions/
│   ├── specifications/
│   ├── reports/
│   │   ├── architecture/
│   │   ├── implementation/
│   │   ├── verification/
│   │   ├── performance/
│   │   ├── audits/
│   │   └── completion/
│   └── archive/
├── tools/
│   ├── generators/
│   ├── verification/
│   ├── migration/
│   ├── auditing/
│   ├── diagnostics/
│   └── development/
├── servers/
├── memory-bank/
├── scripts/
├── data/
├── .github/
├── .gitignore
├── README.md
├── package.json
├── tsconfig.json
├── start.sh
├── start.bat
└── ARCHITECTURE.md               # NEW: top-level architecture doc
```

---

## 2. Move Map (Source → Destination)

### 2.1 Runtime Foundation Runtimes (EXISTING - MOVE)

| Source | Destination |
|--------|-------------|
| `repo_intelligence/` | `runtime/foundation/repository/` |
| `verification/` | `runtime/foundation/verification/` |

### 2.2 Runtime System Runtimes (ONE EXISTING, REST STUBS)

| Source | Destination |
|--------|-------------|
| `context-runtime/` | `runtime/system/context/` |
| *(stub)* | `runtime/system/evidence/README.md` |
| *(stub)* | `runtime/system/financial/README.md` |
| *(stub)* | `runtime/system/timeline/README.md` |
| *(stub)* | `runtime/system/graph/README.md` |
| *(stub)* | `runtime/system/command/README.md` |
| *(stub)* | `runtime/system/intelligence/README.md` |

### 2.3 Internal Restructuring (repo_intelligence → runtime/foundation/repository)

| Source File | Destination |
|-------------|-------------|
| `repo_intelligence/graph/graph_service.py` | `runtime/foundation/repository/graph/graph_service.py` |
| `repo_intelligence/graph/schema.py` | `runtime/foundation/repository/graph/schema.py` |
| `repo_intelligence/builder/builder.py` | `runtime/foundation/repository/builder/builder.py` |
| `repo_intelligence/builder/index.py` | `runtime/foundation/repository/builder/index.py` |
| `repo_intelligence/query/query.py` | `runtime/foundation/repository/query/query.py` |
| `repo_intelligence/analysis/impact.py` | `runtime/foundation/repository/analysis/impact.py` |
| `repo_intelligence/analysis/metrics.py` | `runtime/foundation/repository/analysis/metrics.py` |
| `repo_intelligence/validation/validator.py` | `runtime/foundation/repository/validation/validator.py` |
| `repo_intelligence/scanner/` | `runtime/foundation/repository/scanner/` |
| `repo_intelligence/cli/` (new) | `runtime/foundation/repository/cli/` |
| `repo_intelligence/models/` (new) | `runtime/foundation/repository/models/` |
| `repo_intelligence/index.py` | `runtime/foundation/repository/api/index.py` |
| `repo_intelligence/__main__.py` | `runtime/foundation/repository/__main__.py` |
| `repo_intelligence/README.md` | `runtime/foundation/repository/README.md` |
| `repo_intelligence/REPORT.md` | `docs/reports/implementation/repository_runtime_report.md` |
| `repo_intelligence/generate_index.py` | `tools/generators/generate_repository_index.py` |
| `repo_intelligence/index.json` | `runtime/generated/repository/index.json` |
| `repo_intelligence/graph.json` (if exists) | `runtime/generated/repository/graph.json` |

### 2.4 Internal Restructuring (verification → runtime/foundation/verification)

| Source File | Destination |
|-------------|-------------|
| `verification/runtime.py` | `runtime/foundation/verification/runtime.py` |
| `verification/registry.py` | `runtime/foundation/verification/registry/registry.py` |
| `verification/planner.py` | `runtime/foundation/verification/planner/planner.py` |
| `verification/models/` (new) | `runtime/foundation/verification/models/` |
| `verification/validation/` (new) | `runtime/foundation/verification/validation/` |
| `verification/cli/` (new) | `runtime/foundation/verification/cli/` |
| `verification/__init__.py` | `runtime/foundation/verification/__init__.py` |
| `verification/api/` (new) | `runtime/foundation/verification/api/` |

### 2.5 Internal Restructuring (context-runtime → runtime/system/context)

| Source File | Destination |
|-------------|-------------|
| `context-runtime/src/ContextRuntime.ts` | `runtime/system/context/src/workspace/ContextRuntime.ts` |
| `context-runtime/src/ContextManager.ts` | `runtime/system/context/src/workspace/ContextManager.ts` |
| `context-runtime/src/ContextWorkspace.ts` | `runtime/system/context/src/workspace/ContextWorkspace.ts` |
| `context-runtime/src/ContextHistory.ts` | `runtime/system/context/src/history/ContextHistory.ts` |
| `context-runtime/src/ContextSelection.ts` | `runtime/system/context/src/selection/ContextSelection.ts` |
| `context-runtime/src/ContextNavigation.ts` | `runtime/system/context/src/navigation/ContextNavigation.ts` |
| `context-runtime/src/ContextSerialization.ts` | `runtime/system/context/src/serialization/ContextSerialization.ts` |
| `context-runtime/src/ContextValidation.ts` | `runtime/system/context/src/validation/ContextValidation.ts` |
| `context-runtime/src/types.ts` | `runtime/system/context/src/models/types.ts` |
| `context-runtime/src/index.ts` | `runtime/system/context/src/workspace/index.ts` |
| `context-runtime/package.json` | `runtime/system/context/package.json` |
| `context-runtime/README.md` | `runtime/system/context/README.md` |
| `context-runtime/tests/` | `testing/runtime/system/context/` |

### 2.6 Documentation

| Source | Destination |
|--------|-------------|
| `docs/stage-*/` | `docs/architecture/` or `docs/archive/` |
| `docs/program-1-operating-system/` | `docs/architecture/` |
| `docs/Unified_testing_framework.md` | `docs/specifications/unified_testing_framework.md` |
| `docs/PHASE_*_REPORT.md` | `docs/reports/completion/PHASE_*_REPORT.md` |
| `docs/ENGINE_PACKAGE_AUDIT_REPORT.md` | `docs/reports/audits/engine_package_audit.md` |

### 2.7 Tools

| Source | Destination |
|--------|-------------|
| `backend/scripts/generate_*.py` | `tools/generators/` |
| `backend/tools/*.py` | `tools/development/` or `tools/diagnostics/` |
| `backend/verification_intelligence.py` | `tools/verification/verification_intelligence.py` |
| `frontend/scripts/*.ts` | `tools/generators/` or `tools/development/` |
| `frontend/tools/*.ts` | `tools/development/` or `tools/diagnostics/` |
| Root scripts (if any) | `tools/migration/` |

### 2.8 Reports & Audits (Root Level)

| Source | Destination |
|--------|-------------|
| `*_AUDIT*.md` (at root) | `docs/reports/audits/` |
| `*_REPORT.md` (at root) | `docs/reports/implementation/` |
| `PHASE_*.md` (at root) | `docs/reports/completion/` |
| `STAGE_*.md` (at root) | `docs/reports/architecture/` |
| `ENGINE_*.md` (at root) | `docs/reports/implementation/` |
| `CAPABILITY_*.md` (at root) | `docs/reports/performance/` or `docs/reports/audits/` |
| `GENERATOR_*.md` (at root) | `docs/reports/implementation/` |
| `SELECTIVE_*.md` (at root) | `docs/reports/verification/` |
| `TEST_*.md` (at root) | `docs/reports/verification/` |

### 2.9 Root Cleanup

**Files to KEEP at root:**
- `README.md`
- `package.json`
- `tsconfig.json`
- `start.sh`
- `start.bat`
- `.gitignore`
- `.github/`

**Everything else at root → MOVE to appropriate location above**

---

## 3. Import Update Plan

### 3.1 Python Imports (repo_intelligence → runtime.foundation.repository)

| Old Import | New Import |
|------------|------------|
| `from repo_intelligence.graph import graph_service` | `from runtime.foundation.repository.graph import graph_service` |
| `from repo_intelligence.builder import builder` | `from runtime.foundation.repository.builder import builder` |
| `from repo_intelligence.query import query` | `from runtime.foundation.repository.query import query` |
| `from repo_intelligence.analysis import impact, metrics` | `from runtime.foundation.repository.analysis import impact, metrics` |
| `from repo_intelligence.validation import validator` | `from runtime.foundation.repository.validation import validator` |
| `from repo_intelligence import scanner` | `from runtime.foundation.repository.scanner import scanner` |
| `from repo_intelligence import index` | `from runtime.foundation.repository.api import index` |
| `import repo_intelligence` | `import runtime.foundation.repository` |

### 3.2 Python Imports (verification → runtime.foundation.verification)

| Old Import | New Import |
|------------|------------|
| `from verification import runtime` | `from runtime.foundation.verification import runtime` |
| `from verification import registry` | `from runtime.foundation.verification.registry import registry` |
| `from verification import planner` | `from runtime.foundation.verification.planner import planner` |
| `import verification` | `import runtime.foundation.verification` |

### 3.3 TypeScript Imports (context-runtime → runtime.system.context)

| Old Import | New Import |
|------------|------------|
| `import { ContextRuntime } from 'context-runtime'` | `import { ContextRuntime } from '@clarifin/runtime/system/context'` |
| `import { ContextManager } from 'context-runtime/src/ContextManager'` | `import { ContextManager } from '@clarifin/runtime/system/context/src/workspace/ContextManager'` |
| `import { ContextWorkspace } from 'context-runtime/src/ContextWorkspace'` | `import { ContextWorkspace } from '@clarifin/runtime/system/context/src/workspace/ContextWorkspace'` |
| `import { ContextHistory } from 'context-runtime/src/ContextHistory'` | `import { ContextHistory } from '@clarifin/runtime/system/context/src/history/ContextHistory'` |
| `import { ContextSelection } from 'context-runtime/src/ContextSelection'` | `import { ContextSelection } from '@clarifin/runtime/system/context/src/selection/ContextSelection'` |
| `import { ContextNavigation } from 'context-runtime/src/ContextNavigation'` | `import { ContextNavigation } from '@clarifin/runtime/system/context/src/navigation/ContextNavigation'` |
| `import { ContextSerialization } from 'context-runtime/src/ContextSerialization'` | `import { ContextSerialization } from '@clarifin/runtime/system/context/src/serialization/ContextSerialization'` |
| `import { ContextValidation } from 'context-runtime/src/ContextValidation'` | `import { ContextValidation } from '@clarifin/runtime/system/context/src/validation/ContextValidation'` |
| `import { ContextTypes } from 'context-runtime/src/types'` | `import { ContextTypes } from '@clarifin/runtime/system/context/src/models/types'` |

### 3.4 Package.json / tsconfig.json Path Aliases

Add to `package.json`:
```json
{
  "imports": {
    "@clarifin/runtime/foundation/*": "./runtime/foundation/*/src",
    "@clarifin/runtime/system/*": "./runtime/system/*/src"
  }
}
```

Add to `tsconfig.json`:
```json
{
  "compilerOptions": {
    "paths": {
      "@clarifin/runtime/foundation/*": ["runtime/foundation/*/src"],
      "@clarifin/runtime/system/*": ["runtime/system/*/src"]
    }
  }
}
```

---

## 4. Migration Phases (CRITICAL: Execute Sequentially)

### Phase 0: Pre-Migration Intelligence (NO FILE MOVES)

**Purpose:** Map every import that will break. Establish green baseline. Create rollback point.

```bash
# 0.1: Map all external imports that reference paths to be moved
grep -rn "repo_intelligence" backend/ .github/ tools/ --include="*.py" --include="*.yml" --include="*.sh" 2>/dev/null | tee /tmp/repo_intelligence_imports.txt

grep -rn "from verification\|import verification" backend/ .github/ tools/ --include="*.py" --include="*.yml" 2>/dev/null | grep -v "__pycache__" | tee /tmp/verification_imports.txt

grep -rn "context-runtime" frontend/ --include="*.ts" --include="*.tsx" --include="*.json" 2>/dev/null | tee /tmp/context_runtime_imports.txt

grep -rn "repo_intelligence\|context-runtime\|verification/" .github/ 2>/dev/null | tee /tmp/workflow_path_references.txt

# Count files to update
wc -l /tmp/repo_intelligence_imports.txt
wc -l /tmp/verification_imports.txt
wc -l /tmp/context_runtime_imports.txt
wc -l /tmp/workflow_path_references.txt

# 0.2: Establish green baseline
cd backend && python -m pytest tests/ -q --tb=no 2>&1 | tail -5
# Record: ___ passing, ___ failing, ___ errors

cd frontend && npx tsc --noEmit 2>&1 | wc -l
# Record: ___ TypeScript errors before migration

cd frontend && npm test 2>&1 | tail -5
# Record: frontend test status

# 0.3: Create backup branch
git checkout -b migration/repository-restructure
git add -A && git commit -m "Pre-migration baseline: all tests passing"

# 0.4: Dependency audit for each runtime to be moved
# Python: who imports repo_intelligence? what does it import?
# TypeScript: who imports context-runtime? what does it import?
python -c "
import sys, ast, os
for root, dirs, files in os.walk('repo_intelligence'):
    for f in files:
        if f.endswith('.py'):
            with open(os.path.join(root, f)) as fp:
                try:
                    tree = ast.parse(fp.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                print(f'repo_intelligence/{f}: imports {alias.name}')
                        elif isinstance(node, ast.ImportFrom):
                            print(f'repo_intelligence/{f}: from {node.module} import ...')
                except: pass
"
# Save output: /tmp/repo_intelligence_dependencies.txt
```

**Phase 0 Deliverable:** Intelligence Report with:
- Test baseline counts
- Complete import maps for each runtime
- Dependency audit for each runtime
- Go/No-go decision

---

### Phase 1: Directory Scaffolding (NO FILE MOVES)

Create all destination directories first. Empty directories cannot break imports.

```bash
# Priority 1: Directories receiving moved files
mkdir -p runtime/foundation/repository/{api,builder,graph,scanner,query,analysis,validation,cli,models}
mkdir -p runtime/foundation/verification/{api,planner,registry,models,validation,cli}
mkdir -p runtime/system/context/src/{workspace,history,selection,navigation,serialization,validation,models,cli}

# Priority 2: Stub directories (just README.md)
mkdir -p runtime/system/{evidence,financial,timeline,graph,command,intelligence}

# Priority 3: Supporting directories
mkdir -p runtime/generated/{repository,verification}
mkdir -p testing/runtime/{foundation/{repository,verification},system/context}
mkdir -p docs/runtimes/{foundation/{repository,verification},system/context}
mkdir -p docs/reports/{architecture,implementation,verification,performance,audits,completion}
mkdir -p tools/{generators,verification,migration,auditing,diagnostics,development}

git add -A
git commit -m "Create runtime directory structure (empty)"
```

---

### Phase 2: Move Foundation Runtimes (ONE AT A TIME)

#### Step 2.1: Move `repo_intelligence` → `runtime/foundation/repository/`

```bash
# Pre-move checklist
find repo_intelligence -type f | wc -l                    # File count
grep -rn "from repo_intelligence" repo_intelligence/      # Internal imports
cat /tmp/repo_intelligence_imports.txt                    # External references

# Copy (NOT MOVE - keep originals until validated)
cp -r repo_intelligence/graph runtime/foundation/repository/graph
cp -r repo_intelligence/builder runtime/foundation/repository/builder
cp -r repo_intelligence/query runtime/foundation/repository/query
cp -r repo_intelligence/analysis runtime/foundation/repository/analysis
cp -r repo_intelligence/validation runtime/foundation/repository/validation
cp -r repo_intelligence/scanner runtime/foundation/repository/scanner
cp repo_intelligence/index.py runtime/foundation/repository/api/index.py
cp repo_intelligence/__main__.py runtime/foundation/repository/__main__.py
cp repo_intelligence/README.md runtime/foundation/repository/README.md

# Add __init__.py files to every directory
find runtime/foundation/repository -type d -exec touch {}/__init__.py \;

# Fix imports in MOVED FILES ONLY
# Update every "from repo_intelligence" in runtime/foundation/repository/
# to "from runtime.foundation.repository"
find runtime/foundation/repository -name "*.py" -exec sed -i 's/from repo_intelligence\./from runtime.foundation.repository./g' {} \;
find runtime/foundation/repository -name "*.py" -exec sed -i 's/import repo_intelligence/import runtime.foundation.repository/g' {} \;

# Run tests
cd backend && python -m pytest tests/ -q --tb=short
# MUST match baseline exactly

# Verify new imports work
cd /home/vasantha/AI-Projects/ClariFin_OS && python -c "
import sys
sys.path.insert(0, '.')
from runtime.foundation.repository.graph import graph_service
from runtime.foundation.repository.builder import builder
from runtime.foundation.repository.query import query
from runtime.foundation.repository.analysis import impact, metrics
from runtime.foundation.repository.validation import validator
from runtime.foundation.repository.scanner import scanner
print('repo_intelligence imports OK')
"

# ONLY if all tests pass and imports work:
rm -rf repo_intelligence/
git add -A
git commit -m "Move repo_intelligence → runtime/foundation/repository (validated)"
```

#### Step 2.2: Move `verification` → `runtime/foundation/verification/`

```bash
# Pre-move checklist
find verification -type f | wc -l
grep -rn "from verification\|import verification" verification/
cat /tmp/verification_imports.txt

# IMPORTANT: If verification imports repo_intelligence,
# those imports must already be updated to runtime.foundation.repository

# Copy (NOT MOVE)
cp -r verification/runtime.py runtime/foundation/verification/runtime.py
cp -r verification/registry.py runtime/foundation/verification/registry/registry.py
cp -r verification/planner.py runtime/foundation/verification/planner/planner.py
cp verification/__init__.py runtime/foundation/verification/__init__.py

# Create missing directories and __init__.py
mkdir -p runtime/foundation/verification/{api,planner,registry,models,validation,cli}
find runtime/foundation/verification -type d -exec touch {}/__init__.py \;

# Fix imports in MOVED FILES ONLY
find runtime/foundation/verification -name "*.py" -exec sed -i 's/from verification\./from runtime.foundation.verification./g' {} \;
find runtime/foundation/verification -name "*.py" -exec sed -i 's/import verification/import runtime.foundation.verification/g' {} \;

# Run tests
cd backend && python -m pytest tests/ -q --tb=short
# MUST match baseline exactly

# Verify new imports work
python -c "
import sys
sys.path.insert(0, '.')
from runtime.foundation.verification import runtime
from runtime.foundation.verification.registry import registry
from runtime.foundation.verification.planner import planner
print('verification imports OK')
"

# ONLY if all tests pass and imports work:
rm -rf verification/
git add -A
git commit -m "Move verification → runtime/foundation/verification (validated)"
```

---

### Phase 3: Move System Runtimes

#### Step 3.1: Move `context-runtime` → `runtime/system/context/`

```bash
# Pre-move checklist
find context-runtime -type f | wc -l
cat /tmp/context_runtime_imports.txt

# Baseline
cd frontend && npx tsc --noEmit 2>&1 | wc -l
cd frontend && npm test 2>&1 | tail -5

# Copy (NOT MOVE)
cp -r context-runtime/src/* runtime/system/context/src/
cp context-runtime/package.json runtime/system/context/package.json
cp context-runtime/README.md runtime/system/context/README.md

# Move tests to testing/
mkdir -p testing/runtime/system/context
cp -r context-runtime/tests/* testing/runtime/system/context/

# Update tsconfig.json path aliases (add before import fixes)
# See section 3.4

# Fix imports in MOVED FILES ONLY
# Update every "context-runtime" import in runtime/system/context/
# to "@clarifin/runtime/system/context"
find runtime/system/context -name "*.ts" -exec sed -i "s|context-runtime|@clarifin/runtime/system/context|g" {} \;

# Fix imports in FRONTEND
find frontend -name "*.ts" -o -name "*.tsx" -exec sed -i "s|context-runtime|@clarifin/runtime/system/context|g" {} \;

# Run typecheck
cd frontend && npx tsc --noEmit
# MUST have same or fewer errors than baseline

# Run frontend tests
cd frontend && npm test
# MUST pass

# ONLY if typecheck and tests pass:
rm -rf context-runtime/
git add -A
git commit -m "Move context-runtime → runtime/system/context (validated)"
```

#### Step 3.2: Create Minimal Stubs for Future Runtimes

```bash
# For each: evidence, financial, timeline, graph, command, intelligence
for runtime in evidence financial timeline graph command intelligence; do
  cat > runtime/system/${runtime}/README.md <<EOF
# ${runtime^} Runtime

**Status:** Planned — Not yet implemented.

**Scheduled for:** Program $(case $runtime in
  evidence) echo 4 ;;
  financial) echo 5 ;;
  intelligence) echo 8 ;;
  *) echo "Future" ;;
esac) (see docs/architecture/)

**Purpose:** $(case $runtime in
  evidence) echo "Evidence storage, ingestion, and retrieval" ;;
  financial) echo "Financial instruments, pricing, risk, and portfolio management" ;;
  intelligence) echo "Reasoning, planning, synthesis, and retrieval" ;;
  graph) echo "Graph investigation, projection, traversal, and visualization" ;;
  timeline) echo "Chronology, windows, playback, snapshots, and anchors" ;;
  command) echo "Command parsing, routing, execution, and completion" ;;
esac)

**Dependencies:** runtime/foundation/repository, runtime/foundation/verification

Do not import from this runtime.
Do not write tests for this runtime.
Do not document APIs that do not exist.
EOF
done

git add -A
git commit -m "Create stub runtimes with README.md only (no implementation yet)"
```

---

### Phase 4: Update Supporting Files

```bash
# 4.1: Update .github/ workflow files
# Update any workflow referencing old paths
grep -rn "repo_intelligence\|context-runtime\|verification/" .github/
# Fix each reference manually

# 4.2: Update tools/ references
# Move tools per move map section 2.7
# Update any internal imports in tools/

# 4.3: Update pyproject.toml / pytest configuration
# Ensure pytest does NOT discover tests in runtime/ source

# 4.4: Update .gitignore - Generated artifacts strategy (DECISION REQUIRED)
# See "Generated Artifacts Strategy" section below

# 4.5: Root cleanup
# Move reports and audits per move map 2.8
# Verify root contains ONLY permitted files
```

---

### Phase 5: Documentation (FOR IMPLEMENTED RUNTIMES ONLY)

```
Each IMPLEMENTED runtime needs 4 documents:
runtime/foundation/repository/
├── README.md           ← Update from moved repo_intelligence/README.md
├── ARCHITECTURE.md     ← Write based on existing code
├── PUBLIC_API.md       ← Document actual exported functions
└── EXTENSION_GUIDE.md  ← How to add new analysis modules

runtime/foundation/verification/
├── README.md           ← Write from existing
├── ARCHITECTURE.md     ← Write based on existing code
├── PUBLIC_API.md       ← Document actual API
└── EXTENSION_GUIDE.md  ← How to add new verification types

runtime/system/context/
├── README.md           ← Update from context-runtime/README.md
├── ARCHITECTURE.md     ← Write based on existing TypeScript code
├── PUBLIC_API.md       ← Document exported types and functions
└── EXTENSION_GUIDE.md  ← How to add new context sources

Each STUB runtime needs ONLY:
runtime/system/{evidence,financial,timeline,graph,command,intelligence}/
└── README.md           ← Already created in Phase 3.2
```

---

## 5. Generated Artifacts Strategy (DECISION REQUIRED BEFORE MIGRATION)

### Recommended: Hybrid Approach

| Directory | Strategy | Rationale |
|-----------|----------|-----------|
| `runtime/generated/repository/index.json` | **COMMIT** | Small, stable, enables CI to skip build |
| `runtime/generated/repository/graph.json` | **COMMIT** | Small, stable |
| `runtime/generated/repository/cache/` | **GITIGNORE** | Large, ephemeral |
| `runtime/generated/verification/` | **GITIGNORE** | Not yet implemented |
| `runtime/generated/{evidence,financial,...}` | **GITIGNORE** | Not yet implemented |

### .gitignore entries to add:
```
# Generated artifacts
runtime/generated/*/cache/
runtime/generated/verification/
runtime/generated/evidence/
runtime/generated/financial/
runtime/generated/timeline/
runtime/generated/graph/
runtime/generated/command/
runtime/generated/intelligence/
```

### Document in ARCHITECTURE.md:
> "runtime/generated/repository/index.json and graph.json are committed because they enable CI jobs to skip the build step when the repository structure has not changed. Update them by running: `python -m runtime.foundation.repository.builder`. Cache directories are gitignored."

---

## 6. Verification Plan

### 6.1 Per-Runtime Validation (After Each Phase 2/3 Step)

```bash
# After EACH runtime move:
# 1. Backend tests pass (same count as baseline)
cd backend && python -m pytest tests/ -q --tb=no

# 2. New imports resolve
python -c "from runtime.foundation.repository.graph import graph_service; print('OK')"

# 3. Checksum verification
find runtime/foundation/runtime/system -type f \( -name "*.py" -o -name "*.ts" \) | xargs sha256sum > /tmp/checksums_<runtime>.txt
# Compare with pre-move checksums for that runtime
```

### 6.2 Full Validation (After All Moves Complete)

```bash
# 1. All backend tests pass
cd backend && python -m pytest tests/ -v --tb=short

# 2. All frontend tests pass
cd frontend && npm test

# 3. TypeScript clean
cd frontend && npx tsc --noEmit

# 4. All runtime imports resolve
python -c "
from runtime.foundation.repository.graph import graph_service
from runtime.foundation.repository.builder import builder
from runtime.foundation.repository.query import query
from runtime.foundation.repository.analysis import impact, metrics
from runtime.foundation.repository.validation import validator
from runtime.foundation.repository.scanner import scanner
from runtime.foundation.verification import runtime
from runtime.foundation.verification.registry import registry
from runtime.foundation.verification.planner import planner
print('All foundation imports OK')
"

# 5. No source files in generated/
find runtime/generated -type f \( -name "*.py" -o -name "*.ts" \) | grep -v "\.json$" && echo "ERROR: Source files in generated/" || echo "OK"

# 6. No tests in runtime source
find runtime/foundation runtime/system -name "*test*" -o -name "*_test*" | grep -v __pycache__ && echo "ERROR: Tests found in runtime source" || echo "OK"

# 7. Tests in correct location
find testing/runtime -name "*.test.ts" -o -name "*_test.py" | head -20

# 8. CI/CD pipeline passes
```

---

## 7. Risk Analysis & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Broken Python imports** | High | High | Move ONE runtime at a time; validate after each; keep originals until validated |
| **Broken TypeScript imports** | High | High | Update path aliases BEFORE fixing imports; typecheck after context-runtime move |
| **Test discovery failures** | Medium | High | DO NOT MOVE `backend/tests`, `frontend/tests`, `frontend/__tests__` |
| **Generated artifacts in source** | Medium | Medium | Move all `*.json` index files to `runtime/generated/`; .gitignore cache/ |
| **Circular dependencies** | Low | High | Run `madge --circular` on TypeScript; `pydeps` on Python pre-migration |
| **Missing files** | Low | High | Checksum verification per-runtime; git history as backup |
| **Symlink breakage** | Low | Medium | Audit with `find -L` before moving; preserve symlinks |
| **Tooling path assumptions** | Medium | Medium | Update `package.json` scripts, `pyproject.toml`, CI configs in Phase 4 |
| **Documentation link rot** | Medium | Low | Update relative links in moved markdown files |
| **Stubs creating false completeness** | Medium | Low | Only 1 README.md per stub; no ARCHITECTURE.md until implemented |

---

## 8. Sign-Off Criteria (REVISED)

Migration is complete ONLY when:

- [ ] All files moved per Move Map (checksum verified per-runtime)
- [ ] All Python imports resolve (`python -c "import runtime.foundation.repository..."`)
- [ ] All TypeScript imports resolve (`npx tsc --noEmit`)
- [ ] `backend/tests` pass 100% (same count as baseline)
- [ ] `frontend/tests` pass 100%
- [ ] `frontend/__tests__` pass 100%
- [ ] `testing/runtime` tests discover and run
- [ ] **No tests in any `runtime/` source directory**
- [ ] **No source files in any `runtime/generated/` directory**
- [ ] Root directory contains ONLY permitted files
- [ ] **Implemented runtimes have 4 docs** (README.md, ARCHITECTURE.md, PUBLIC_API.md, EXTENSION_GUIDE.md)
- [ ] **Stub runtimes have exactly 1 README.md** stating status
- [ ] **Generated artifacts strategy documented** in ARCHITECTURE.md
- [ ] CI/CD pipeline passes
- [ ] No circular dependencies detected
- [ ] Migration commit history is clean (one commit per runtime moved)

---

## 9. Rollback Plan

```bash
# If ANY phase fails critically:
git checkout main
# Everything restored to pre-migration baseline

# Or restore specific phase:
git checkout migration/repository-restructure~<N>
# Where N is number of commits to go back
```

---

## 10. Post-Migration Lock

After sign-off, this architecture is **LOCKED**. Future changes must:

1. Add new runtimes ONLY under `runtime/foundation/` or `runtime/system/`
2. Follow domain-specific internal structure (no generic `api/core/models` unless domain-appropriate)
3. Place generated artifacts ONLY in `runtime/generated/<runtime-name>/`
4. Place runtime tests ONLY in `testing/runtime/<foundation|system>/<name>/`
5. Place runtime docs in `docs/runtimes/<foundation|system>/<name>/`
6. Place tools in `tools/<generators|verification|migration|auditing|diagnostics|development>/`
7. Place reports in `docs/reports/<architecture|implementation|verification|performance|audits|completion>/`
8. Never place source code, tests, or generated files in root
9. **Stubs remain stubs** until implementation begins — only then add full documentation

---

*Plan Version: 1.0 (LOCKED)*
*Architect: Principal Software Architect, ClariFin_OS*
*Date: 2026-07-31*