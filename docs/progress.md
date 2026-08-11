# Verification Ecosystem Integration Audit — Execution Progress

**Phase:** VEA-1 complete → VEA-2 Phase 1 complete → VEA-2 Phase 1.5 complete → **VEA-2 Phase 2 in progress**
**Execution mode:** Autonomous, milestone-driven
**Current status:** VEA-2 PHASE 2 — Evidence Integrity (identity spine: unit → execution → evidence → provenance)

---

## VEA-1 Summary (Complete)

VEA-1 audit certified the verification ecosystem. See `docs/verification/VEA1_AUDIT_REPORT.md`.

**Finding:** The repository has substantial verification intelligence, but information is lost
at the boundaries between components. The system understands change→impact but fails to
propagate that understanding through verification planning and execution.

**Authority:** `runtime.foundation.architecture` provider is canonical for capabilities/chains.
`verification.yaml` registry has stale module paths. `profiles.py` tasks are audit-only
(never executed). `CrossLayerImpactPlanner` correctly computes blast radius but orchestrator
discards it before planning.

---

## VEA-2 Phase 1 — Integration Backbone Repair (COMPLETE)

See `docs/verification/VEA2_PHASE1_CERTIFICATION.md`. C1–C12 PASS at code level.
Full Phase 1 detail is retained in `docs/verification/VEA2_PHASE1_CERTIFICATION.md`.

---

# VEA-2 Phase 1.5 — Real-World Cross-Layer Failure Forensic Diagnosis

## Milestone Status

| Milestone | Status |
|-----------|--------|
| M1 Establish immutable baseline | DONE |
| M2 Capture raw frontend failure | DONE |
| M3 Failure clustering | DONE |
| M4 Trace backend/frontend causality | DONE |
| M5 Predicted vs actual blast radius | DONE |
| M6 Verify verification selection | DONE |
| M7 Failure classification | DONE |
| M8 Root-cause compression | DONE |
| M9 Framework gap vs application defect | DONE |
| M10 Diagnose evidence infrastructure | DONE |
| M11 Minimal evidence-correlation improvements | DONE |
| M12 Re-run the same real failure | DONE |
| M13 Controlled application remediation | DONE |
| M14 Prevent the error loop | DONE |
| M15 Regression tests | DONE |

---

## M1 — Establish Immutable Baseline

**Status:** DONE
**Started:** 2026-08-11
**Completed:** 2026-08-11

### Repository state

```
HEAD:    b9074020aef5a3e4c8313cc313a80a10fd623bbb
Subject: fix(loan-engine): make amortization schedules exact and self-consistent
Branch:  recovery/program-r-forensic-reconstruction
Working tree:
   D docs/verification/progress.md   (moved back to docs/progress.md per execution contract)
  ?? docs/progress.md
```

No application source was modified during baseline collection.

### Environment

```
OS      linux
Python  3.12.3
pytest  9.0.2
Node    v20.20.2
npm     10.8.2
frontend/node_modules  PRESENT (installed 2026-08-10)
```

Note: VEA-2 Phase 1 recorded "frontend dev environment not available locally". That
limitation **no longer holds** — frontend verification is now locally executable. This
is why the frontend failure is observable for the first time.

### Commands executed

```bash
git rev-parse HEAD
git status --porcelain=v1
git log --oneline -15
git diff --name-status HEAD~1 HEAD
bash .github/scripts/run_backend_verification.sh
python3 -m pytest runtime/tests -q --no-header
```

### Baseline verification status

| Layer | Command | Exit | Result |
|-------|---------|------|--------|
| Backend | `.github/scripts/run_backend_verification.sh` | 0 | **GREEN** — 26 contract + 206 property + 468 unit/invariant passed (77s) |
| Runtime (framework) | `pytest runtime/tests` | 0 | **GREEN** — 281 passed (30.6s) |
| Frontend | `.github/scripts/run_frontend_verification.sh` | 1 | **RED** — reproducible |

### Evidence

`runtime/generated/evidence/vea2-phase1_5/` (gitignored raw capture):
- `frontend_typecheck.txt`
- `frontend_eslint.txt`
- `frontend_vitest.txt`
- `frontend_build.txt`

### Acceptance

- [x] Current frontend failure is reproducible locally
- [x] Backend status explicitly recorded (GREEN)
- [x] Repository state captured
- [x] No source changes introduced during baseline collection

---

## M2 — Capture Raw Frontend Failure

**Status:** DONE
**Started:** 2026-08-11
**Completed:** 2026-08-11

### Commands executed

```bash
cd frontend && npx tsc --noEmit                  # exit 0   (22.1s)
cd frontend && npx eslint . --ext .ts,.tsx --quiet  # exit 1 (79.8s)
cd frontend && npx vitest run                    # exit 1  (198.8s)
cd frontend && npx next build                    # exit 1   (40.1s)
```

Working directory: `/home/vasantha/AI-Projects/ClariFin_OS/frontend`

### Phase-separated raw failure record

| Phase | Exit | Duration | Signal |
|-------|------|----------|--------|
| **typecheck** (`tsc --noEmit`) | **0** | 22.1s | **PASS — zero TypeScript errors** |
| **lint** (`eslint`) | 1 | 79.8s | 44 errors |
| **test** (`vitest run`) | 1 | 198.8s | 1 failed / 1236 passed (1237 total, 92 files) |
| **build** (`next build`) | 1 | 40.1s | Turbopack build failed with 10 errors |
| **environment** | n/a | n/a | No environment failure; node_modules present, all tools resolve |

### Headline finding (contradicts the premise under investigation)

The execution document framed the specimen as *"previous AI-agent behavior: repeated
TypeScript/build fixes → error cascades / fix loops."*

**There are zero TypeScript errors.** `tsc --noEmit` exits 0.

The frontend failure is real and reproducible, but it is **not** a TypeScript failure.
Any prior agent loop spent fixing "TypeScript errors" was chasing a signal that the
typechecker does not emit. This is itself a primary forensic finding.

### Raw failure signatures

**lint (44 errors)**
- `lib/runtime/use-workspace-registration.ts:52:10` — `react-hooks/refs`:
  "Cannot access refs during render" (`return config.current;`)
- `public/pdf.worker.mjs` — 43 errors across a **vendored third-party bundle**
  (`@next/next/no-assign-module-variable` ×2, `@typescript-eslint/no-this-alias` ×7,
  plus additional findings in the same file)

**test (1 failure)**
- `components/toolbar/__tests__/workspace-toolbar-performance.test.tsx:28`
  `WorkspaceToolbar Performance > renders under 150ms`
  `AssertionError: expected 288.5322960000012 to be less than 250`
  (wall-clock performance assertion, machine-load sensitive)

**build (10 errors, 1 root pattern)**
- Turbopack: React hooks imported into modules reachable from a Server Component
  without a `"use client"` directive. Affected modules:
  - `lib/runtime/navigation-runtime.ts:106`
  - `lib/runtime/selection-runtime.ts:93`
  - `lib/runtime/timeline-runtime.ts:101`
  - `lib/runtime/workspace-runtime.ts:96`
  - `lib/runtime/use-workspace-registration.ts:6`
  Each reported twice (import-specifier + import-statement position) = 10 diagnostics.
  Import trace root: `lib/runtime/index.ts` → `app/layout.tsx` (Server Component).

### Acceptance

- [x] Reproducible raw failure record exists
- [x] Record distinguishes typecheck / build / test / lint / environment
- [x] No remediation attempted
- [x] Used existing verification script (`run_frontend_verification.sh`) — no parallel
      evidence framework created; per-phase decomposition run manually because the
      existing script collapses all phases into a single exit code (recorded as a
      framework observation for M10)

---

## M3 — Failure Clustering

**Status:** DONE
**Started:** 2026-08-11
**Completed:** 2026-08-11

### Method

Clustered by (phase, file, diagnostic code, import trace, change history). Pre-existence was
then **empirically proven**, not inferred, by building/linting/testing the frontend in an
isolated git worktree pinned to `bacc1fe2` — the last commit that touched `frontend/`, and
5 commits *before* the backend change at HEAD.

```bash
git worktree add /tmp/kilo/vea15-baseline bacc1fe2 --detach
cp -r frontend/node_modules /tmp/kilo/vea15-baseline/frontend/node_modules
cd /tmp/kilo/vea15-baseline/frontend
npx next build          # exit 1 — Turbopack build failed with 10 errors
npx eslint . --quiet    # exit 1 — 44 problems (44 errors)
npx tsc --noEmit        # exit 0
npx vitest run components/toolbar/__tests__/workspace-toolbar-performance.test.tsx  # exit 0
```

Note: a symlinked `node_modules` produced a misleading `TurbopackInternalError:
Symlink ... points out of the filesystem root`. A real copy was used instead. Recorded so
the experiment is reproducible and the spurious error is not mistaken for a finding.

### Clusters

| # | Cluster | Phase | Count | Class | Pre-existence proof |
|---|---------|-------|-------|-------|---------------------|
| **C-A** | Missing `"use client"` on React-hook modules under `lib/runtime/` reachable from `app/layout.tsx` | build | 10 diagnostics / **5 modules / 1 root cause** | `ROOT_CLUSTER` | **Identical 10 errors, same files, same line:col at `bacc1fe2`** |
| **C-B** | `react-hooks/refs` — ref read during render in `lib/runtime/use-workspace-registration.ts:52` | lint | 1 | `ROOT_CLUSTER` | Present at `bacc1fe2` |
| **C-C** | Vendored third-party bundle `public/pdf.worker.mjs` linted as first-party source | lint | 43 | `ROOT_CLUSTER` (single config root cause) | Present at `bacc1fe2` |
| **C-D** | `workspace-toolbar-performance.test.tsx` wall-clock assertion `288.5ms < 250ms` | test | 1 | `ENVIRONMENT_FAILURE` (load-sensitive/flaky) | Passes in isolation at `bacc1fe2` **and** at HEAD (3/3 runs) |
| — | typecheck | typecheck | **0** | n/a | `tsc --noEmit` exit 0 at both commits |

`UNCLASSIFIED`: **0**.

### Cluster compression

```
55 raw diagnostics (10 build + 44 lint + 1 test)
        ↓
4 clusters
        ↓
3 real root causes + 1 flaky test
        ↓
0 caused by the backend change
```

`C-A` is one root cause, not 10: each of the 5 modules is reported twice (import-specifier
and import-statement column), and all 5 share the single barrel entry `lib/runtime/index.ts`
imported by the Server Component `app/layout.tsx`.

`C-C` is one root cause, not 43: `eslint.config.mjs` does not ignore `public/`, so a
vendored pdf.js worker bundle is linted as project source.

### Acceptance

- [x] Every error belongs to a controlled cluster class
- [x] Zero `UNCLASSIFIED`
- [x] Pre-existence proven empirically, not asserted

---

## M4 — Trace Backend/Frontend Causality

**Status:** DONE

### Change under test

```
HEAD b9074020  fix(loan-engine): make amortization schedules exact and self-consistent
  backend/src/engines/loan_engine/amortization.py
  backend/src/engines/loan_engine/floating_rate.py
  backend/tests/properties/forecasting/test_engine_properties.py
  .github/actions/upload-runtime/action.yml
  .github/workflows/golden.yml
```

Capability owner (provider-resolved): `engine:loan_engine` → `capability:useLoansCapability`
(`frontend/lib/capabilities/use-loans-capability.ts`).

### Dependency-chain trace per cluster

For each failing cluster, the chain was walked **frontend → backend**:

| Cluster | Frontend symbol | Depends on | Reaches backend? |
|---------|-----------------|------------|------------------|
| C-A | `useState/useEffect` from `react` in `lib/runtime/*-runtime.ts` | React + Next.js RSC boundary | **No.** Imports are `./runtime-types`, `../event-bus`, `react`. No API/DTO/mapper/generated-type edge. |
| C-B | `config.current` (a `useRef`) | React ref semantics | **No** |
| C-C | `public/pdf.worker.mjs` | pdf.js vendor bundle | **No** |
| C-D | `WorkspaceToolbar` render wall-clock | host CPU/load | **No** |

Independent corroboration:

```bash
git diff bacc1fe2 HEAD --name-only | grep '^frontend/'   # → 0 files
git diff bacc1fe2 HEAD --name-only | grep -E 'dto|mapper|router|schema|openapi'  # → none
```

Every failing frontend file is **byte-identical** to `bacc1fe2` (verified per-file with
`git diff --quiet`), including `lib/runtime/index.ts` and `app/layout.tsx`.

### Conclusion

**No causal chain exists between the backend change and any frontend failure cluster.**
No DTO, router, mapper, OpenAPI schema, or generated type changed. The backend delta is
confined to loan-engine arithmetic internals, and backend verification is GREEN.

---

## M5 — Predicted vs Actual Blast Radius

**Status:** DONE

### Framework prediction (real pipeline, not simulated)

```bash
VERIFICATION_BASE_REF=HEAD~1 python3 runtime/verify.py affected
```

Direct impact: 14 entities (`engine:loan_engine`, 2 engine modules, 11 backend tests).
Indirect impact: 55 entities, of which **7 are frontend**:

| Predicted frontend entity | graph | via | relation |
|---|---|---|---|
| `capability:useLoansCapability` | ownership | `engine:loan_engine` | owns |
| `mapper:frontend/lib/mappers/loans-mapper.ts` | chain-map | `router:backend/src/routers/loans.py` | consumed-by |
| `view_model:AmortizationEntryViewModel` | chain-map | `router:backend/src/routers/loans.py` | view-model |
| `mapper:frontend/lib/mappers/credit-cards-mapper.ts` | chain-map | `router:backend/src/routers/credit_cards.py` | consumed-by |
| `view_model:StatementHistoryViewModel` | chain-map | `router:backend/src/routers/credit_cards.py` | view-model |
| `capability:useCreditCardsCapability` | ownership | `engine:credit_card_engine` | owns |
| `capability:useBehaviourCapability` | execution | `endpoint:GET /report` | executes |

### Actual failing frontend files

```
lib/runtime/navigation-runtime.ts
lib/runtime/selection-runtime.ts
lib/runtime/timeline-runtime.ts
lib/runtime/workspace-runtime.ts
lib/runtime/use-workspace-registration.ts
public/pdf.worker.mjs
components/toolbar/__tests__/workspace-toolbar-performance.test.tsx
```

### Intersection

**Empty. Zero overlap** between the 7 predicted entities and the 7 actually-failing files.

### Classification per cluster

| Cluster | Classification | Justification |
|---------|----------------|---------------|
| C-A | **UNRELATED** | No dependency on the changed backend capability; pre-existing at `bacc1fe2` |
| C-B | **UNRELATED** | Same |
| C-C | **UNRELATED** | Same |
| C-D | **UNRELATED** | Same |

**No cluster is causally related to the change**, therefore no cluster requires a
PREDICTED-CORRECT / UNDER-PREDICTED assessment.

The framework was **not** under-predicting. It correctly predicted the *contract* surface
that loan-engine changes can reach (loans mapper / `AmortizationEntryViewModel` /
`useLoansCapability`). Those predicted surfaces are **green**. The frontend is red for
entirely separate, pre-existing reasons.

### Over-prediction assessment (restraint)

`capability:useCreditCardsCapability`, `mapper:credit-cards-mapper.ts` and
`view_model:StatementHistoryViewModel` entered the radius through a shared
`endpoint:GET /report` / `credit_card_engine` hop. This is a **mild OVER-PREDICTION**: a
loan amortization change reaching credit-card view models is a wide hop. It is recorded as
an observation, **not remediated in this phase** — it causes extra verification (safe
direction), not a missed failure, and Section 21 requires correctness before optimization.

---

## M6 — Verify Verification Selection

**Status:** DONE

### Selected units with full provenance

| Unit | source | impact_kinds | Reason | Correct? |
|------|--------|--------------|--------|----------|
| `unit-targeted` | `ownership` | `engine` | 17 provider-recorded test files verify an impacted engine | Yes |
| `contracts-schemathesis` | `chain-map+blast-radius` | `endpoint, dto` | 35 endpoints in blast radius | Yes |
| `backend-integration` | `chain-map+blast-radius` | `router, service, repository` | 11 entities impacted | Yes |
| `backend-unit` | `chain-map+blast-radius` | `engine, engine_module, mapper, router, service` | 27 backend entities impacted | Yes |
| `frontend-unit` | `chain-map+blast-radius` | `capability, workspace, component, view_model, mapper` | 7 frontend entities impacted | Yes — justified by predicted contract surface |
| `frontend-typecheck-build` | `chain-map+blast-radius` | `capability, workspace, component, view_model, mapper` | frontend entity/contract/capability impacted — type compatibility must be verified | Yes |

### Skipped units with justification

| Unit | Reason |
|------|--------|
| `playwright-e2e` | no workspace impacted |
| `runtime-self-test` | runtime unchanged |
| `mutation-run` | requires explicit request (cost >= 600s) |
| `golden-regression` | requires explicit request (cost >= 600s) |

### Findings

- **No unexplained unit.** All 6 selected units carry `source`, `impact_kinds` and
  `capabilities`. C11 provenance holds on the real specimen, not just synthetic tests.
- **No silently omitted causally-necessary unit.** Frontend verification *was* selected,
  which is why the pre-existing frontend breakage became visible at all.
- **No "run everything" escalation.** 6 of 10 units selected; 4 skipped with stated reasons.
- Selecting frontend verification for a loan-engine change is **correct behaviour**: the
  chain map shows loan router → loans mapper → `AmortizationEntryViewModel`, a genuine
  contract surface.

### Critical framework observation (feeds M9/M10)

The selected unit `frontend-typecheck-build` runs
`cd frontend && npx tsc --noEmit && npm run build`, and `frontend-unit` runs
`npm --prefix frontend run test`. Both **fail** — but they fail on defects that are
**outside** the blast radius that justified selecting them.

The framework selected the right units for the right reasons, then reported a **red**
result whose content is unrelated to its own prediction. Nothing in the current pipeline
detects or states that mismatch. **That gap — not the frontend code — is the real
verification-architecture defect this specimen exposes.** See M9/M11.

---

## M7 — Failure Classification

**Status:** DONE

Controlled taxonomy from §11. Every classification is evidence-backed.

| Cluster | Classification | Evidence |
|---------|----------------|----------|
| **C-A** (5 modules, 10 build diagnostics) | `FRONTEND_IMPLEMENTATION` + `PRE_EXISTING` | Turbopack: "You're importing a component that needs `useState`/`useEffect`. This React Hook only works in a Client Component." Import trace `lib/runtime/index.ts → app/layout.tsx`. Identical at `bacc1fe2`. |
| **C-B** (1 lint) | `FRONTEND_IMPLEMENTATION` + `PRE_EXISTING` | `react-hooks/refs` at `use-workspace-registration.ts:52:10`, `return config.current;`. Present at `bacc1fe2`. |
| **C-C** (43 lint) | `FRONTEND_TOOLCHAIN` + `PRE_EXISTING` | All 43 in `public/pdf.worker.mjs`, a vendored pdf.js bundle; `eslint.config.mjs` does not ignore `public/`. Present at `bacc1fe2`. |
| **C-D** (1 test) | `ENVIRONMENT` | `expected 288.53 to be less than 250`; passes in isolation at `bacc1fe2` and 3/3 at HEAD. Wall-clock assertion under 92-file parallel suite load. |
| **Cross-cutting** | `VERIFICATION_FRAMEWORK` | Framework cannot express "selected unit failed for reasons outside its blast radius" (M6 observation). |

Explicitly **not** applicable, each disproven by evidence:
`BACKEND_FRONTEND_CONTRACT_DRIFT`, `BACKEND_FRONTEND_TYPE_DRIFT`, `DTO_GENERATED_TYPE_DRIFT`,
`MAPPER_DRIFT`, `VIEW_MODEL_DRIFT`, `API_ROUTER_CONTRACT_DRIFT`, `STALE_GENERATED_ARTIFACT`
— no DTO/mapper/router/schema changed, and `tsc --noEmit` exits 0 (any drift in these
categories would surface as a type error).

No new taxonomy categories were required.

---

## M8 — Root-Cause Compression

**Status:** DONE

### C-A — Missing `"use client"` boundary (PRIMARY)

```
Root cause          5 modules in frontend/lib/runtime/ import React hooks but lack "use client";
                    they are re-exported by lib/runtime/index.ts, which app/layout.tsx
                    (a Server Component) imports.
Affected capability none (frontend shell runtime; no backend capability)
Affected files      lib/runtime/navigation-runtime.ts:106
                    lib/runtime/selection-runtime.ts:93
                    lib/runtime/timeline-runtime.ts:101
                    lib/runtime/workspace-runtime.ts:96
                    lib/runtime/use-workspace-registration.ts:6
Dependency chain    lib/runtime/*-runtime.ts → lib/runtime/index.ts → app/layout.tsx (RSC)
PRIMARY diagnostic  "This React Hook only works in a Client Component"
SECONDARY           5 duplicate column-position diagnostics (10 total, not 10 defects)
Verification unit   frontend-typecheck-build
Evidence            runtime/generated/evidence/vea2-phase1_5/frontend_build.txt
Classification      FRONTEND_IMPLEMENTATION + PRE_EXISTING
Confidence          HIGH (byte-identical reproduction at bacc1fe2)
Inspection order    1. lib/runtime/index.ts (barrel — the aggregation point)
                    2. the 5 hook-bearing runtime modules
                    3. app/layout.tsx (the RSC consumer)
```

### C-B — Ref read during render (PRIMARY)

```
Root cause          use-workspace-registration.ts returns config.current during render
Affected files      lib/runtime/use-workspace-registration.ts:52
PRIMARY diagnostic  react-hooks/refs — "Cannot access ref value during render"
SECONDARY           none
Classification      FRONTEND_IMPLEMENTATION + PRE_EXISTING
Confidence          HIGH
```

### C-C — Vendored bundle linted as source (PRIMARY, config-level)

```
Root cause          eslint.config.mjs does not ignore public/; public/pdf.worker.mjs
                    (third-party pdf.js build output) is linted as first-party source
Affected files      frontend/eslint.config.mjs  (the actual defect)
                    frontend/public/pdf.worker.mjs  (the victim — DO NOT EDIT)
PRIMARY diagnostic  1 configuration defect
SECONDARY           43 lint diagnostics, all cascade
Classification      FRONTEND_TOOLCHAIN + PRE_EXISTING
Confidence          HIGH
```

### C-D — Load-sensitive performance assertion

```
Root cause          wall-clock assertion under parallel-suite CPU contention
Affected files      components/toolbar/__tests__/workspace-toolbar-performance.test.tsx:28
Classification      ENVIRONMENT
Confidence          HIGH (isolated: pass at bacc1fe2 and 3/3 at HEAD; full suite: fail)
```

### Compression result

**55 raw diagnostics → 3 actionable root causes + 1 flaky test.**
An agent treating these as 55 independent repair tasks — the exact loop this phase exists
to prevent — would be doing ~52 units of unnecessary and risky work.

---

## M9 — Framework Gap vs Application Defect

**Status:** DONE

### Application defects (pre-existing, unrelated to the backend change)

| ID | Defect | Class |
|----|--------|-------|
| APP-1 | 5 `lib/runtime/` modules missing `"use client"` — **production build is broken** | `FRONTEND_IMPLEMENTATION` |
| APP-2 | Ref read during render in `use-workspace-registration.ts:52` | `FRONTEND_IMPLEMENTATION` |
| APP-3 | `eslint.config.mjs` lints vendored `public/` output | `FRONTEND_TOOLCHAIN` |
| APP-4 | Load-sensitive wall-clock perf assertion | `ENVIRONMENT` (test-quality) |

### Verification-framework defects

| ID | Gap | Evidence |
|----|-----|----------|
| **FW-1** | **No blast-radius/failure correlation.** The framework cannot state whether a failure inside a selected unit lies inside or outside the blast radius that justified selecting that unit. Every finding in M4/M5 was derived by hand. | M5: zero overlap between 7 predicted entities and 7 failing files, undetected by the pipeline |
| **FW-2** | **No phase decomposition in frontend verification.** `run_frontend_verification.sh` collapses eslint + tsc + vitest into a single exit code. The M2 headline finding (**zero TypeScript errors**) is invisible to the framework and had to be recovered manually. This is precisely what misled prior agents into a "TypeScript fix loop". | M2: `tsc --noEmit` exit 0, yet script exits 1 |
| **FW-3** | **No `npm run build` in frontend verification.** The optimizer's `frontend-typecheck-build` unit includes `npm run build`, but the executed script `run_frontend_verification.sh` does not. The 10 build errors — the most severe defect present — are invisible to the actual verification path. Previously logged as GAP-006. | Optimizer command vs script contents diverge |
| **FW-4** | **No pre-existing-failure baseline.** The framework cannot distinguish "this change broke it" from "it was already broken", the single most important question for an agent. | Required a manual `git worktree` experiment to answer |

**This is the central result of Phase 1.5: the framework worked correctly at
change→capability→impact→selection, and is blind at failure→attribution.**

---


## M10 — Diagnose Evidence Infrastructure

**Status:** DONE

### Chain evaluated

```
execution result → verification unit → test result → failure evidence → capability → change
```

### Findings

| # | Finding | Evidence |
|---|---------|----------|
| **E-1** | **VEA-1 JUnit finding CONFIRMED.** `EvidenceAggregator._collect_test_results()` looks for `junit.xml` / `test-results.xml` / `pytest-results.xml`. **No verification script emits `--junitxml`.** Only `run_mutation_selective.sh:54` emits JUnit (for mutmut). | `grep -rn junitxml .github/scripts/` → 1 hit, mutation only |
| **E-2** | **`EvidenceSummary` is backend-only.** Fields are `backend.{unit_tests, property_tests, contract_tests, coverage, mutation}`. There is **no frontend field at all** — no typecheck, build, lint or vitest slot. The frontend failure in this specimen is structurally unrepresentable in the evidence model. | `aggregator.py` — sole "frontend" occurrence is a synthesized `suggested_layer` string |
| **E-3** | **No unit↔failure linkage.** Evidence is aggregated by *artifact type*, never keyed by `VerificationUnit.id`. The C11 provenance added in Phase 1 lives on the plan and is **discarded before evidence aggregation**, so a failure can never be traced back to the impact that selected it. | `EvidenceSummary` has no unit identity field |
| **E-4** | **Attribution is keyword-guessing, not graph traversal.** `_find_chain_for_failure()` returns the **first** entry of the chain map irrespective of which test failed, and `_find_dependency_chain()` matches by substring. On this specimen it would attribute an unrelated frontend build failure to an arbitrary engine. | `aggregator.py:474` — `for engine_file, chain in cross_map.items(): ... return` on first iteration |
| **E-5** | **Phase collapse.** `run_frontend_verification.sh` runs eslint, tsc and vitest under one `fail` flag and a single exit code. Machine-readable per-phase status does not exist. | Script lines 11–20 |

### Decision (per §14: do not introduce a new evidence system)

The existing evidence system is **not** the right insertion point for this specimen's core
gap. It is a CI-artifact aggregator (JUnit/coverage/mutation XML+JSON), whereas the missing
capability — *"is this failure inside the blast radius that justified running this unit?"* —
requires the **plan-side** objects (`BlastRadius`, `VerificationUnit.provenance`) that the
intelligence platform already holds in memory.

Adding frontend/JUnit plumbing to `EvidenceAggregator` (GAP-005/GAP-006) is real work but
would **not** have answered any question in M3–M9. It is therefore left to Phase 2 and
**not** speculatively implemented here.

The smallest correct change is a **failure-attribution** step in the intelligence platform
that correlates observed failing files against the already-computed blast radius. See M11.

---

## M11 — Minimal Evidence-Correlation Improvements

**Status:** DONE

Two changes. Each is justified by an observed failure from M2–M9; nothing speculative was
built. GAP-005 (JUnit) and the `EvidenceAggregator` frontend model were deliberately **not**
implemented — see the M10 decision.

### Change 1 — `runtime/foundation/intelligence/platform/attribution.py` (new, 290 lines)

| Question | Answer |
|----------|--------|
| What observed failure required this? | FW-1. The pipeline reported "frontend verification failed" for a change with **zero** overlap between its 7 predicted entities and the 7 actually-failing files. Every conclusion in M4/M5 had to be derived by hand. |
| What existing component is improved? | The intelligence platform. It consumes the already-computed `BlastRadius` and `VerificationUnit.provenance` (Phase 1 C11); it does **not** re-derive dependency analysis. |
| Why is this the smallest correct change? | It is a pure, additive, deterministic function — no I/O, no clock, no subprocess. No planner, optimizer, blast-radius or orchestrator behaviour is altered, so Phase 1 C1–C12 are untouched. |
| How is it tested? | `runtime/tests/test_failure_attribution.py`, 10 tests, mutation-verified. |

Verdicts: `IN_BLAST_RADIUS`, `OUTSIDE_BLAST_RADIUS`, `PRE_EXISTING`, `ATTRIBUTION_UNKNOWN`.
`ATTRIBUTION_UNKNOWN` is a first-class outcome — the module never guesses (addresses E-4,
where the old `_find_chain_for_failure()` returned the *first* chain-map entry regardless of
which test failed).

`AttributionReport.change_is_implicated` is the single boolean that answers "is my change
guilty?", plus `clusters()` for cascade compression (addresses FW-4/E-3).

### Change 2 — `.github/scripts/run_frontend_verification.sh` (phase decomposition)

| Question | Answer |
|----------|--------|
| What observed failure required this? | FW-2/FW-3. The script collapsed eslint+tsc+vitest into one exit code, so a run could exit 1 with **zero TypeScript errors** — the exact signal that drove prior agents into a TypeScript fix loop. It also omitted `npm run build`, hiding the most severe defect (10 build errors). |
| What existing component is improved? | The existing script. No new framework. |
| Why is this the smallest correct change? | The exit-code contract is unchanged (0 all-pass / 1 any-fail), so `run_full_verification.sh` and `registry.py` consumers are unaffected. It adds `build` (closing GAP-006) and emits per-phase JSON. |
| How is it tested? | Executed on the real specimen; output below. |

### Change 3 — formatter (`cli_format.py`)

`format_cross_layer_failure()` renders the §18 diagnostic, following the repository's
existing formatter architecture rather than inventing a reporting system.

### Not implemented (deliberate)

`--junitxml` on all test commands (GAP-005) and a frontend section in `EvidenceSummary`
(E-2) are real gaps but answered **no** question in this diagnosis. Deferred to Phase 2 per
§15 ("Do not implement speculative features").

---

## M12 — Re-run the Same Real Failure

**Status:** DONE

Same repository state, same real failure, same pipeline — re-evaluated, not replaced by a
synthetic case.

### Frontend verification, now phase-decomposed

```
overall: fail
  lint       fail  exit=1 49s
  typecheck  pass  exit=0 22s      ← previously invisible
  build      fail  exit=1 19s      ← previously not run at all
  test       pass  exit=0 103s     ← confirms C-D was load-flaky
```

`runtime/generated/evidence/frontend/frontend-verification.json` (`frontend-verification/v1`).

Two facts the framework could not previously express are now machine-readable:
**TypeScript is clean**, and **the production build is broken**.

### Cross-layer diagnosis on the real specimen

```
CROSS-LAYER FAILURE

Change:      backend/src/engines/loan_engine/amortization.py
             backend/src/engines/loan_engine/floating_rate.py  (+ CI/docs/runtime files)

Capability:  capability:useLoansCapability
             capability:useCreditCardsCapability
             capability:useBehaviourCapability

Impact:      34 predicted downstream files, incl.
             frontend/lib/mappers/loans-mapper.ts
             frontend/types/loans-view-model.ts
             frontend/lib/capabilities/use-loans-capability.ts

Verification: unit-targeted, contracts-schemathesis, backend-integration,
              backend-unit, frontend-unit, frontend-typecheck-build
              (each with source= and kinds= provenance)

Failure attribution:
  observed=59  in-blast-radius=0  outside=59  unknown=0

NO FAILURE IS ATTRIBUTABLE TO THIS CHANGE.
  Every observed failure lies outside the blast radius that justified running these units.
  Do NOT modify the changed files to make this verification green.
```

**The conclusion that took ~15 manual forensic steps in M3–M9 is now produced automatically
by the pipeline.**

### Regression check

```
python3 -m pytest runtime/tests -q   → 291 passed  (281 baseline + 10 new), 0 failed
ruff check <changed files>           → All checks passed
bash .github/scripts/run_backend_verification.sh → exit 0 (unchanged)
```

No existing test was modified, skipped, or weakened.

---

## M14 — Prevent the Error Loop

**Status:** DONE

The §18 diagnostic is produced by `format_cross_layer_failure()` and shown under M12.

The loop-prevention properties, each covered by a regression test:

| Property | Test |
|----------|------|
| States explicitly when no failure is attributable to the change | `test_diagnostic_output_names_excluded_areas` |
| Emits "Do NOT modify the changed files to make this verification green" | same |
| Lists excluded/unrelated areas by phase and file | same |
| Still implicates the change when a failure *is* in the radius | `test_failure_inside_blast_radius_implicates_the_change` |
| Compresses cascades into clusters | `test_clusters_compress_cascades` |
| Never guesses | `test_unresolvable_failure_is_unknown_never_silently_unrelated` |

Counterfactual: had this existed before, the prior agent would have read
`in-blast-radius=0` and `typecheck pass` and stopped, instead of entering a TypeScript
repair loop against a compiler that was already clean.

---

## M15 — Regression Tests for the Discovery

**Status:** DONE

`runtime/tests/test_failure_attribution.py` — 10 tests, all protecting architectural
invariants rather than implementation details.

Framework defect → regression test mapping:

| Defect | Test |
|--------|------|
| FW-1 (no failure/blast-radius correlation) | `test_real_frontend_failures_are_attributed_outside_blast_radius` |
| FW-1 inverse (must not over-correct into never blaming the change) | `test_failure_inside_blast_radius_implicates_the_change` |
| FW-4 / E-3 (provenance lost before evidence) | `test_attribution_carries_unit_provenance` |
| FW-4 (pre-existing vs unrelated) | `test_pre_existing_failure_is_distinguished_from_merely_unrelated` |
| E-4 (attribution by guessing) | `test_unresolvable_failure_is_unknown_never_silently_unrelated` |
| Cascade clustering | `test_clusters_compress_cascades` |
| Determinism | `test_attribution_is_deterministic` |
| Path-form false negatives | `test_path_normalisation_does_not_create_false_negatives` |
| Phase-1 selection must not regress | `test_loan_engine_change_still_selects_frontend_verification` |
| Loop prevention | `test_diagnostic_output_names_excluded_areas` |

### Test strength verified by mutation

The tests were confirmed load-bearing, not tautological. Injecting a mutant that makes
attribution always claim `IN_BLAST_RADIUS`:

```
matched = _match(failure.path, radius) or 'MUTANT'
→ 4 failed, 6 passed   (mutant killed)
```

The mutant was reverted and the suite restored to 10/10 passing.

---

## M13 — Controlled Application Remediation

**Status:** DONE

Remediation began **only after** M3–M9 classification. Each fix traces to a diagnosed root
cause. No broad refactoring; no unrelated TypeScript repair (there were no TypeScript errors
to repair).

### Fix 1 — APP-1 / cluster C-A: missing `"use client"` (5 files)

```
Diagnosis    → C-A, FRONTEND_IMPLEMENTATION + PRE_EXISTING
Files        → lib/runtime/{navigation,selection,timeline,workspace}-runtime.ts
                lib/runtime/use-workspace-registration.ts
Symbol       → React hooks (useState/useEffect/useRef) in RSC-reachable modules
Correction   → prepend `'use client';` — exactly the 5 diagnosed modules, nothing else
Result       → all 10 Turbopack errors cleared; "✓ Compiled successfully"
```

### Fix 2 — module-level `window` access during prerender (2 files)

**Discovered during remediation, not present in the original inventory.** The compile error
in C-A masked it; it only became observable once compilation succeeded. Diagnosed with the
same discipline (chunk-offset → source symbol) rather than guessed.

```
Diagnosis    → ReferenceError: window is not defined, at module evaluation
Located by   → reading the emitted chunk at the exact byte offset in the stack trace,
                then grepping the unique event name back to source
Files        → lib/intelligence/intelligence-invocation.ts:204
                lib/graph/graph-invocation.ts:264
Root cause   → init installers run as import-time side effects and call
                window.addEventListener, which is undefined during SSR/prerender
Correction   → guard the single module-level call site with
                `if (typeof window !== 'undefined')`
Why minimal  → browser behaviour is byte-identical; no function bodies changed
```

### Fix 3 — `useSearchParams()` without a Suspense boundary (1 file)

Also revealed only after Fix 2, by the same masking effect.

```
Diagnosis    → "useSearchParams() should be wrapped in a suspense boundary at /accounts"
Obtained via → `next build --debug-prerender` (the plain build hid the cause)
File         → components/os-shell/app-shell.tsx
Symbol       → <DeepLinkSync /> (calls useSearchParams)
Correction   → wrap in <Suspense fallback={null}> per the Next.js documented fix
Result       → BUILD EXIT 0 — 17/17 static pages generated
```

### Fix 4 — APP-3 / cluster C-C: eslint lints vendored + generated output

```
Diagnosis    → C-C, FRONTEND_TOOLCHAIN + PRE_EXISTING. 43 of 44 lint errors came
                from public/pdf.worker.mjs, a vendored pdfjs-dist bundle.
File         → frontend/eslint.config.mjs  (the defect — NOT pdf.worker.mjs)
Correction   → add "public/**" and "dist/**" to globalIgnores
Note         → `distDir: 'dist'` in next.config.ts, so build output landed in dist/
                and was being linted as first-party source (observed: a stray build
                inflated the count from 44 to 292)
Result       → lint errors 44 → 35; the entire 43-error cascade eliminated
```

The vendored bundle itself was **not** edited, per §4.2/§4.4.

### Fix 5 — APP-2 / cluster C-B: ref read during render

```
Diagnosis    → C-B, react-hooks/refs at use-workspace-registration.ts:52
File         → lib/runtime/use-workspace-registration.ts
Correction   → useRef → useMemo for the value that is returned during render;
                registered.current (effect-only) left as a ref
Result       → file lints clean
```

### Verification after remediation

| Layer | Command | Exit | Result |
|-------|---------|------|--------|
| Frontend typecheck | `npx tsc --noEmit` | 0 | **PASS** (was already passing) |
| Frontend build | `npm run build` | 0 | **PASS** (was FAIL — 10 errors) |
| Frontend test | `npx vitest run` | 0 | **PASS — 1237/1237, 92/92 files** |
| Frontend lint | `npx eslint .` | 1 | 31 pre-existing errors remain (see below) |
| Backend | `run_backend_verification.sh` | 0 | **GREEN** — 26 + 206 + 468 passed |
| Runtime framework | `pytest runtime/tests` | 0 | **GREEN** — 291 passed |

`components/toolbar/__tests__/workspace-toolbar-performance.test.tsx` now passes inside the
full suite, consistent with the C-D `ENVIRONMENT` classification.

### Deliberate stop: 31 residual lint errors NOT fixed

| Rule | Count |
|------|-------|
| `react-hooks/set-state-in-effect` | 15 |
| `react-hooks/exhaustive-deps` | 8 |
| `react-hooks/static-components` | 2 |
| `react-hooks/purity` | 2 |
| `react-hooks/immutability` | 2 |
| `@next/next/no-sync-scripts` | 1 |
| `@next/next/no-assign-module-variable` | 1 |

These are **not repaired**, because:

1. Every affected file is **byte-identical to `bacc1fe2`** (verified per file with
   `git diff --quiet`) — all pre-existing.
2. None belongs to clusters C-A…C-D. §17 forbids repairing unrelated errors "unless they
   are proven to be part of the same causal cluster".
3. They are unrelated to the backend change (`in-blast-radius=0`).
4. They are genuine React-correctness findings across ~20 components — a separate,
   substantial workstream that must be diagnosed on its own terms, not folded into a
   forensic milestone.

**No suppression, downgrade, rule removal, threshold change or file exclusion was used to
hide them.** `eslint.config.mjs` still lints all first-party source with the same rules;
only vendored (`public/`) and generated (`dist/`) output was excluded, which is a
correctness fix, not a weakening.

Every file **I** modified lints clean (exit 0).

### Files changed (application)

```
frontend/lib/runtime/navigation-runtime.ts        + 'use client'
frontend/lib/runtime/selection-runtime.ts         + 'use client'
frontend/lib/runtime/timeline-runtime.ts          + 'use client'
frontend/lib/runtime/workspace-runtime.ts         + 'use client'
frontend/lib/runtime/use-workspace-registration.ts + 'use client', useRef → useMemo
frontend/lib/intelligence/intelligence-invocation.ts  SSR guard on init
frontend/lib/graph/graph-invocation.ts                SSR guard on init
frontend/components/os-shell/app-shell.tsx            Suspense around DeepLinkSync
frontend/eslint.config.mjs                            ignore public/ and dist/
```

Backend: **unchanged**, as required by §0.13 — no diagnostic finding implicated it.

---

## Phase 1.5 Completion

**Status:** DONE
**Completed:** 2026-08-11
**Final report:** `docs/verification/VEA2_PHASE1_5_REAL_WORLD_DIAGNOSIS.md`

### Final verification

```
runtime/tests            291 passed (281 baseline + 10 new), 0 failed
ruff check runtime/...   All checks passed
frontend tsc --noEmit    exit 0
frontend next build      exit 0 — Compiled successfully, 17/17 static pages
frontend vitest run      92/92 files, 1237/1237 tests passed
backend verification     exit 0 — 26 + 206 + 468 passed
frontend eslint          exit 1 — 31 pre-existing errors, deliberately out of scope (M13)
```

### Headline outcomes

1. **The backend change was innocent** — proven, not assumed, by reproducing every failure
   in an isolated worktree 5 commits earlier.
2. **There were zero TypeScript errors** — the prior agent loop chased a signal the
   compiler never emitted.
3. **The frontend production build was broken and invisible** — the verification script
   never ran `npm run build`. Now fixed and green.
4. **55 diagnostics → 3 root causes + 1 flaky test.**
5. **The framework gap was the real finding** — correct at
   change→capability→impact→selection, blind at failure→attribution. Closed and
   regression-tested (mutation-verified).

### Files changed

Framework:
```
runtime/foundation/intelligence/platform/attribution.py   (new)
runtime/foundation/intelligence/platform/cli_format.py    (+format_cross_layer_failure)
runtime/foundation/intelligence/__init__.py               (exports)
runtime/tests/test_failure_attribution.py                 (new, 10 tests)
.github/scripts/run_frontend_verification.sh              (phase decomposition + build)
```

Application:
```
frontend/lib/runtime/{navigation,selection,timeline,workspace}-runtime.ts
frontend/lib/runtime/use-workspace-registration.ts
frontend/lib/intelligence/intelligence-invocation.ts
frontend/lib/graph/graph-invocation.ts
frontend/components/os-shell/app-shell.tsx
frontend/eslint.config.mjs
```

Backend: **unchanged.**

### Next: VEA-2 Phase 2 — Evidence Correlation + Automated Diagnosis

Requirements handed off (see report §Handoff): E-1 JUnit emission, E-2 frontend evidence
model, E-3 unit-keyed evidence, E-4 replace keyword attribution with graph traversal,
credit-card over-prediction hop, 31 pre-existing React-hooks lint errors, GAP-003.

---

# VEA-2 Phase 2 — Evidence Integrity

**Execution document:** `.kilo/plans/1786342506938-vea2-phase2-evidence-integrity.md`
**Deferred-item register:** `docs/verification/VEA_BACKLOG.md`

**Objective:** Establish one durable identity spine from plan → execution → evidence, then
make Phase 1.5's attribution run automatically on real pipeline output.

```
VerificationUnit.id ──► VerificationStep.unit_id ──► ExecutionResult.unit_id ──► Evidence.unit_id
        │                                                                              │
        └────────────── provenance (capabilities, impact_kinds, source) ───────────────┘
```

**Reframing that drives this phase:** the repository contains two entirely disjoint
verification pipelines. The intelligence pipeline produces `VerificationUnit` with C11
provenance but **never executes a subprocess**. The orchestrator pipeline executes
`bash .github/scripts/run_*.sh` via `Executor` but **carries no provenance**. CI only ever
invokes the orchestrator. There is **no join key between planning and execution at all** —
Phase 1.5's attribution worked only because failures were hand-fed from manually parsed logs.

## Milestone Status

| Milestone | Status |
|-----------|--------|
| M0 Baseline and backlog register | DONE |
| M1 Stable verification-unit identity in the models | DONE |
| M2 Explicit unit ↔ registry mapping, UNMAPPED visible | DONE |
| M3 Thread identity through execution | DONE |
| M4 Per-phase structured evidence, keyed by unit | DONE |
| M5 Evidence model carries frontend and unit identity | DONE |
| M6 Attribution consumes real pipeline evidence | NOT_STARTED |
| M7 Re-run the Phase 1.5 specimen end-to-end | NOT_STARTED |

---

## M0 — Baseline and Backlog Register

**Status:** DONE
**Started:** 2026-08-11
**Completed:** 2026-08-11

### Objective

Freeze the starting state and create the deferred-item register, so that every later
milestone is measured against an immutable, evidenced baseline.

### Commands executed

```bash
git rev-parse HEAD
git status --porcelain
git branch --show-current
python3 -m pytest runtime/tests -q --no-header
bash .github/scripts/run_backend_verification.sh
bash .github/scripts/run_frontend_verification.sh
ls .github/workflows/*.yml | wc -l
grep -rn "verify\.py" .github/workflows/*.yml
git diff --quiet HEAD     -- <3 no-children-prop files>
git diff --quiet bacc1fe2 -- <3 no-children-prop files>
```

### Repository state

```
HEAD:    b9074020  fix(loan-engine): make amortization schedules exact and self-consistent
Branch:  recovery/program-r-forensic-reconstruction
```

Working tree carries the uncommitted Phase 1.5 deliverables (attribution.py, cli_format.py,
run_frontend_verification.sh phase decomposition, the 9 frontend remediation files) plus the
new `docs/verification/VEA_BACKLOG.md`. **No `.github/workflows/` file is modified.**

### Baseline verification status

| Layer | Command | Exit | Expected | Result |
|-------|---------|------|----------|--------|
| Runtime (framework) | `pytest runtime/tests -q` | 0 | 291 passed | **GREEN — 291 passed** (16.45s) |
| Backend | `run_backend_verification.sh` | 0 | exit 0 | **GREEN — 26 contract + 206 property + 468 unit/invariant** |
| Frontend | `run_frontend_verification.sh` | 1 | exit 1, lint-only | **RED — lint only**, as predicted |

Frontend per-phase decomposition (from `frontend-verification/v1` evidence):

```
lint       fail  exit=1  28s     ← the sole failure
typecheck  pass  exit=0   7s
build      pass  exit=0  49s
test       pass  exit=0 104s     ← 92/92 files, 1237/1237 tests
```

All three baseline expectations in plan M0.2 hold exactly.

### Files changed

```
docs/verification/VEA_BACKLOG.md   (new — deferred-item register)
docs/progress.md                   (this entry + phase header)
```

**No source file modified. No `.github/workflows/` file modified.**

### Evidence

- `runtime/generated/evidence/frontend/frontend-verification.json`
- `runtime/generated/evidence/frontend/{lint,typecheck,build,test}.log`
- `docs/verification/VEA_BACKLOG.md`

### Findings

**F-1 — Baseline lint count is 34, not 31. Corrected, with proof.**

The plan and Phase 1.5 M13 both cite **31** pre-existing lint errors. The measured value is
**34**. This is a **documentation gap in Phase 1.5, not a regression**:

| Rule | Phase 1.5 M13 table | M0 measured | Δ |
|------|--------------------|-------------|---|
| `react-hooks/set-state-in-effect` | 15 | 15 | 0 |
| `react-hooks/exhaustive-deps` | 8 | 8 | 0 |
| `react-hooks/static-components` | 2 | 2 | 0 |
| `react-hooks/purity` | 2 | 2 | 0 |
| `react-hooks/immutability` | 2 | 2 | 0 |
| `@next/next/no-sync-scripts` | 1 | 1 | 0 |
| `@next/next/no-assign-module-variable` | 1 | 1 | 0 |
| **`react/no-children-prop`** | **absent from table** | **3** | **+3** |
| **Total** | **31** | **34** | **+3** |

Every one of the 31 documented errors is still present, unchanged. The delta is exactly one
rule that Phase 1.5's table omitted. Pre-existence was **proven, not inferred** (§1
`PROVEN over PROBABLE`):

```
frontend/components/dashboard/cashflow-chart.tsx:53:72
frontend/components/dashboard/category-spend-chart.tsx:39:72
frontend/components/graph/graph-overlay.tsx:160:9
```

All three are byte-identical to **both** `HEAD` and `bacc1fe2` (`git diff --quiet` → clean),
i.e. unchanged since five commits before the change under test. They were not introduced by
Phase 1.5 remediation and are not caused by the backend change.

Phase 1.5's own narrative separately recorded lint dropping "44 → 35" after excluding
vendored `public/`/generated `dist/`, which is already inconsistent with its 31-row table.
The measured value supersedes both.

**Consequence for the completion gate:** the §4 Restraint criterion "the 31 lint errors
remain exactly 31" is **corrected to exactly 34**, with the per-rule distribution above.
Recorded in `VEA_BACKLOG.md` BL-001 as the binding baseline. Any deviation in either
direction means scope leaked.

**F-2 — CI workflow topology baseline recorded (9 workflows, 7 profile-invoking).**

`ls .github/workflows/*.yml | wc -l` → **9**. Seven invoke a distinct `verify.py <profile>`:
`backend`(:51), `frontend`(:61), `golden`(:45), `mutation`(:52), `playwright`(:71),
`quick`(:46), `runtime`(:54). The other two (`dependency-update.yml`, `release.yml`) invoke
no profile.

Trigger overlap confirmed as described in plan §2.1, with two refinements worth recording:

- `quality.yml` has **no `paths:` filter at all** and triggers on `push: branches: ["**"]` —
  it runs on every push to every branch.
- `playwright.yml` is branch-restricted to `main`/`master`/`develop`, unlike
  `backend-verify`/`frontend-verify`/`verification-runtime` which run on `"**"`. So the
  "~5 workflow fan-out" for `backend/src/routers/**` is branch-dependent, not universal.
- `golden.yml` and `mutation.yml` are cron-triggered (03:00 / 02:00 daily) — by design, not
  redundancy.

Full map, overlap table and audit constraints recorded in `VEA_BACKLOG.md` BL-004. This is
**observation only**; no workflow file was read-modified.

**F-3 — The plan's structural claim is confirmed at baseline.** The frontend evidence JSON
already carries per-phase status but has **no unit identity field**, and the manifest the
later milestones consume does not yet exist. There is currently no artifact anywhere that
joins a planned unit to an executed command.

### Blockers

None.

### Decision

Baseline frozen and accepted. Proceeding to M1 with the corrected lint baseline of **34**
rather than the plan's stated 31, because the plan's hard invariant requires the measured,
proven value to win over the documented one. The correction is recorded in the backlog
register and will be re-asserted at M7.

### Next milestone

M1 — Stable verification-unit identity in the models.

---

## M1 — Stable Verification-Unit Identity in the Models

**Status:** DONE
**Started:** 2026-08-11
**Completed:** 2026-08-11

### Objective

Give the execution layer a place to carry identity and provenance, so that later
milestones can thread a stable join key from plan → execution → evidence.

### Commands executed

```bash
grep -rn "ExecutionResult(" --include=*.py .    # → 5 sites, all executor.py
grep -rn "VerificationStep(" --include=*.py .   # → 2 sites, all planner.py
python3 -m pytest runtime/tests/test_verification_identity.py -q --no-header
python3 -m pytest runtime/tests -q --no-header
python3 -m ruff check runtime/foundation/verification/models/model.py \
                      runtime/tests/test_verification_identity.py
git status --porcelain runtime/tests/snapshots/
```

### Files inspected

```
runtime/foundation/verification/models/model.py
runtime/foundation/verification/planner/planner.py   (construction sites + dedup, ~630-690)
runtime/foundation/verification/executor.py          (construction sites)
runtime/tests/test_orchestrator.py                   (test conventions)
```

### Files changed

```
runtime/foundation/verification/models/model.py      +32 / -2
runtime/tests/test_verification_identity.py          (new, 18 tests)
```

### Change detail

Added to **both** `VerificationStep` and `ExecutionResult`, optional and defaulted:

```python
unit_id: str | None = None
provenance: dict[str, Any] = field(default_factory=dict)
```

- `frozen=True, slots=True` preserved on both dataclasses (asserted by test).
- `provenance` mirrors the C11 shape already emitted by
  `VerificationUnit.to_dict()["provenance"]`: `capabilities`, `impact_kinds`, `source`.
- A docstring on each dataclass records **why `id` must not be used as the join key**:
  step IDs are positional (`step-0001`) and are *reassigned* during command dedup
  (`planner.py` ~line 660), so they are unstable across runs.

### Tests executed (counts before → after)

```
runtime/tests   291 passed  →  309 passed   (291 baseline unmodified + 18 new)
ruff check      All checks passed
snapshots       unchanged (git status clean) — change is purely additive
```

Construction-site verification confirmed the plan's estimate exactly: **5**
`ExecutionResult` sites (all `executor.py`), **2** `VerificationStep` sites (all
`planner.py`). None required modification.

### Test coverage

| Requirement | Test class |
|-------------|-----------|
| Defaults are `None` / `{}` | `TestBackwardsCompatibility` |
| **Negative:** construction without new fields must not raise | `test_step_constructs_without_new_fields`, `test_result_constructs_without_new_fields` |
| Round-trip retention of `unit_id` + `provenance` | `TestIdentityRoundTrip` |
| `frozen`/`slots` preserved | `TestImmutabilityPreserved` |
| `None` is a legitimate visible state (`UNMAPPED` precursor) | `TestUnmappedIsLegitimate` |

Two invariants were tested beyond the plan's minimum, both guarding defect classes Phase 2
is specifically trying to avoid:

- `test_unit_id_is_not_normalised_or_rewritten` — the join key must survive byte-for-byte;
  any slugifying/casing would silently break joins or make distinct units collide.
- `test_default_provenance_is_not_shared_between_instances` — a shared mutable default
  would leak provenance between steps and produce false attribution.

### Test strength verified by mutation

Tests confirmed load-bearing, not tautological. Injecting a mutant that defaults
`VerificationStep.unit_id` to a bogus value:

```
unit_id: str | None = "MUTANT"
→ 1 failed, 17 passed   (mutant killed by test_step_defaults_are_none_and_empty_dict)
```

Mutant reverted; suite restored to 18/18 passing.

### Findings

**F-4 — The dedup path is confirmed as the M3 risk point.** Reading `planner.py:650-689`
during construction-site analysis confirms the plan's §M3.5 concern is real: dedup rebuilds
each surviving `VerificationStep` field-by-field. Any field not explicitly copied there is
**silently dropped**. `unit_id`/`provenance` must be added to that reconstruction in M3, and
the collapse of two units onto one command must retain *both* IDs rather than the first.
Recorded now so M3 does not rediscover it by regression.

### Blockers

None.

### Decision

M1 accepted. The change is strictly additive: no existing construction site touched, no
snapshot churn, no behavioural change. Acceptance criteria met — 291 baseline tests pass
unmodified, new model tests pass, ruff clean on changed files.

### Next milestone

M2 — Explicit unit ↔ registry mapping, with `UNMAPPED` visible.

---

## M2 — Explicit Unit ↔ Registry Mapping, with UNMAPPED Visible

**Status:** DONE
**Started:** 2026-08-11
**Completed:** 2026-08-11

### Objective

Establish the join between the 10 optimizer unit IDs and the registry's workflow IDs,
explicitly and machine-checked — never by inference.

### Commands executed

```bash
grep -oE 'id="[a-z-]+",' runtime/foundation/intelligence/platform/optimizer.py | sort -u
python3 -c "<regex scrape of optimizer unit IDs>"      # → closed set of 10 confirmed
python3 -m pytest runtime/tests/test_verification_unit_mapping.py -q --no-header
python3 -m pytest runtime/tests -q --no-header
python3 -m ruff check runtime/foundation/verification/registry/ \
                      runtime/tests/test_verification_unit_mapping.py
```

### Files inspected

```
runtime/foundation/intelligence/platform/optimizer.py   (unit declarations + C11 provenance)
runtime/foundation/intelligence/platform/cost.py        (_SKIPPED_BASELINE_SECONDS)
runtime/foundation/verification/registry/registry.py    (workflow/script IDs)
```

### Files changed

```
runtime/foundation/verification/registry/registry.py     +UNMAPPED, +UNIT_TO_WORKFLOW,
                                                          +resolve_unit_workflow(),
                                                          +resolve_unit(),
                                                          +get_workflow_for_unit()
runtime/foundation/verification/registry/__init__.py     exports
runtime/tests/test_verification_unit_mapping.py          (new, 29 tests)
```

### The mapping

Closed set of 10 optimizer units confirmed **from source**, not assumed:

| Unit | → Workflow | Justification |
|------|-----------|---------------|
| `unit-targeted` | `backend` | Runs provider-recorded pytest files per impacted engine. The orchestrator has no per-file script; that work is executed inside `run_backend_verification.sh`. |
| `backend-unit` | `backend` | Runs `backend/tests/unit/` — same executed script. **Many-to-one with `unit-targeted`, deliberate.** |
| `backend-integration` | `integration` | Runs `backend/tests/integration/`; `run_integration_tests.sh` is the dedicated entry point. |
| `contracts-schemathesis` | `contracts` | Runs `backend/tests/contract/`; `run_contract_tests.sh` is the contract entry point. |
| `frontend-unit` | `frontend` | vitest work. |
| `frontend-typecheck-build` | `frontend` | tsc+build work. **Many-to-one with `frontend-unit`**: one script runs lint+typecheck+build+test behind a single exit code. M4 per-phase evidence is what re-separates them. |
| `playwright-e2e` | `playwright` | Direct. |
| `runtime-self-test` | `runtime` | Direct. |
| `mutation-run` | `mutation` | Cost-gated; maps so an explicitly-requested run is still joinable. |
| `golden-regression` | `golden` | Cost-gated; same rationale. |

`UNMAPPED` sentinel added: a reportable outcome, surfaced in the M3 manifest, never
silently dropped and never guessed.

### Tests executed (counts before → after)

```
runtime/tests   309 passed  →  338 passed   (291 baseline + 18 M1 + 29 M2)
ruff check      All checks passed
snapshots       unchanged
```

### Test coverage

| Requirement | Test |
|-------------|------|
| **Coverage test** — every one of the 10 units has a mapping decision | `test_every_optimizer_unit_has_a_mapping_decision` |
| Coverage derived from optimizer source, not just a literal | `test_coverage_is_derived_from_the_optimizer_not_just_the_literal` |
| Cost-gated units resolve without error | `test_cost_gated_unit_resolves_without_error` |
| Unknown ID → `UNMAPPED`, no raise, no guess | `TestUnmappedIsReachableAndNeverGuessed` |
| Many-to-one explicit | `test_many_to_one_collapses_are_exactly_the_documented_ones` |
| Mapped workflows actually exist and have commands | `TestMappingTargetsAreReal` |

### Findings

**F-5 — `mutation-run` and `golden-regression` are skip-only units.** Verified from
source: they are declared **only** in the `skipped` loop and never as a
`VerificationUnit`, so they have no `command` and can never be selected. They are still
mapped, so that an explicitly-requested heavy run remains joinable to unit identity. This
is recorded rather than treated as an anomaly, and asserted by
`test_cost_gated_units_are_never_selected_by_the_optimizer`.

**F-6 — Two documented many-to-one collapses exist, and both matter for M3.**
`{unit-targeted, backend-unit} → backend` and
`{frontend-unit, frontend-typecheck-build} → frontend`. These are exactly the cases where
plan §M3.5 requires the surviving deduped step to retain **all** contributing unit IDs.
`test_many_to_one_collapses_are_exactly_the_documented_ones` pins the set, so a new,
undecided collapse cannot appear silently.

### Test strength verified by mutation

Two mutants, both killed, both reverted:

```
MUTANT 1  remove the "playwright-e2e" mapping row
          (simulates a new unit added with no mapping decision)
          → 2 failed, 27 passed   ← coverage test fired, as designed

MUTANT 2  reintroduce the E-4 defect class in resolve_unit_workflow():
              if known in unit_id.lower() or unit_id.lower() in known: return workflow
          → 7 failed, 22 passed   ← every near-miss guard fired
```

Mutant 2 is the important one. It proves the anti-inference guard is real: substring,
prefix and case-insensitive "helpful" matching are each caught on distinct inputs
(`backend`, `BACKEND-UNIT`, `backend-unit-extra`, `frontend`, `unit`, `backend-`, `""`).
If a future agent reintroduces keyword joining, CI fails immediately.

### Blockers

None.

### Decision

M2 accepted. The mapping is enumerated with a per-row justification, machine-checked for
coverage against optimizer source, and `UNMAPPED` is reachable and asserted. No heuristic,
category or substring inference exists on the lookup path.

### Next milestone

M3 — Thread identity through execution (planner population, orchestrator copy, run manifest).

---

## M3 — Thread Identity Through Execution

**Status:** DONE
**Started:** 2026-08-11
**Completed:** 2026-08-11

### Objective

Make `unit_id` + provenance survive plan → execute → result, and emit the run manifest
that becomes the durable join-key artifact for M5/M6.

### Commands executed

```bash
# Control capture, before and after, across all 7 profiles
python3 -c "<plan every profile, print step id + command>"     # pre-change control
PYTHONHASHSEED=0 python3 -c "<same>"                            # pinned-seed control
git stash push <changed files> && <re-run control> && git stash pop
diff /tmp/kilo/pre_pinned.txt /tmp/kilo/post_pinned.txt

PYTHONHASHSEED=0 python3 runtime/verify.py runtime              # real run → manifest
python3 -m pytest runtime/tests/test_verification_identity_execution.py -q
python3 -m pytest runtime/tests -q --no-header
python3 -m ruff check runtime/foundation/verification/
```

### Files changed

```
runtime/foundation/verification/planner/planner.py       unit_id/provenance population
                                                          + dedup identity merge
runtime/foundation/verification/orchestrator.py          identity copy onto results,
                                                          + write_run_manifest(),
                                                          + _current_branch()
runtime/foundation/verification/registry/registry.py     + units_for_workflow()
runtime/foundation/verification/registry/__init__.py     export
runtime/tests/test_verification_identity_execution.py    (new, 34 tests)
```

### Executed-command control — the central Phase 2 invariant

Plan §M3 acceptance requires the executed command list to be byte-identical to pre-M3.
Verified by capturing all 7 profiles' planned steps from **pristine `HEAD` code**
(via `git stash`) and from the M3 tree, under `PYTHONHASHSEED=0`:

```
diff pre_pinned.txt post_pinned.txt
→ *** BYTE-IDENTICAL — M3 changes nothing executed ***
```

Same commands, same order, same step IDs across `quick`, `backend`, `frontend`,
`runtime`, `golden`, `mutation`, `playwright`.

### Findings

**F-7 — PRE-EXISTING DEFECT: planner step ordering is non-deterministic.**
*Discovered while establishing the M3 control. Not introduced by this milestone.*

The first control diff showed step *ordering* differing between runs — a STOP-condition
signal ("changing step ordering"). Investigation proved the cause is **pre-existing**, not
the M3 change:

```
# pristine HEAD code, git-stashed, 3 consecutive runs of profile "mutation":
run_fast_checks | run_backend_verification | run_runtime_verification | run_mutation_selective
run_runtime_verification | run_fast_checks | run_backend_verification | run_mutation_selective
run_fast_checks | run_backend_verification | run_runtime_verification | run_mutation_selective
```

Root cause located and proven, not guessed:

- `planner.py::_determine_workflows_scripts` builds `workflows`/`scripts` as **unordered
  `set()`s** (lines ~528-556) and an unordered `capabilities` set iterated at
  `for cap_id in capabilities:`, whose `workflows.update(cap.workflows)` insertion order
  therefore varies.
- Although the function returns `sorted(...)`, the variance has already entered upstream
  and propagates into which workflow `_build_steps` selects first per target.
- **Proof:** with `PYTHONHASHSEED=0` the ordering is stable across every repeat run;
  without it, it varies. Python string-hash randomisation is the driver.

**Handling — deliberately NOT fixed.** Correcting it would change the order in which CI
executes scripts, which is precisely what plan §M3 prohibits ("changing step ordering or
dedup semantics") and what the Phase 2 control exists to hold constant. It is recorded
here and added to `VEA_BACKLOG.md` as **BL-009** for a later phase. The M3 control was
instead established under a pinned hash seed, which isolates the variable and still
proves M3 itself is behaviourally neutral.

This also has a consequence worth flagging for Group E (BL-004): the future CI-topology
audit cannot rely on step order to prove execution equivalence between workflows. It must
compare the command *set* keyed by `unit_id`, which the manifest now makes possible.

**F-8 — Identity population is by explicit reverse lookup, not inference.** The planner
already resolves the owning registry workflow, which is the *target* of the M2 table, so
`units_for_workflow()` performs an enumerated reverse lookup. No command string, target
name or category is pattern-matched at any point.

**F-9 — F-4 confirmed and closed.** The dedup rebuild did silently drop unlisted fields,
as predicted at M1. `merged_units` now accumulates contributing unit IDs per command
*before* dedup collapses them, and the rebuild carries the full set. Verified live: the
`backend` profile's deduped step retains `['backend-unit', 'unit-targeted']`.

### Real-run evidence

`runtime/generated/evidence/run-manifest.json` (`run-manifest/v1`), from
`python runtime/verify.py runtime` (exit 0):

```json
{ "schema": "run-manifest/v1",
  "commit": "b9074020...", "branch": "recovery/program-r-forensic-reconstruction",
  "profile": "runtime",
  "steps": [{ "step_id": "step-0001", "unit_id": "runtime-self-test",
              "contributing_units": ["runtime-self-test"],
              "command": "bash .github/scripts/run_runtime_verification.sh",
              "exit_code": 0, "status": "passed",
              "provenance": { "source": "registry-workflow-mapping", ... } }],
  "unmapped": [] }
```

Many-to-one and UNMAPPED both verified live on the `backend` profile:

```
step-0001  runtime-self-test  ['runtime-self-test']
step-0002  UNMAPPED           []                              ← run_fast_checks.sh, reported
step-0003  backend-unit       ['backend-unit', 'unit-targeted'] ← both retained
```

### Tests executed (counts before → after)

```
runtime/tests   338 passed  →  372 passed   (291 baseline + 18 M1 + 29 M2 + 34 M3)
ruff check      All checks passed
snapshots       unchanged — no regeneration needed, change is additive
```

M3 tests were confirmed robust to hash randomisation (3 unpinned repeat runs, 34/34 each).

### Test coverage

| Requirement | Test |
|-------------|------|
| Planned step carries expected `unit_id` | `TestPlannedStepsCarryIdentity` |
| `ExecutionResult` carries the same `unit_id` as its step | `TestExecutionResultCarriesIdentity` |
| Manifest round-trips and contains provenance | `TestRunManifest` |
| **Dedup: two units → one command → both IDs retained** | `test_many_to_one_collapse_retains_all_contributing_units` |
| **Negative:** unmapped step → `UNMAPPED`, run does not crash | `TestUnmappedIsVisibleAndNonFatal` |
| Commands unchanged / IDs positional | `TestExecutedCommandsAreUnchanged` |

### Test strength verified by mutation

```
MUTANT A  dedup keeps only the first unit (all_units = [step.unit_id])
          → 2 failed, 32 passed   ← dedup-preservation guard fired

MUTANT B  orchestrator stops copying unit_id/provenance onto ExecutionResult
          → 5 failed, 29 passed   ← identity-copy guard fired
```

Both reverted; suite restored to 34/34.

### Blockers

None. F-7 was a candidate STOP condition, resolved by proving it pre-existing and
deferring the fix rather than silently changing CI ordering.

### Decision

M3 accepted. Identity flows plan → step → result → manifest; executed commands are
byte-identical under controlled conditions; dedup no longer loses identity; `UNMAPPED` is
visible and non-fatal. The pre-existing ordering non-determinism (F-7) is recorded and
deferred, not repaired, because repairing it would violate the phase's own control.

### Next milestone

M4 — Per-phase structured evidence, keyed by unit (backend phase decomposition + JUnit XML).

---

## M4 — Per-Phase Structured Evidence, Keyed by Unit

**Status:** DONE
**Started:** 2026-08-11
**Completed:** 2026-08-11

### Objective

Generalize the Phase 1.5 frontend phase decomposition to the backend and key all of it by
`unit_id`. **E-1 (JUnit) lands here as one artifact among several, not as the objective.**

### Commands executed

```bash
bash -n .github/scripts/run_backend_verification.sh
VERIFICATION_UNIT_ID=backend-unit bash .github/scripts/run_backend_verification.sh
BACKEND_EVIDENCE_DIR=... bash .github/scripts/run_backend_verification.sh   # fail direction
python3 -c "<TestResultCollector(REPO_ROOT).collect()>"
python3 -m pytest runtime/tests/test_backend_evidence.py -q
python3 -m pytest runtime/tests -q --no-header
git check-ignore -v backend/tests/generated/junit.xml runtime/generated/evidence/...
```

### Files changed

```
.github/scripts/run_backend_verification.sh    per-phase evidence, JUnit, unit_id
.github/scripts/run_frontend_verification.sh   + VERIFICATION_UNIT_ID in summary only
runtime/tests/test_backend_evidence.py         (new, 31 tests)
```

**No `.github/workflows/` file modified** (asserted by `TestNoWorkflowFilesTouched`).

### Change detail

`run_backend_verification.sh` now emits, per suite phase — `contract`, `invariants`,
`properties`, `unit-engines`:

- status, exit code, duration, log path, JUnit path;
- `runtime/generated/evidence/backend/backend-verification.json`
  (`backend-verification/v1`), mirroring the frontend `frontend-verification/v1` shape;
- `--junitxml` per suite, plus a merged `backend/tests/generated/junit.xml`.

Phase names are resolved by an **explicit `phase_name_for()` case statement**, not by
string-munging the directory path, so a renamed directory produces `unknown` loudly rather
than silently renaming a phase.

Both scripts accept `VERIFICATION_UNIT_ID` and record it in their JSON summary. When
unset it is recorded as `""` — absent, never guessed.

**Preserved exactly:** the pytest commands, the four-way parallelism, and the exit-code
contract. Per-suite exit codes are now captured positionally (`codes+=`) instead of being
collapsed into a single flag, which is what makes per-phase attribution possible.

### E-1 closed — verified against the existing consumer

The merged JUnit is written to `backend/tests/generated/junit.xml`, exactly the path
`EvidenceAggregator._collect_test_results()` has always probed and never found. Verified
by running the **existing, unmodified** `TestResultCollector`:

```
passed=861  failed=0  error=0  skipped=0  duration=154.7s
```

861 = 26 contract + 206 property + 468 unit/engines + 161 invariants. The collector that
had been dead code since VEA-1 now receives real data.

### Exit-code contract verified in BOTH directions

Plan M4 requires asserting both. A script only ever observed passing is not verified.

```
all-pass tree            → exit 0, overall_status "pass"
one injected failing test → exit 1, overall_status "fail"
                            failing phases == ["invariants"]   ← attributable
```

The injected probe was removed and the tree confirmed clean
(`git status --porcelain backend/` → empty).

This is the concrete improvement: previously a backend failure produced one opaque exit
code; it is now attributed to the exact suite that failed.

### Real-run evidence

```
runtime/generated/evidence/backend/backend-verification.json   (backend-verification/v1)
runtime/generated/evidence/backend/{contract,invariants,properties,unit-engines}.log
runtime/generated/evidence/backend/{...}-junit.xml             (4 files)
backend/tests/generated/junit.xml                              (merged, collector path)
```

Backend verification still exits 0 on the current tree; wall clock 74s for suites
totalling ~85s of work, confirming parallelism is intact.

Both artifact locations are already covered by `.gitignore` (lines 47 and 84), so no
generated evidence enters the repository.

### Tests executed (counts before → after)

```
runtime/tests (excl. M4)   372 passed          (unchanged — no regression)
runtime/tests/test_backend_evidence.py   31 passed  (120s; includes the both-directions
                                                     exit-contract test, which runs the
                                                     real backend suite twice)
ruff check                 All checks passed
```

### Test coverage

| Requirement | Test |
|-------------|------|
| Backend JSON validates against its schema and lists every phase | `TestBackendEvidenceSchema` |
| JUnit produced and parses with existing `TestResultCollector` | `TestJUnitEmission` |
| **Exit code 0 on all-pass, 1 on any-fail (both asserted)** | `test_backend_exit_contract_holds_both_directions` |
| Backend suite still runs in parallel | `test_suites_still_run_in_parallel` |
| Frontend evidence unchanged in shape | `TestFrontendEvidenceUnchangedInShape` |
| `VERIFICATION_UNIT_ID` accepted and recorded, never guessed | `TestUnitIdPropagation` |
| Workflows untouched | `TestNoWorkflowFilesTouched` |

### Findings

**F-10 — A stale-evidence trap was found and designed out.** The first run of
`test_junit_is_parseable_by_the_existing_collector` failed with `failed=1`, because the
merged `junit.xml` still contained the earlier exit-contract probe's deliberate failure.
The test was asserting `failed == 0`, which made it a hostage to unrelated prior state.

Rather than deleting the artifact and moving on, the assertion was corrected to test what
E-1 actually claims — that the collector *finds and parses* tests, and that counts are
internally consistent (`len(failed_test_names) == failed`). Pinning the file to green
would have been a test that passes for the wrong reason.

**F-11 — Per-phase decomposition changes what a backend failure means.** Before M4 the
only recoverable fact was "backend verification failed". The `invariants`-only failure
injected during the contract test is now isolated in both the JSON summary and its own
JUnit file, so M5/M6 can attribute it to a unit and phase without parsing prose logs.

### Blockers

None.

### Decision

M4 accepted. Backend evidence JSON + JUnit XML exist after a real run, frontend evidence
shape is unchanged, backend verification still exits 0 on the current tree, and the suite
still runs in parallel. E-1 is closed and demonstrated against the pre-existing consumer
rather than a new one.

### Next milestone

M5 — Evidence model carries frontend and unit identity (closes E-2 and E-3).

---

## M5 — Evidence Model Carries Frontend and Unit Identity

**Status:** DONE
**Started:** 2026-08-11
**Completed:** 2026-08-11

### Objective

Close **E-2** (frontend structurally unrepresentable) and **E-3** (no unit↔failure
linkage) in `EvidenceAggregator`, without touching the E-4 keyword functions.

### Commands executed

```bash
python3 -m pytest runtime/tests/test_evidence_aggregator.py -q      # must pass UNMODIFIED
python3 -m pytest runtime/tests/test_evidence_frontend_units.py -q
python3 -m pytest runtime/tests -q --no-header
python3 -m ruff check runtime/system/evidence/
git diff --stat runtime/system/evidence/aggregator.py               # additive-only check
```

### Files changed

```
runtime/system/evidence/aggregator.py            +248 / -0   (purely additive)
runtime/tests/test_evidence_frontend_units.py    (new, 32 tests)
```

### Change detail

**E-2 — `EvidenceSummary.frontend`.** New section populated from the M4
`frontend-verification/v1` evidence: per-phase `lint`/`typecheck`/`build`/`test` with
status, exit code, duration and log path. Rendered in the markdown report. Previously the
only occurrence of "frontend" in this module was a synthesized `suggested_layer` string,
so a red frontend build left no trace at all.

**E-2 — `overall_status` accounts for the frontend.** A failing frontend phase raises a
`frontend_verification_failed` attention item, which forces `attention_needed`. A red
frontend build can no longer be reported as `pass`.

**E-3 — `EvidenceSummary.unit_failures`.** A unit-keyed failure list joined via the M3 run
manifest. Each entry carries `unit_id`, `layer`, `phase`, `path`, `diagnostic`,
`provenance` and `contributing_units`. Both frontend phases and backend suite phases are
covered.

**Join discipline.** The join key comes from the manifest, matched **by workflow**, never
by string matching against commands or test names. `_collect_unit_failures` contains no
`startswith`/`endswith`/`in command`/`re.search`, asserted by test.

### E-4 left in place and untouched — verified

Plan M5 prohibits rewriting or extending `_find_chain_for_failure()` /
`_find_dependency_chain()`. Verified mechanically:

```
git diff --stat runtime/system/evidence/aggregator.py
→ 1 file changed, 248 insertions(+)        ← zero deletions, zero modifications
```

`TestE4RemainsUntouched` additionally asserts, via `inspect.getsource`, that **none** of
the five new methods reference either keyword function. Phase 2 bypasses E-4; it does not
build on it. It remains a known defect owned by Phase 3 (`VEA_BACKLOG.md` BL-003).

### Tests executed (counts before → after)

```
runtime/tests (excl. slow M4)   372 →  404 passed   (+32 M5)
test_evidence_aggregator.py     8 passed, UNMODIFIED   ← plan M5 acceptance
ruff check                      All checks passed
```

### Test coverage

| Requirement | Test |
|-------------|------|
| Frontend build failure appears in `EvidenceSummary.frontend` | `TestFrontendIsRepresentable` |
| A red frontend forces a non-pass overall | `TestFrontendFailureForcesNonPass` |
| Unit-keyed failures carry provenance end-to-end | `test_failure_carries_provenance_end_to_end` |
| Backend-only runs aggregate exactly as before | `TestBackendAggregationUnchanged` |
| **Negative:** missing frontend evidence → `not_run`, not `pass` | `TestMissingFrontendEvidenceIsNotRun` |
| E-4 untouched and uncalled | `TestE4RemainsUntouched` |

### Test strength verified by mutation — one real gap found and closed

```
MUTANT A  frontend_failed = False   (frontend failure ignored)
          → 3 failed, 27 passed     ← killed

MUTANT B  join falls back to the FIRST manifest entry when no workflow matches
          (i.e. reintroduce the E-4 "first entry wins" defect in a new format)
          → 30 passed, 0 failed     ← *** SURVIVED ***
```

**Mutant B initially survived.** That is a genuine weakness in the first draft of the test
suite: the very defect class Phase 2 exists to eliminate would have passed CI. Rather than
accept it, two tests were added:

- `test_unrelated_manifest_entry_is_never_borrowed` — the manifest contains only a
  *backend* step; a frontend failure must resolve to `UNMAPPED` and must **not** inherit
  `backend-unit` or its provenance.
- `test_join_is_by_workflow_not_by_position` — manifest ordering must not influence the
  join.

Re-running Mutant B against the strengthened suite:

```
→ 1 failed, 31 passed              ← killed
```

Mutant reverted; suite restored to 32/32.

### Findings

**F-12 — Mutation testing caught what review did not.** The original E-3 tests all passed
against a mutant that borrowed an unrelated unit's identity, because every fixture happened
to contain a matching `frontend` workflow entry. Tests that only exercise the happy join
cannot detect a bad fallback. The negative case — *a manifest that deliberately contains
no matching entry* — is what makes the guard real. This is the same lesson as E-4 itself:
a join that always returns something looks correct until you ask it about something it
does not know.

**F-13 — `not_run` vs `pass` is now structurally enforced.** Missing or corrupt frontend
evidence yields an empty `frontend` dict and never contributes a `pass`. Corrupt JSON is
caught and treated as absent rather than crashing aggregation.

### Blockers

None.

### Decision

M5 accepted. The frontend is representable, failures are joinable to units and provenance,
`test_evidence_aggregator.py` passes unmodified, and the E-4 functions are provably
untouched and uncalled.

### Next milestone

M6 — Attribution consumes real pipeline evidence (`verify.py diagnose-failures`).

---

## M6 — Attribution Consumes Real Pipeline Evidence

**Status:** DONE
**Started:** 2026-08-11
**Completed:** 2026-08-11

### Objective

Remove the Phase 1.5 hand-fed-log dependency: attribution now runs on the M3
manifest + M4/M5 evidence, with `unit_id` as the join key — never a string match
against a command or test name (the E-4 defect class).

### Commands executed

```bash
python3 -m pytest runtime/tests/test_diagnose_failures.py -q
python3 -m pytest runtime/tests/test_failure_attribution.py test_cross_layer_planner.py -q  # 25 unmodified
python3 -m pytest runtime/tests -q --no-header --ignore=test_backend_evidence.py   # 404 → 412
python3 -m ruff check runtime/foundation/intelligence/platform/attribution.py runtime/verify.py runtime/tests/test_diagnose_failures.py
python3 runtime/verify.py diagnose-failures        # real end-to-end, zero manual parsing
git diff --stat runtime/foundation/intelligence/platform/attribution.py
```

### Files changed

```
runtime/foundation/intelligence/platform/attribution.py   +58 / -0   (additive adapter)
runtime/verify.py                                       +44 / -1   (diagnose-failures subcommand)
runtime/tests/test_diagnose_failures.py                 (new, 8 tests)
```

### Change detail

**Adapter `build_observed_failures(unit_failures)`.** Pure translation from the M5
`EvidenceSummary.unit_failures` shape into `ObservedFailure` records. The `unit_id`
is taken verbatim (it already carries the M3 manifest join done in M5); no inference
happens here. Two behaviours:

- A failure whose `unit_id == UNMAPPED` could not be tied to a verification scope, so
  its file path is blanked and it is reported as `ATTRIBUTION_UNKNOWN` — honestly, not
  as a guessed `OUTSIDE_BLAST_RADIUS`. The real evidence path is preserved in `code`.
- `pre_existing` is populated **only** when the evidence records it. Absent evidence
  leaves it `None` → `OUTSIDE_BLAST_RADIUS`, never `PRE_EXISTING`. No inference.

**`cmd_diagnose_failures` in `verify.py`.** Computes the change/blast/plan via the
intelligence platform, aggregates the M5 evidence from `runtime/generated/evidence`,
builds the observed failures, runs `attribute_failures`, and renders
`format_cross_layer_failure`. Exit code is 1 only when the change is actually
implicated — an unrelated red pipeline is not a diagnostic failure.

### Compliance with the plan's hard invariant

- No `re.search`/`startswith`/`endswith`/`in command`/`.find()` in
  `build_observed_failures` — asserted by `test_adapter_performs_no_string_matching`
  via `inspect.getsource`.
- `UNMAPPED_UNIT` equals `EvidenceAggregator.UNMAPPED_SENTINEL` — asserted
  (`test_unmapped_constant_matches_aggregator_sentinel`), so the two joinable halves
  stay consistent.
- `attribute_failures`, `ObservedFailure`, `FailureAttribution`, `AttributionReport`
  verdict semantics are **untouched** (the function body is unchanged; only
  `build_observed_failures` + `__all__` were added — verified by `git diff --stat`:
  1 file changed, 58 insertions, 0 deletions).

### Tests executed (counts before → after)

```
runtime/tests (excl. slow M4)   404 →  412 passed   (+8 M6)
Phase 1.5 attribution tests      25 passed, UNMODIFIED   ← plan M6 acceptance
ruff check                        All checks passed
```

### Test coverage

| Requirement | Test |
|-------------|------|
| Artifacts-alone verdict matches Phase 1.5 (`in_blast_radius=0`, not implicated) | `test_adapter_reproduces_phase1_5_verdict_from_artifacts_alone` |
| Synthetic in-radius failure still implicates (guards over-correction) | `test_synthetic_in_radius_failure_still_implicates` |
| Unjoinable failure → `ATTRIBUTION_UNKNOWN`, surfaced | `test_unjoinable_failure_is_attribution_unknown` |
| **Negative:** no evidence → explicit "nothing to diagnose", no fabricated verdict | `test_no_evidence_state_is_explicit_not_fabricated` |
| `pre_existing` never inferred | `test_pre_existing_is_never_inferred` |
| No string matching (E-4 forbidden) | `test_adapter_performs_no_string_matching` |

### Test strength verified by mutation — required check passed

```
MUTANT  "forcing the join to always match" — drop the UNMAPPED branch so every
        failure (even an unjoinable one) is matched against the blast radius by its
        real path, instead of being reported UNKNOWN
        → 1 failed, 7 passed     ← killed (test_unjoinable_failure_is_attribution_unknown)
```

Mutant reverted; suite restored to 8/8.

### Findings

**F-14 — A genuine mutation weakness, caught proactively this time.** After M5 caught
Mutant B by adding a negative test, M6's first probe was designed *before* writing the
unjoinable test was trusted: the "join always matches" mutant is exactly the E-4
defect class ("first entry / always match wins") re-expressed for Phase 2. A suite that
only asserted `OUTSIDE_BLAST_RADIUS` counts would have let it pass. The dedicated
`ATTRIBUTION_UNKNOWN` assertion is what makes the guard real.

**F-15 — Real end-to-end run already surfaces an `ATTRIBUTION_UNKNOWN`.** Running
`python runtime/verify.py diagnose-failures` against the existing
`runtime/generated/evidence` directory (left by earlier M3/M4 runs) produced a live
`Unattributed (insufficient evidence): lint: failure has no resolvable file path`
entry. That is M6 req 5 working on real artifacts without any manual log parsing — the
command is not theoretical.

### Blockers

None.

### Decision

M6 accepted. Attribution runs on artifacts alone, `unit_id` is the only join key, the
E-4 functions and verdict semantics are untouched, and the negative/no-evidence and
unjoinable cases are explicitly reported rather than guessed.

### Next milestone

M7 — Re-run the Phase 1.5 specimen end-to-end and certify.

---

## M7 — Re-run the Phase 1.5 Specimen End-to-End

**Status:** DONE
**Started:** 2026-08-11
**Completed:** 2026-08-11

### Objective

Prove the durable data path on the same real specimen with no manual steps, and write
the certification. No application changes, no artificial greening, no workflow edits.

### Commands executed

```bash
python3 runtime/verify.py diagnose-failures        # real evidence, zero manual parsing
bash .github/scripts/run_backend_verification.sh   # backend green gate (exit 0)
npx eslint . --ext .ts,.tsx --quiet                # lint gate (frontend)
python3 -m pytest runtime/tests/test_diagnose_failures.py runtime/tests/test_failure_attribution.py runtime/tests/test_cross_layer_planner.py -q
find runtime/generated/evidence -type f            # artifact inventory
python3 -m ruff check runtime/                      # changed-file lint
```

### Files changed

```
docs/verification/VEA2_PHASE2_CERTIFICATION.md   (new — the certification)
docs/progress.md                                 (this entry)
```

No source files changed in M7. The milestone is documentation + verification only, as
the plan requires (Prohibited: application changes; any fix that makes the specimen green
artificially; `.github/workflows/` edits).

### Evidence (paths / measurements)

- **Identity spine live.** `runtime/generated/evidence/run-manifest.json`
  (`run-manifest/v1`): 3 steps, unit_ids `['UNMAPPED','backend-unit','runtime-self-test']`,
  1 surfaced `UNMAPPED` entry (`run_fast_checks.sh`). Real proof the spine carries
  `unit_id` plan→step→result→evidence.
- **Backend green.** `run_backend_verification.sh` → exit 0; all four parallel suites
  (`unit-engines`, `contracts`, `properties`, `invariants`) `pass`. Reproduces the M4
  result; no backend application code changed since.
- **Frontend lint gate = 34** (corrected M0 baseline), composition unchanged:
  `set-state-in-effect`15 `exhaustive-deps`8 `react/no-children-prop`3 `static-components`2
  `purity`2 `immutability`2 `no-sync-scripts`1 `no-assign-module-variable`1. A change in
  this count would signal scope leak; it is unchanged. (M0 corrected the spec's "31" to
  the proven 34 — see F-12/M0.)
- **Attribution reproduced automatically.** `verify.py diagnose-failures` on real
  evidence produced the §18 CROSS-LAYER diagnostic with `in-blast-radius=0`,
  `outside=0`, `unknown=1`, `change_is_implicated=False`. Zero manual log parsing.
- **Specimen verdict identical to Phase 1.5.** `test_diagnose_failures.py::
  test_adapter_reproduces_phase1_5_verdict_from_artifacts_alone` feeds the exact 6
  specimen frontend failure paths (loan-engine change at `b9074020`) through the artifact
  adapter and asserts `in_blast_radius=0` / `change_is_implicated=False` — identical to
  the Phase 1.5 manual result.
- **Phase 1.5 suite unmodified.** `test_failure_attribution.py` + `test_cross_layer_planner.py`
  = 25 passed, unchanged. Verdict semantics untouched.
- **Manual-step count:** Phase 1.5 ≈ 15 forensic → Phase 2 = **0** (one command).

### Test coverage

The M6 suite (8 tests) plus the unmodified Phase 1.5 suite (25) are the acceptance
evidence. Mutation probes for M5 (Mutant B) and M6 (join-always-matches) both killed and
reverted.

### Blockers

None.

### Decision

M7 accepted. Phase 2 is complete: the identity spine carries `unit_id` plan→execution→
evidence, failures join to units and provenance by workflow (never by string match),
attribution runs on real artifacts with zero manual parsing, and the Phase 1.5 verdict
is reproduced identically. Full certification: `docs/verification/VEA2_PHASE2_CERTIFICATION.md`.

### Next milestone

None — VEA-2 Phase 2 is complete. Phase 3 (graph-based diagnosis / E-4 replacement) and
the deferred Group E CI topology audit are the documented handoffs.
