# Program 1 – Verification Infrastructure Foundation

## Audit Report & Implementation Plan

---

## 1. Workflow Inventory

### Active Workflows (10 total)

| Workflow | File | Triggers | Jobs | Purpose |
|----------|------|----------|------|---------|
| **CI** | `ci.yml` | `workflow_dispatch` only (disabled) | 6 jobs | Full CI pipeline (superseded) |
| **Quality Gate** | `quality.yml` | push to \*\*, PR to main/develop | 6 jobs | Fast quality gate (<5 min) |
| **Backend Full Suite** | `backend.yml` | PR to main/develop, paths: backend/\*\* | 13 jobs | Complete backend test suite |
| **Frontend-Backend Sync** | `frontend.yml` | PR to main/develop, paths: backend/src/routers/\*\*, frontend/\*\* | 1 job | OpenAPI schema sync |
| **Frontend Build** | `frontend-build.yml` | push to main/develop (frontend/\*\*), PR to main | 1 job | Frontend build + typecheck |
| **Full Stack Validation** | `full-validation.yml` | `workflow_dispatch` only (disabled) | 3 jobs | Full stack (superseded) |
| **Nightly Property Tests** | `nightly-property-tests.yml` | schedule (2 AM UTC), workflow_dispatch | 2 jobs | Property + performance tests |
| **Playwright E2E** | `playwright.yml` | push/PR to main/master/develop, workflow_dispatch | 1 job | E2E tests |
| **Mutation Testing** | `mutation.yml` | schedule (2 AM UTC), workflow_dispatch | 3 jobs | Mutation testing (nightly) |
| **Golden Dataset** | `golden.yml` | schedule (3 AM UTC), workflow_dispatch | 2 jobs | Golden dataset regression |

---

## 2. Job & Dependency Analysis

### quality.yml (Quality Gate - Fast)
```
lint (5 min)
  └─► unit-tests (10 min) ──► quality-gate
  └─► architecture (5 min)  ──► quality-gate
  └─► meta (5 min)          ──► quality-gate
  └─► intelligence-quality  ──► quality-gate
```

### backend.yml (Full Backend Suite)
```
detect-changes ──► intelligence-analysis
                     │
                     ├─► property-tests (15 min) ──┐
                     ├─► contract-tests (10 min) ──┤
                     ├─► capability-tests (10 min) ─┤
                     ├─► invariant-tests (10 min)  ──► integration-tests (15 min) ──┐
                     ├─► migration-tests (10 min)  ────────────────────────────────┤
                     └─► capability-validation (15 min) ──────────────────────────────┤
                                                                                     ├─► coverage-report (15 min)
                                                                                     ├─► determinism-check (10 min)
                                                                                     └─► intelligence-reports
                                                                                     └─► quality-report
```

### mutation.yml (Nightly Mutation)
```
discover ──► mutation-engines[matrix: 6 engines] (90 min) ──► mutation-report (15 min)
```

### ci.yml (Superseded - Manual Only)
```
frontend-static (10 min) ──► frontend-tests (10 min) ──► build (15 min) ──► e2e (20 min)
backend-static (10 min) ──► backend-tests (10 min) ──────────────────────────┘
security (10 min) ──────────────────────────────────────────────────────────► (independent)
```

---

## 3. Duplicated Steps Across Workflows

| Step | Workflows Using It | Count |
|------|-------------------|-------|
| `actions/checkout@v4` | All 10 workflows | 10 |
| `actions/setup-python@v5` | 8 workflows (all but frontend-build) | 8 |
| `actions/setup-node@v4` | 4 workflows (ci, frontend-build, playwright, ci security) | 4 |
| `pip install -r backend/requirements.txt` | 7 workflows | 7 |
| `npm ci` (frontend) | 4 workflows | 4 |
| `actions/upload-artifact@v4` | 9 workflows | 9 |
| `actions/download-artifact@v4` | 3 workflows | 3 |

---

## 4. Cache Usage Analysis

| Workflow | Python Cache | Node Cache | Pip Cache | Notes |
|----------|-------------|------------|-----------|-------|
| quality.yml | ✅ via action | ❌ | ✅ via action | Uses composite action |
| backend.yml | ✅ via action | ❌ | ✅ via action | Uses composite action |
| mutation.yml | ✅ via action | ❌ | ✅ via action | Uses composite action |
| golden.yml | ✅ via action | ❌ | ✅ via action | Uses composite action |
| ci.yml | ✅ inline | ✅ inline | ✅ inline | Duplicated setup |
| nightly-property-tests.yml | ✅ inline | ❌ | ✅ inline | Duplicated setup |
| playwright.yml | ✅ inline | ✅ inline | ✅ inline | Duplicated setup |
| frontend.yml | ✅ via action | ❌ | ✅ via action | Uses composite action |
| frontend-build.yml | ❌ | ✅ inline | ❌ | No composite action |
| full-validation.yml | ✅ inline | ✅ inline | ✅ inline | Duplicated setup |

**Missing Caches:**
- frontend-build.yml: No pip cache (not needed), but Node cache present
- Several workflows use inline setup instead of composite action

---

## 5. Artifact Production Summary

| Workflow | Artifacts Produced | Retention |
|----------|-------------------|-----------|
| quality.yml | coverage-unit, coverage.xml (Codecov) | 30 days |
| backend.yml | property-results, contract-results, coverage-full, intelligence-reports, quality-report | 30-90 days |
| mutation.yml | mutation-{engine}, mutation-report | 90 days |
| golden.yml | golden-results | 90 days |
| ci.yml | vitest-coverage, next-build, playwright-report | 1-7 days |
| nightly-property-tests.yml | property-test-results, performance-test-results | 7 days |
| playwright.yml | playwright-report, test-results | 7-30 days |

---

## 6. Missing Job Summaries

**Workflows without GitHub Job Summaries:**
- quality.yml - Has quality-gate summary job but no markdown summary
- backend.yml - No summary job
- mutation.yml - Has mutation-report job but no PR comment summary
- golden.yml - Has regression-comparison but no summary
- ci.yml - No summary
- nightly-property-tests.yml - No summary
- playwright.yml - Has PR comment but no job summary
- frontend.yml - No summary
- frontend-build.yml - No summary
- full-validation.yml - No summary

---

## 7. Reusable Actions Inventory

| Action | Path | Used By |
|--------|------|---------|
| setup-python-env | `.github/actions/setup-python-env/action.yml` | quality.yml, backend.yml, mutation.yml, golden.yml, frontend.yml |

**Missing Composite Actions:**
- ❌ setup-node-env (Node.js setup with npm cache)
- ❌ setup-playwright (Playwright browser install + cache)
- ❌ upload-test-results (Standardized artifact upload)
- ❌ job-summary (Standardized GitHub Job Summary)

---

## 8. Helper Scripts Inventory

| Script | Path | Consumed By |
|--------|------|-------------|
| check_coverage_threshold.py | `.github/scripts/check_coverage_threshold.py` | quality.yml (unit-tests job) |
| run_contract_tests.sh | `.github/scripts/run_contract_tests.sh` | Not directly used in workflows |
| run_fast_checks.sh | `.github/scripts/run_fast_checks.sh` | Not directly used in workflows |
| run_mutation_selective.sh | `.github/scripts/run_mutation_selective.sh` | Not directly used in workflows |
| generate_mutation_report.py | `.github/scripts/generate_mutation_report.py` | mutation.yml (mutation-report job) |

---

## 9. Dependency Graph

```mermaid
graph TD
    %% Triggers
    PushAll((Push to **))
    PRMainDevelop((PR to main/develop))
    PRMain((PR to main))
    Schedule2AM((Schedule 2 AM UTC))
    Schedule3AM((Schedule 3 AM UTC))
    Manual((workflow_dispatch))
    PathsBackend((Paths: backend/**))
    PathsFrontend((Paths: frontend/**))
    PathsRouters((Paths: backend/src/routers/**))
    
    %% Workflows
    Quality[Quality Gate\nquality.yml]
    Backend[Backend Full Suite\nbackend.yml]
    FrontendSync[Frontend-Backend Sync\nfrontend.yml]
    FrontendBuild[Frontend Build\nfrontend-build.yml]
    NightlyProps[Nightly Property Tests\nnightly-property-tests.yml]
    Playwright[Playwright E2E\nplaywright.yml]
    Mutation[Mutation Testing\nmutation.yml]
    Golden[Golden Dataset\ngolden.yml]
    CI[CI (Superseded)\nci.yml]
    FullVal[Full Validation (Superseded)\nfull-validation.yml]
    
    %% Dependencies
    PushAll --> Quality
    PRMainDevelop --> Quality
    PRMainDevelop --> Backend
    PRMainDevelop --> FrontendSync
    PathsBackend --> Backend
    PathsRouters --> FrontendSync
    PathsFrontend --> FrontendBuild
    PRMain --> FrontendBuild
    Schedule2AM --> NightlyProps
    Schedule2AM --> Mutation
    Schedule3AM --> Golden
    Manual --> NightlyProps
    Manual --> Mutation
    Manual --> Golden
    Manual --> Playwright
    Manual --> CI
    Manual --> FullVal
    PushAll --> Playwright
    PRMainDevelop --> Playwright
    
    %% Shared Actions
    SetupPython[setup-python-env action] -.-> Quality
    SetupPython -.-> Backend
    SetupPython -.-> Mutation
    SetupPython -.-> Golden
    SetupPython -.-> FrontendSync
    
    %% CI Target Derivation
    Backend -.-> CiTargets[ci_targets.py]
    NightlyProps -.-> CiTargets
    Mutation -.-> CiTargets
    
    %% Intelligence Layer
    Backend -.-> Intelligence[verification_intelligence]
    Quality -.-> Intelligence
    Mutation -.-> Intelligence
```

---

## 10. Consolidation Recommendations

| Workflow | Recommendation | Rationale |
|----------|---------------|-----------|
| `ci.yml` | **RETIRE** | Superseded by quality.yml + backend.yml + frontend-build.yml + playwright.yml |
| `full-validation.yml` | **RETIRE** | Superseded, disabled triggers |
| `frontend.yml` + `frontend-build.yml` | **MERGE** | Both test frontend; different triggers can be unified |
| `nightly-property-tests.yml` | **KEEP** | Distinct nightly schedule |
| `mutation.yml` | **KEEP** | Distinct nightly schedule, specialized |
| `golden.yml` | **KEEP** | Distinct nightly schedule, specialized |
| `playwright.yml` | **KEEP** | E2E testing distinct from unit/integration |
| `quality.yml` | **KEEP** | Fast quality gate for every push |
| `backend.yml` | **KEEP** | Comprehensive backend suite for PRs |

---

## 11. Implementation Plan - Safe Infrastructure Improvements

### Phase A: Create Composite Actions
1. **`.github/actions/setup-node-env/action.yml`** - Node.js + npm cache
2. **`.github/actions/setup-playwright/action.yml`** - Playwright browser install + cache
3. **`.github/actions/upload-test-artifacts/action.yml`** - Standardized artifact upload
4. **`.github/actions/job-summary/action.yml`** - Standardized GitHub Job Summary

### Phase B: Standardize Cache Usage
- Update workflows using inline `actions/setup-node` and `actions/setup-python` to use composite actions
- Add missing pip cache keys where absent

### Phase C: Standardize Artifact Upload & Job Summaries
- Replace ad-hoc `actions/upload-artifact` with composite action
- Add job summary generation to all workflows

### Phase D: Create Verification Runtime Folder
- `verification/runtime/cli.py` - CLI entry point
- `verification/runtime/orchestrator.py` - Orchestration logic
- `verification/verification.yaml` - Placeholder configuration

---

## 12. Files to Create

| File | Purpose |
|------|---------|
| `.github/actions/setup-node-env/action.yml` | Composite action for Node.js setup |
| `.github/actions/setup-playwright/action.yml` | Composite action for Playwright |
| `.github/actions/upload-test-artifacts/action.yml` | Composite action for artifact upload |
| `.github/actions/job-summary/action.yml` | Composite action for job summaries |
| `verification/runtime/cli.py` | CLI entry point |
| `verification/runtime/orchestrator.py` | Orchestration logic |
| `verification/verification.yaml` | Placeholder config |

---

## 13. Files to Modify

| File | Changes |
|------|---------|
| `quality.yml` | Use composite actions, add job summary |
| `backend.yml` | Use composite actions, add job summary |
| `frontend-build.yml` | Use setup-node-env action, add job summary |
| `playwright.yml` | Use setup-playwright action, add job summary |
| `mutation.yml` | Add job summary |
| `golden.yml` | Add job summary |
| `nightly-property-tests.yml` | Use composite actions, add job summary |
| `ci.yml` | Add retired notice, use composite actions |
| `full-validation.yml` | Add retired notice |

---

## 14. Risks & Assumptions

**Risks:**
1. Composite actions may break existing workflows if inputs/outputs mismatch
2. Cache key changes may cause cache misses initially
3. Job summary format may need iteration

**Assumptions:**
1. Python 3.12 is the standard version (per pyproject.toml)
2. Node.js 20 is the standard version (per frontend package.json)
3. Existing workflow triggers must not change
4. No test behavior changes allowed
5. Verification intelligence layer exists at `backend/src/verification/`

---

## 15. Acceptance Criteria Verification

| Criteria | Status |
|----------|--------|
| Existing CI remains fully functional | ✅ Will verify after changes |
| All changes additive or refactoring-only | ✅ |
| No test behavior changes | ✅ |
| Repository prepared for Program 2 | ✅ |