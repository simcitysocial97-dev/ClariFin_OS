# GitHub Actions Audit

Generated: 2026-08-05

## Workflow Inventory

| Filename | Trigger | Jobs | Purpose | Artifacts | Dependencies | Est. Runtime | Status |
|----------|---------|------|---------|-----------|--------------|--------------|--------|
| backend-verify.yml | push, pull_request | 1 | Backend verification via runtime | cross-layer-map, verification-report, verification-cache, evidence | Python 3.12 | 30 min | KEEP |
| backend.yml | WORKFLOW_DISPATCH ONLY | 12 | Full backend suite (retired) | intelligence-plan, property-results, contract-results, coverage-full, intelligence-reports, quality-report | path-filter, Python | 30+ min | **DELETE** |
| ci.yml | WORKFLOW_DISPATCH ONLY | 5 | CI pipeline (retired) | vitest-coverage, next-build, playwright-report | Node 24, Python 3.12 | 45+ min | **DELETE** |
| frontend-build.yml | push, pull_request | 1 | Frontend build verification | bundle size | Node.js | 10 min | KEEP |
| frontend.yml | pull_request | 2 | Frontend-backend sync | openapi-schema, cross-layer-map, verification-report, verification-cache | Python, Node.js, backend routers | 15 min | **MERGE** |
| full-validation.yml | WORKFLOW_DISPATCH ONLY | 3 | Full stack validation (retired) | - | - | 30 min | **DELETE** |
| golden.yml | schedule, workflow_dispatch | 2 | Golden dataset regression | golden-results, regression-comparison | Python 3.12 | 30 min | KEEP |
| mutation.yml | schedule, workflow_dispatch | 3 | Mutation testing | mutation logs, mutation-report | Python 3.12 | 90 min | KEEP |
| nightly-property-tests.yml | schedule, workflow_dispatch | 2 | Nightly property + perf tests | property-test-results, performance-test-results | Python 3.12 | 120 min | **DELETE** |
| playwright.yml | push, pull_request | 1 | E2E Playwright tests | playwright-report, test-results | Node.js 20, Python 3.12 | 60 min | KEEP |
| quality.yml | push, pull_request | 5 | Quality gate | coverage-unit, intelligence-quality | Python 3.12 | 20 min | KEEP |
| verification-runtime.yml | push, pull_request | 1 | Runtime self-validation | verification-quality, verification-performance, observability-artifacts | Python 3.12 | 30 min | KEEP |

## Classification Summary

### KEEP (7 workflows)
- **backend-verify.yml** - Canonical backend verification
- **frontend-build.yml** - Frontend build verification  
- **golden.yml** - Golden dataset regression tests (scheduled)
- **mutation.yml** - Mutation testing (scheduled)
- **playwright.yml** - E2E browser tests
- **quality.yml** - Fast quality gate with lint, unit tests, architecture
- **verification-runtime.yml** - Programs 7-11 runtime self-validation

### DELETE (3 workflows)
- **backend.yml** - Marked RETIRED, superseded by backend-verify.yml
- **ci.yml** - Marked SUPERSEDED, only workflow_dispatch trigger
- **full-validation.yml** - Marked SUPERSEDED, only workflow_dispatch trigger
- **nightly-property-tests.yml** - Duplicate function with mutation.yml

### MERGE (1 workflow)
- **frontend.yml** - Frontend-backend sync verification - can be integrated into backend-verify.yml

### SUPERSEDED
All deprecated workflows are already disabled (workflow_dispatch only).

### EXPERIMENTAL
None identified.

## Duplicate Verification Analysis

| Artifact | Produced By | Conflict? |
|----------|-------------|-----------|
| cross-layer-map | backend-verify.yml, frontend.yml | YES - duplicates production |
| TypeScript check | quality.yml (frontend job), frontend-build.yml | PARTIAL - different scope |
| Backend unit tests | quality.yml, backend.yml | YES (backend.yml retired) |
| Ruff check | quality.yml | SINGLE |
| Ruff check | ci.yml | YES (ci.yml retired) |

## Recommendations

1. Delete obsolete workflows: `backend.yml`, `ci.yml`, `full-validation.yml`
2. Merge `frontend.yml` into `backend-verify.yml` or `frontend-build.yml`
3. Remove `nightly-property-tests.yml` (redundant with mutation.yml schedule)
4. Standardize naming conventions across remaining workflows
5. Ensure single-source artifact generation

## Artifact Pipeline Flow

```
Cross-layer map → Verification Planner → Verification Runtime → Evidence → Observability → Knowledge Index → Engineering Reports
```

No workflow should regenerate artifacts that already exist earlier in the pipeline.