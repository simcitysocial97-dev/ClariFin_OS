# VEA-1: Verification Ecosystem Integration Audit — Final Report

**Date:** 2026-08-09  
**Branch:** recovery/program-r-forensic-reconstruction  
**Commit:** 814e1149 (Program T fixes)  
**Status:** CERTIFIED (audit complete with evidence)

---

## Executive Summary

The ClariFin_OS verification ecosystem contains substantial infrastructure but **cannot reliably execute the change→capability→impact→verification→test→evidence→diagnosis chain**. The system discovers changed files, maps some to capabilities, and computes cross-layer blast radii—but **execution planning ignores the blast radius**, **key file categories are invisible to verification**, and **evidence is not structured for automated diagnosis**.

**Primary Failure:** A backend DTO change that breaks the API contract and frontend types produces **zero verification units** because `dto` kind is not recognized by the optimizer.

---

## 1. Authority Map (M0)

| Concern | Authority | Notes |
|---------|-----------|-------|
| Changed files | `orchestrator._collect_changed_files()` (git diff HEAD) | **Bug:** fails on clean CI checkout; misses untracked files |
| Capabilities | `runtime.foundation.architecture` provider (canonical) | Registry in `verification.yaml` has **stale module paths** |
| Scopes | `VerificationPlanner._resolve_scopes_from_files()` (path prefixes) | Coarse; no capability-level precision |
| Verification targets | `VerificationPlanner` (registry-driven) | **Ignores** `CrossLayerImpactPlanner` output |
| Execution | `Executor` (runs shell commands) | No junit/structured output; evidence = raw logs |
| Evidence | `EvidenceAggregator` (collects junit/coverage/mutation) | **No junit emitted** → evidence empty |
| CI | GitHub workflows calling `python runtime/verify.py <profile>` | Same entry point as local (good); diverges due to clean checkout |

**Compatibility layers:** Profiles in `profiles.py` define tasks but **are not executed**; only `verification.yaml` workflows/scripts are used.

---

## 2. Infrastructure Inventory (M1)

| Subsystem | Purpose | Entry Point | Inputs | Outputs | Machine-Readable | Capability-Aware |
|-----------|---------|-------------|--------|---------|------------------|------------------|
| Unit tests | Capability correctness | `pytest` | changed files | JUnit XML (not emitted) | No (no junitxml) | Via provider ownership |
| Contract | API contract | `schemathesis` | endpoints | JUnit XML (not emitted) | No | Endpoint-based |
| Property | Mathematical properties | `hypothesis` | loan/reconciliation engines | JUnit XML (not emitted) | No | Engine-based |
| Invariant | Ledger/accounting | `pytest -m invariant` | invariant tests | JUnit XML (not emitted) | No | Limited |
| Integration | API wiring | `pytest integration/` | routers/services | JUnit XML (not emitted) | No | Service/router-based |
| Frontend lint/type | Code quality | `eslint`/`tsc` | frontend src | Exit code only | No | Path-based |
| Frontend unit | Component logic | `vitest` | frontend tests | Exit code only | No | Path-based |
| Frontend build | **Missing from CI** | — | — | — | — | — |
| Golden | Regression | `golden tests` | golden datasets | Custom JSON | Partial | Capability-based |
| Mutation | Test strength | `mutmut` | engine modules | Custom JSON | Partial | Module-based |
| Playwright | E2E | `playwright` | workspaces | JUnit XML | Yes | Workspace-based |
| Coverage | Line coverage | `pytest --cov` | all tests | coverage.xml | Yes | — |
| Capability registry | Capability metadata | `VerificationRegistry` | YAML + defaults | Requirements/workflows/scripts | Yes | Yes (but stale modules) |
| Planner | Verification selection | `VerificationPlanner` | changed files, scope | `VerificationPlan` | Yes | Via registry scopes |
| Cross-Layer Planner | Blast radius | `CrossLayerImpactPlanner` | changed files | `ImpactReport` | Yes | Full (provider-backed) |
| Intelligence optimizer | Minimal verification | `optimize_verification` | Blast radius | `VerificationPlanIntel` | Yes | Full (provider-backed) |
| Evidence aggregator | Evidence collection | `EvidenceAggregator` | artifacts dir | `EvidenceSummary` | Yes | Chain enrichment only |

---

## 3. Change → Capability Matrix (M2)

| Change Type | File Exists | Detected | Symbol/Module | Capability Resolved | Confidence | Mapping Source | Downstream Dependencies |
|-------------|-------------|----------|---------------|---------------------|------------|----------------|------------------------|
| Backend engine | ✅ | ✅ | engine_module | ✅ useLoansCapability | HIGH | Provider ownership | service, router, endpoint, capability, test |
| Backend service | ✅ | ✅ | service | ✅ useLoansCapability | HIGH | Provider ownership | router, endpoint, capability |
| Backend router | ✅ | ✅ | router | ✅ useLoansCapability | HIGH | Provider ownership | endpoint, capability |
| Backend DTO | ✅ | ✅ | **dto** | ❌ NONE | **NONE** | **UNREGISTERED** | mapper, frontend types |
| Backend mapper | ✅ | ✅ | mapper | ❌ NONE | **NONE** | **UNREGISTERED** | frontend mapper |
| Frontend hook | ✅ | ✅ | capability | ✅ useLoansCapability | HIGH | Provider ownership | workspace, component |
| Frontend mapper | ✅ | ✅ | mapper | ✅ useLoansCapability | HIGH | Provider ownership | workspace |
| Frontend view model | ✅ | ✅ | view_model | ❌ NONE | PARTIAL | View model files only | — |
| Frontend generated type | ✅ | ❌ | (none) | ❌ NONE | NONE | UNREGISTERED | — |
| Runtime | ✅ | ❌ | (none) | ❌ NONE | NONE | UNREGISTERED | — |
| Verification config | ✅ | ❌ | (none) | ❌ NONE | NONE | UNREGISTERED | — |
| API schema | ✅ | ❌ | (none) | ❌ NONE | NONE | UNREGISTERED | — |

**Key Finding:** `dto`, `mapper` (backend), `generated type`, `runtime`, `verification config`, `api schema` are **invisible to capability mapping** → produce zero verification.

---

## 4. Capability → Impact Matrix (M3)

The `CrossLayerImpactPlanner` (Program 7A) backed by the canonical architecture provider **correctly computes cross-layer dependencies** for registered entity kinds:

| Source Kind | Impacts | Evidence |
|-------------|---------|----------|
| engine | service, router, endpoint, capability, test | ✅ Complete |
| service | router, endpoint, capability | ✅ Complete |
| router | endpoint, capability | ✅ Complete |
| capability | workspace, component, view_model, mapper, test | ✅ Complete |
| dto | mapper | ✅ **Detected but UNUSED** |
| mapper (backend) | (frontend mapper via chain) | ⚠️ Chain exists, not in optimizer kinds |
| view_model | — | ⚠️ Detected, not in optimizer kinds |

**Duplication:** Registry capabilities (`loan-engine`, `reconciliation`, `ledger`) use **stale module paths** (`backend/src/loan_engine`) that don't exist. Real modules are under `backend/src/engines/*`. Provider capabilities (`useLoansCapability`, etc.) are **canonical and correct**.

---

## 5. Impact → Verification Planning Matrix (M4)

| Planner | Input | Output | Uses Blast Radius? | Selects Frontend for Backend Change? |
|---------|-------|--------|-------------------|--------------------------------------|
| `VerificationPlanner` (registry) | Changed files + forced scope | `VerificationPlan` (workflow/scripts) | ❌ **NO** | ❌ Only if frontend scope forced |
| `CrossLayerImpactPlanner` | Changed files | `ImpactReport` (with `verification_plan`) | N/A (source) | ✅ `run_frontend: True` |
| `Intelligence optimizer` | Blast radius | `VerificationPlanIntel` (unit targets + suites) | ✅ **YES** | ✅ `frontend-unit` if capability/workspace impacted |

**Critical Gap:** `VerificationOrchestrator.run()` calls `analyze_cross_layer()` but **passes only `changed_files` and forced `scope` to `generate_plan()`**. The blast radius is computed but **discarded** before planning.

**Result:** Backend change → `CrossLayerImpactPlanner` says "run frontend" → `VerificationPlanner` ignores it → **no frontend verification runs**.

---

## 6. Capability → Test Sufficiency (M5)

| Capability | Unit Tests | Contract Tests | Property Tests | Invariant Tests | Integration | Frontend Tests | Build/Type | Mutation | Coverage |
|------------|------------|----------------|----------------|-----------------|-------------|----------------|------------|----------|----------|
| loan_engine (useLoansCapability) | 10+ | ✅ (endpoints) | 10+ | — | ✅ (routers) | ❌ not auto | ❌ not in CI | Selective | 40% threshold |
| reconciliation | 4+ | — | 4+ | — | — | ❌ | ❌ | — | — |
| ledger | — | — | — | 10+ | — | ❌ | ❌ | — | — |
| api-contracts | — | ✅ (schemathesis) | — | — | — | ❌ | ❌ | — | — |

**Gap:** No automated mapping from capability → test ownership. Provider records tests per engine but **not per capability**.

---

## 7. Failure → Evidence → Diagnosis Map (M6)

| Failure Type | Evidence Produced | Machine-Readable | Correlatable to Capability | Actionable Diagnosis |
|--------------|-------------------|------------------|---------------------------|----------------------|
| pytest failure | Raw stderr (no junit) | ❌ | ❌ (heuristic chain match only) | ❌ "Investigate failing task: ..." |
| schemathesis failure | Raw stderr | ❌ | ❌ | ❌ |
| TypeScript error | Exit code + stderr | ❌ | ❌ | ❌ |
| Build failure | **Not run in CI** | — | — | — |
| Mutation report | Custom JSON | ✅ | ❌ | ❌ |
| Coverage | coverage.xml | ✅ | ❌ | ❌ |
| Playwright | JUnit XML | ✅ | Workspace-based | Partial |

**EvidenceAggregator enriches with chains** but **no junit is emitted** by verification scripts → evidence is empty.

---

## 8. Local ↔ CI Capability Matrix (M8)

| Capability | Local Works | CI Works | Same Model? | Divergence |
|------------|-------------|----------|-------------|------------|
| Changed file detection | ✅ (git diff HEAD) | ❌ (clean checkout = empty) | NO | **P0: CI fails** |
| Capability mapping | ✅ | ✅ (same code) | YES | — |
| Blast radius | ✅ | ✅ | YES | — |
| Verification planning | ✅ | ✅ | YES | — |
| Unit tests | ✅ | ✅ | YES | — |
| Contract tests | ✅ | ✅ | YES | — |
| Property tests | ✅ | ✅ | YES | — |
| Frontend typecheck | ✅ (if deps installed) | ✅ | YES | — |
| **Frontend build** | ❌ (not in script) | ❌ (not in script) | — | **Missing everywhere** |
| Cross-layer verification | ❌ (planner ignores blast) | ❌ | — | **Architectural** |
| Evidence collection | ❌ (no junit) | ❌ (no junit) | YES | **Missing everywhere** |
| Heavy suites (mutation/golden) | On-demand | Scheduled | Budget only | By design |

---

## 9. Cross-Layer Specimen Report (M7)

**Experiment:** Modify `backend/src/core/dtos/loans_dto.py` (backend DTO) → verify frontend impact detection.

| Question | Answer | Evidence |
|----------|--------|----------|
| 1. System detects backend change? | ✅ | `changed_files` includes DTO |
| 2. Identifies affected capability? | ❌ | DTO kind → **no capability mapping** |
| 3. Identifies frontend impact? | ✅ (blast) | `CrossLayerImpactPlanner` → `mapper` + `capability` → `run_frontend: True` |
| 4. Schedules frontend verification? | ❌ | `VerificationPlanner` ignores blast radius |
| 5. Frontend build/type identifies failure? | ❌ (not run) | `run_frontend_verification.sh` lacks `npm run build` |
| 6. Framework connects frontend failure to backend change? | ❌ | No evidence correlation |
| 7. AI agent receives actionable diagnosis? | ❌ | `EvidenceAggregator` empty; recommendations generic |

**Root Cause Chain:** DTO invisible to capability registry → optimizer lacks `dto` kind → planner ignores blast radius → frontend verification not selected → build not run → type drift undetected.

---

## 10. Integration Gap Register (M9)

| GAP-ID | Severity | Subsystem | Current Behavior | Expected Behavior | Evidence | Existing Infra | Root Cause | Recommended Integration | Complexity | Risk |
|--------|----------|-----------|------------------|-------------------|----------|----------------|------------|------------------------|------------|------|
| GAP-001 | P0 | Changed file detection | `git diff HEAD` fails on clean CI checkout | Compare against merge base / base commit | `verify.py backend` exits 1 on clean tree | `orchestrator._collect_changed_files()` | Wrong git ref | Use `git diff origin/main...HEAD` or CI-provided changed files | Low | High |
| GAP-002 | P0 | Verification planning | Planner ignores `CrossLayerImpactPlanner` blast radius | Blast radius drives plan selection | Backend change → `run_frontend: True` ignored | Both planners exist | Orchestrator discards blast | Pass blast radius to `generate_plan()`; filter by impacted scopes | Low | High |
| GAP-003 | P0 | Capability registry | Stale module paths (`backend/src/loan_engine`) | Paths match real modules (`backend/src/engines/loan_engine`) | Registry capabilities never match files | `verification.yaml` capabilities | Paths not updated after restructure | Sync registry modules to provider engine paths | Low | High |
| GAP-004 | P0 | Optimizer kinds | `dto`, `mapper` (backend), `view_model`, `generated type` not recognized | All provider entity kinds drive verification | `loans_dto.py` → 0 verification units | `optimize_verification()` | Hardcoded kind list | Extend `impacted()` kinds to include all provider kinds | Low | High |
| GAP-005 | P1 | Evidence emission | No junit XML emitted by verification scripts | All test commands emit `--junitxml` | `EvidenceAggregator` finds no junit | `run_backend_verification.sh`, `pytest` addopts | Missing `--junitxml` flags | Add `--junitxml=path` to all pytest/npx commands | Low | Medium |
| GAP-006 | P1 | Frontend build | Not run in verification | `npm run build` in frontend verification | Type drift undetected at CI | `run_frontend_verification.sh`, profiles.py has build task | Script incomplete | Add `npm run build` to frontend verification script | Low | High |
| GAP-007 | P1 | Frontend type generation | Manual (`gen:types` needs live server) | Auto-generated on backend change | `api-generated.ts` committed, not regenerated | `frontend/package.json gen:types` | No pipeline | Add OpenAPI fetch + type gen to backend→frontend CI path | Medium | High |
| GAP-008 | P2 | Capability→test ownership | No automated mapping | Each capability knows its test files | Provider has engine→tests only | Architecture provider | Capability test ownership not modeled | Add `tests` to capability registry; link to provider | Medium | Medium |
| GAP-009 | P2 | Diagnosis | Generic "investigate failing task" | Specific: changed component + capability + test | `recommendations` = command strings | `orchestrator._generate_recommendations()` | No failure classification | Parse junit; map failed test → chain → capability → component | Medium | Medium |
| GAP-010 | P3 | Untracked file detection | Misses new/untracked files | Include `git status --porcelain` | New files invisible | `_collect_changed_files()` | Only tracks `git diff HEAD` | Also check untracked; exclude generated | Low | Low |

---

## 11. Minimal Integration Architecture (M10)

```
┌─────────────────────────────────────────────────────────────┐
│ CHANGE INTELLIGENCE                                         │
│  • git diff merge-base → changed files (incl. untracked)    │
│  • Provider ownership resolution (canonical)                │
└─────────────────────┬───────────────────────────────────────┘
                      │ changed_files + ownership
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ CAPABILITY GRAPH  (Provider-backed)                         │
│  • engine → service → router → endpoint                     │
│  • engine → capability → workspace/component/view_model     │
│  • dto → mapper → frontend mapper/type                      │
│  • All kinds registered in optimizer                        │
└─────────────────────┬───────────────────────────────────────┘
                      │ blast_radius (ImpactReport)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ IMPACT GRAPH                                               │
│  • CrossLayerImpactPlanner (canonical)                     │
│  • verification_plan per kind                              │
└─────────────────────┬───────────────────────────────────────┘
                      │ required verification kinds
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ VERIFICATION GRAPH                                         │
│  • VerificationPlanner consumes blast radius               │
│  • Registry capabilities updated to provider paths         │
│  • Optimizer selects minimal suites per kind               │
└─────────────────────┬───────────────────────────────────────┘
                      │ VerificationPlanIntel (selected + skipped)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ EXECUTION                                                  │
│  • Same commands local & CI                                │
│  • All pytest/npx emit --junitxml                          │
│  • Frontend build runs                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │ junit.xml + artifacts
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ EVIDENCE GRAPH                                             │
│  • EvidenceAggregator parses junit                         │
│  • Failed test → chain → capability → component            │
│  • Structured failure classification                       │
└─────────────────────┬───────────────────────────────────────┘
                      │ failure diagnosis
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ DIAGNOSIS                                                  │
│  • AI agent receives: changed file, capability, failed     │
│    test, chain, likely component, repair hints             │
└─────────────────────────────────────────────────────────────┘
```

**No new frameworks.** All components exist; connections are missing.

---

## 12. Implementation Roadmap (M11)

| # | Objective | Reused Components | Files Affected | Behavior Change | Validation | Benchmark | Rollback |
|---|-----------|-------------------|----------------|-----------------|------------|-----------|----------|
| 1 | Fix changed-file detection for CI | `orchestrator._collect_changed_files` | `orchestrator.py` | Use merge-base diff; include untracked | `verify.py backend` passes on clean CI | Clean CI checkout → verification runs | Revert file |
| 2 | Sync capability registry modules | `VerificationRegistry`, provider | `verification.yaml` capabilities | `loan-engine` → `backend/src/engines/loan_engine` | Registry capability matches engine files | Backend engine change → capability resolved | Revert yaml |
| 3 | Connect blast radius to planner | `VerificationPlanner`, `CrossLayerImpactPlanner` | `orchestrator.py`, `planner.py` | `generate_plan(blast_radius=...)` | Backend DTO change → frontend-unit selected | `affected` shows frontend-unit for DTO | Revert planner |
| 4 | Extend optimizer kinds | `optimize_verification` | `optimizer.py` | Add `dto`, `mapper`, `view_model`, `generated_type`, `runtime` | `loans_dto.py` → frontend-unit + contracts | DTO change → 4+ verification units | Revert optimizer |
| 5 | Emit junit from all test commands | `run_*.sh`, pytest addopts | `.github/scripts/*.sh`, `backend/pyproject.toml` | `--junitxml=runtime/generated/execution/...` | `EvidenceAggregator` produces test evidence | Failure → structured evidence | Remove flags |
| 6 | Add frontend build to verification | `run_frontend_verification.sh` | `.github/scripts/run_frontend_verification.sh` | Append `npm run build` | Backend DTO rename → TypeScript error caught | Type drift detected in CI | Remove build line |
| 7 | Auto-generate frontend types | New CI step | `.github/workflows/backend-verify.yml` (or new) | Fetch OpenAPI → `gen:types` → commit/push | `api-generated.ts` matches backend schema | Schema drift = build failure | Disable step |
| 8 | Structured diagnosis | `EvidenceAggregator`, `orchestrator._generate_recommendations` | `aggregator.py`, `orchestrator.py` | Failed test → chain → capability → component | AI agent gets targeted context | Diagnosis accuracy > 80% | Revert logic |

---

## 13. Cross-Layer Specimen (M7) — Full Detail

**Change:** `backend/src/core/dtos/loans_dto.py` (simulated; file exists)

**Detection:** ✅ `_collect_changed_files()` returns it

**Capability Resolution:** ❌ Registry `loan-engine` modules = `backend/src/loan_engine` (stale) → no match. Provider has no `dto` kind in capability mapping.

**Blast Radius (CrossLayerImpactPlanner):**
- Direct: `dto:backend/src/core/dtos/loans_dto.py`, `dto:backend/src/core/dtos/__init__.py`, `mapper:backend/src/core/mappers/loan_mapper.py`
- Indirect: capability `useLoansCapability` → workspace `loans` → components, pages
- `verification_plan`: `run_frontend: True`, `run_contract: True`

**Planner Output (VerificationPlanner):**
- Scope forced to `BACKEND` → `impacted_scopes: [contracts, quick, backend, property]`
- Capabilities: `[ledger, migrations, reconciliation, loan-engine, api-contracts, quick]`
- **Frontend capability NOT selected** (scope doesn't include frontend)
- Steps: `bash .github/scripts/run_backend_verification.sh`, `bash .github/scripts/run_fast_checks.sh`

**Optimizer Output (Intelligence):**
- Kinds recognized: `engine`, `endpoint`, `router`, `service`, `repository`, `capability`, `workspace`, `component`, `view_model`, `mapper`
- **`dto` NOT recognized** → `unit-targeted` skipped (no engine tests), `contracts-schemathesis` skipped (no endpoint), `backend-integration` skipped (no router/service), `frontend-unit` skipped (no frontend file)
- **Result: 0 verification units selected**

**Frontend Verification Script:** Runs `eslint`, `tsc`, `vitest` — **no `npm run build`**

**Outcome:** Backend DTO change → **zero verification** → frontend type drift undetected → production bug.

---

## 14. Audit Certification (M12)

| Intelligence | Question | Answer | Evidence |
|--------------|----------|--------|----------|
| Change | Can a code change be detected? | ⚠️ **PARTIAL** | Works locally; fails on clean CI checkout (GAP-001) |
| Capability | Can it be mapped to a capability? | ⚠️ **PARTIAL** | Engines/services/routers yes; DTOs/mappers/generated types no (GAP-003, GAP-004) |
| Impact | Can downstream effects be identified? | ✅ **YES** | `CrossLayerImpactPlanner` + provider complete for registered kinds |
| Verification | Can required verification be selected? | ❌ **NO** | Planner ignores blast radius (GAP-002); optimizer misses kinds (GAP-004) |
| Test | Can existing test sufficiency be measured? | ❌ **NO** | No capability→test ownership map (GAP-008) |
| Failure | Can a failure be connected to the affected capability? | ❌ **NO** | No junit emitted (GAP-005); no failure classification (GAP-009) |
| Diagnostic | Can an actionable next inspection be produced? | ❌ **NO** | Generic recommendations only (GAP-009) |
| Local/CI Parity | Can the same model operate locally and in CI? | ❌ **NO** | Changed-file detection diverges (GAP-001) |
| Heavy Verification | Can expensive verification be deferred without corrupting model? | ✅ **YES** | Optimizer skips mutation/golden by default with justification |
| Future Test Gen | Does architecture have structured info for safe test generation? | ⚠️ **PARTIAL** | Provider has engine→tests; capability→test ownership missing (GAP-008) |

**Certification Status:** **NOT CERTIFIED** — P0 gaps (001-004) prevent trustworthy automated diagnosis.

---

## Appendix: Evidence Sources

All conclusions above are grounded in repository inspection and empirical CLI execution:

- `runtime/verify.py` lines 53-665 (CLI entry, cache, profiles)
- `runtime/foundation/verification/orchestrator.py` lines 224-465 (orchestration)
- `runtime/foundation/verification/planner/planner.py` lines 65-731 (planner + CrossLayerImpactPlanner)
- `runtime/foundation/verification/verification.yaml` (workflows, scripts, capabilities)
- `runtime/foundation/verification/profiles.py` (profiles — not executed)
- `runtime/foundation/intelligence/platform/optimizer.py` (intelligence optimizer)
- `runtime/foundation/architecture/chains.py` (canonical chain map)
- `runtime/foundation/architecture/provider.py` (canonical provider)
- `.github/scripts/run_backend_verification.sh`, `run_frontend_verification.sh`
- `.github/workflows/backend-verify.yml`, `frontend-verify.yml`
- Empirical runs: `python runtime/verify.py affected/diagnose/risk/intelligence` on `backend/src/engines/loan_engine/emi.py` and `backend/src/core/dtos/loans_dto.py`

---

*End of VEA-1 Audit Report*