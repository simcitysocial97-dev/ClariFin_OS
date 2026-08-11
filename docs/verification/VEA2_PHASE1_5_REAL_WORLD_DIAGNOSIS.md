# VEA-2 Phase 1.5 — Real-World Cross-Layer Failure Forensic Diagnosis

**Status:** COMPLETE
**Date:** 2026-08-11
**Specimen:** HEAD `b9074020` — `fix(loan-engine): make amortization schedules exact and self-consistent`
**Branch:** `recovery/program-r-forensic-reconstruction`
**Execution ledger:** `docs/progress.md`

---

## Executive Summary

The premise under investigation was that a backend change had broken the frontend, and that
prior AI agents had entered a TypeScript/build fix loop trying to repair it.

Forensic analysis establishes something different, and more useful:

1. **There were zero TypeScript errors.** `tsc --noEmit` exited 0 both before and after.
   The prior agent loop was chasing a signal the compiler never emitted.
2. **The backend change was innocent.** Zero frontend files and zero contract surfaces
   changed. Every failing file was byte-identical to a commit five commits earlier, and the
   failures were reproduced there in an isolated worktree.
3. **The verification framework did its job — up to a point.** It correctly mapped
   change → capability → impact → verification selection, and correctly chose to run
   frontend verification. It was then **blind at attribution**: it reported "frontend
   verification failed" without being able to say that the failure had nothing to do with
   the change.
4. **55 raw diagnostics compressed to 3 root causes plus 1 flaky test.**
5. **The frontend production build was broken and nobody knew**, because
   `run_frontend_verification.sh` never ran `npm run build`.

The framework gap — not the frontend code — is the substantive finding. It has been closed
and regression-tested.

### Final state

| Layer | Before | After |
|-------|--------|-------|
| Frontend typecheck | PASS | PASS |
| Frontend build | **FAIL (10 errors)** | **PASS** |
| Frontend test | FAIL (1 flaky) | **PASS — 1237/1237** |
| Frontend lint | FAIL (44) | FAIL (31 pre-existing, out of scope) |
| Backend | PASS | **PASS** |
| Runtime framework | PASS (281) | **PASS (291)** |

---

## A. Baseline

```
HEAD     b9074020aef5a3e4c8313cc313a80a10fd623bbb
Branch   recovery/program-r-forensic-reconstruction
Python   3.12.3    pytest 9.0.2
Node     v20.20.2  npm 10.8.2
frontend/node_modules  PRESENT (installed 2026-08-10)
```

VEA-2 Phase 1 recorded "frontend dev environment not available locally". That limitation no
longer held, which is precisely why this failure became observable for the first time.

| Layer | Command | Exit | Result |
|-------|---------|------|--------|
| Backend | `run_backend_verification.sh` | 0 | GREEN — 26 contract + 206 property + 468 unit/invariant (77s) |
| Runtime | `pytest runtime/tests` | 0 | GREEN — 281 passed (30.6s) |
| Frontend | `run_frontend_verification.sh` | 1 | RED — reproducible |

No source was modified during baseline collection.

---

## B. Failure Inventory

Phase-separated, because the existing script collapsed all phases into one exit code.

| Phase | Exit | Duration | Signal |
|-------|------|----------|--------|
| typecheck (`tsc --noEmit`) | **0** | 22.1s | **zero TypeScript errors** |
| lint (`eslint`) | 1 | 79.8s | 44 errors |
| test (`vitest run`) | 1 | 198.8s | 1 failed / 1236 passed |
| build (`next build`) | 1 | 40.1s | 10 errors — **not part of the verification script at all** |
| environment | n/a | n/a | no environment failure |

---

## C. Failure Clusters

| # | Cluster | Phase | Count | Class |
|---|---------|-------|-------|-------|
| **C-A** | Missing `"use client"` on hook-bearing `lib/runtime/` modules reachable from `app/layout.tsx` | build | 10 diagnostics → **5 modules → 1 root cause** | ROOT_CLUSTER |
| **C-B** | Ref read during render, `use-workspace-registration.ts:52` | lint | 1 | ROOT_CLUSTER |
| **C-C** | Vendored `public/pdf.worker.mjs` linted as first-party source | lint | 43 → **1 config root cause** | ROOT_CLUSTER |
| **C-D** | Wall-clock perf assertion `288.5ms < 250ms` | test | 1 | ENVIRONMENT_FAILURE |

`UNCLASSIFIED`: **0**.

```
55 raw diagnostics → 4 clusters → 3 root causes + 1 flaky test → 0 caused by the backend
```

### Pre-existence proven, not asserted

```bash
git worktree add /tmp/kilo/vea15-baseline bacc1fe2 --detach
cp -r frontend/node_modules /tmp/kilo/vea15-baseline/frontend/node_modules
cd /tmp/kilo/vea15-baseline/frontend
npx next build       # exit 1 — identical 10 errors, same files, same line:col
npx eslint . --quiet # exit 1 — identical 44 errors
npx tsc --noEmit     # exit 0
```

A symlinked `node_modules` produced a misleading `TurbopackInternalError`; a real copy was
used instead. Recorded so the experiment reproduces and the spurious error is not mistaken
for a finding.

---

## D. Change Correlation

```bash
git diff bacc1fe2 HEAD --name-only | grep '^frontend/'                          # 0 files
git diff bacc1fe2 HEAD --name-only | grep -E 'dto|mapper|router|schema|openapi' # none
git log -1 --format='%h %ad' -- frontend/    # bacc1fe2, 5 commits before HEAD
```

Every failing frontend file is byte-identical to `bacc1fe2`. Per-cluster chain walk
(frontend → backend) found no API/DTO/mapper/generated-type edge for any cluster.

**No causal chain exists between the backend change and any frontend failure.**

---

## E. Capability Correlation

`engine:loan_engine` → `capability:useLoansCapability`
(`frontend/lib/capabilities/use-loans-capability.ts`), plus `useCreditCardsCapability` and
`useBehaviourCapability` reached through shared router/endpoint hops.

---

## F. Blast Radius Comparison

**Predicted frontend entities (7):**
`use-loans-capability.ts`, `loans-mapper.ts`, `loans-view-model.ts` (`AmortizationEntryViewModel`),
`credit-cards-mapper.ts`, `credit-cards-view-model.ts` (`StatementHistoryViewModel`),
`use-credit-cards-capability.ts`, `use-behaviour-capability.ts`

**Actually failing files (7):**
`lib/runtime/{navigation,selection,timeline,workspace}-runtime.ts`,
`lib/runtime/use-workspace-registration.ts`, `public/pdf.worker.mjs`,
`components/toolbar/__tests__/workspace-toolbar-performance.test.tsx`

**Intersection: empty.**

| Cluster | Classification |
|---------|----------------|
| C-A, C-B, C-C, C-D | **UNRELATED** |

No cluster is causally related, so no PREDICTED-CORRECT / UNDER-PREDICTED verdict applies.
The framework was **not** under-predicting: the contract surfaces it predicted are green.

**Mild over-prediction observed** — credit-card entities entered via a shared
`GET /report` / `credit_card_engine` hop. Recorded, deliberately **not** optimized: it costs
extra verification (safe direction), and §21 requires correctness before optimization.

---

## G. Verification Plan

| Unit | Selected | source | Justification |
|------|----------|--------|---------------|
| `unit-targeted` | yes | ownership | 17 provider-recorded tests verify an impacted engine |
| `contracts-schemathesis` | yes | chain-map+blast-radius | 35 endpoints in radius |
| `backend-integration` | yes | chain-map+blast-radius | 11 router/service/repository |
| `backend-unit` | yes | chain-map+blast-radius | 27 backend entities |
| `frontend-unit` | yes | chain-map+blast-radius | 7 frontend entities |
| `frontend-typecheck-build` | yes | chain-map+blast-radius | contract type compatibility |
| `playwright-e2e` | skipped | — | no workspace impacted |
| `runtime-self-test` | skipped | — | runtime unchanged |
| `mutation-run` | skipped | — | explicit request required (>=600s) |
| `golden-regression` | skipped | — | explicit request required (>=600s) |

6 of 10 selected. No unexplained unit, no silently omitted unit, no "run everything"
escalation. Selecting frontend verification was **correct**.

---

## H. Provenance

C11 provenance holds on the real specimen, not just synthetic tests: every selected unit
carries `capabilities`, `impact_kinds` and `source`.

**Critical observation:** the framework selected the right units for the right reasons, then
returned red for content unrelated to its own prediction — and nothing in the pipeline
detected that mismatch.

---

## I. Evidence

```
runtime/generated/evidence/vea2-phase1_5/   raw per-phase capture (baseline + reruns)
runtime/generated/evidence/frontend/        frontend-verification.json + per-phase logs
```

---

## J. Classification

| Cluster | Category | Evidence |
|---------|----------|----------|
| C-A | `FRONTEND_IMPLEMENTATION` + `PRE_EXISTING` | Turbopack "This React Hook only works in a Client Component"; identical at `bacc1fe2` |
| C-B | `FRONTEND_IMPLEMENTATION` + `PRE_EXISTING` | `react-hooks/refs` at `:52:10` |
| C-C | `FRONTEND_TOOLCHAIN` + `PRE_EXISTING` | 43/44 errors in a vendored pdfjs bundle |
| C-D | `ENVIRONMENT` | passes in isolation (3/3 at HEAD, 1/1 at baseline), fails under suite load |
| cross-cutting | `VERIFICATION_FRAMEWORK` | framework cannot express out-of-radius failure |

Disproven by evidence: `BACKEND_FRONTEND_CONTRACT_DRIFT`, `BACKEND_FRONTEND_TYPE_DRIFT`,
`DTO_GENERATED_TYPE_DRIFT`, `MAPPER_DRIFT`, `VIEW_MODEL_DRIFT`,
`API_ROUTER_CONTRACT_DRIFT`, `STALE_GENERATED_ARTIFACT` — no contract surface changed and
`tsc` exits 0.

No new taxonomy categories were required.

---

## K. Framework Gaps

| ID | Gap |
|----|-----|
| **FW-1** | No blast-radius/failure correlation — cannot say whether a failure lies inside the radius that selected the unit |
| **FW-2** | No phase decomposition — eslint+tsc+vitest collapsed into one exit code, hiding "TypeScript is clean" |
| **FW-3** | `npm run build` in the optimizer's unit but absent from the executed script — the most severe defect was invisible |
| **FW-4** | No pre-existing-failure baseline — cannot distinguish "I broke it" from "already broken" |
| **E-1** | `EvidenceAggregator` expects JUnit XML; no script emits `--junitxml` (VEA-1 finding confirmed) |
| **E-2** | `EvidenceSummary` is backend-only — frontend failure is structurally unrepresentable |
| **E-3** | Evidence keyed by artifact type, never by `VerificationUnit.id`; C11 provenance discarded |
| **E-4** | `_find_chain_for_failure()` returns the *first* chain-map entry regardless of the failure |

---

## L. Application Defects

| ID | Defect | Class |
|----|--------|-------|
| APP-1 | 5 `lib/runtime/` modules missing `"use client"` — **production build broken** | FRONTEND_IMPLEMENTATION |
| APP-2 | Ref read during render | FRONTEND_IMPLEMENTATION |
| APP-3 | `eslint.config.mjs` lints vendored/generated output | FRONTEND_TOOLCHAIN |
| APP-4 | Load-sensitive perf assertion | ENVIRONMENT |
| APP-5 | Module-level `window` access during prerender (2 files) | *found during remediation, masked by APP-1* |
| APP-6 | `useSearchParams()` without Suspense | *found during remediation, masked by APP-5* |

---

## M. Remediation

Only after classification.

| Fix | Target | Result |
|-----|--------|--------|
| 1 | `'use client'` on exactly the 5 diagnosed modules | 10 build errors → 0, compiles |
| 2 | `typeof window !== 'undefined'` guard on 2 module-level init sites | ReferenceError cleared |
| 3 | `<Suspense fallback={null}>` around `<DeepLinkSync />` | **build exit 0**, 17/17 pages |
| 4 | `eslint.config.mjs` ignore `public/**` + `dist/**` | 44 → 35 errors, 43-cascade gone |
| 5 | `useRef` → `useMemo` for the render-read value | file lints clean |

APP-5 and APP-6 were located by reading the emitted chunk at the exact byte offset from the
stack trace and grepping the unique symbol back to source — the same forensic discipline,
not guesswork. Both were masked by the preceding error, which is why staged verification
after each fix mattered.

**Backend unchanged**, per §0.13.

### 31 residual lint errors deliberately NOT fixed

`react-hooks/set-state-in-effect` (15), `exhaustive-deps` (8), `static-components` (2),
`purity` (2), `immutability` (2), `@next/next` (2).

Every affected file is byte-identical to `bacc1fe2`; none belongs to C-A…C-D; all are
`in-blast-radius=0`. §17 forbids repairing unrelated errors. No suppression, downgrade,
threshold change or exclusion was used to hide them — only vendored and generated output was
excluded from linting, which is a correctness fix, not a weakening. Every file modified in
this phase lints clean.

---

## N. Regression Protection

`runtime/tests/test_failure_attribution.py` — 10 tests.

| Defect | Test |
|--------|------|
| FW-1 | `test_real_frontend_failures_are_attributed_outside_blast_radius` |
| FW-1 inverse | `test_failure_inside_blast_radius_implicates_the_change` |
| FW-4 / E-3 | `test_attribution_carries_unit_provenance` |
| FW-4 | `test_pre_existing_failure_is_distinguished_from_merely_unrelated` |
| E-4 | `test_unresolvable_failure_is_unknown_never_silently_unrelated` |
| cascade | `test_clusters_compress_cascades` |
| determinism | `test_attribution_is_deterministic` |
| path forms | `test_path_normalisation_does_not_create_false_negatives` |
| Phase-1 guard | `test_loan_engine_change_still_selects_frontend_verification` |
| loop prevention | `test_diagnostic_output_names_excluded_areas` |

**Mutation-verified.** Injecting `matched = _match(...) or 'MUTANT'` (always blame the
change) → **4 failed, 6 passed**; mutant killed, then reverted.

No existing test was modified, skipped or weakened. Suite: 281 → 291 passed.

---

## O. Final Diagnostic

The same real failure, re-run through the improved pipeline:

```
CROSS-LAYER FAILURE

Change:       backend/src/engines/loan_engine/amortization.py
              backend/src/engines/loan_engine/floating_rate.py

Capability:   capability:useLoansCapability
              capability:useCreditCardsCapability
              capability:useBehaviourCapability

Impact:       34 predicted downstream files, incl.
              frontend/lib/mappers/loans-mapper.ts
              frontend/types/loans-view-model.ts
              frontend/lib/capabilities/use-loans-capability.ts

Verification: unit-targeted, contracts-schemathesis, backend-integration,
              backend-unit, frontend-unit, frontend-typecheck-build
              (each with source= and impact_kinds= provenance)

Failure attribution:
  observed=59  in-blast-radius=0  outside=59  unknown=0

NO FAILURE IS ATTRIBUTABLE TO THIS CHANGE.
  Every observed failure lies outside the blast radius that justified running these units.
  Do NOT modify the changed files to make this verification green.

Unrelated / pre-existing (excluded from this change):
  build: 5 diagnostics across 5 file(s)
  lint:  54 diagnostics across 20 file(s)
```

Phase decomposition, previously impossible:

```
overall: fail                       →  after remediation:
  lint       fail  exit=1              lint       fail  exit=1  (31 pre-existing)
  typecheck  pass  exit=0              typecheck  pass  exit=0
  build      fail  exit=1              build      pass  exit=0
  test       pass  exit=0              test       pass  exit=0
```

Post-remediation attribution correctly self-classifies the remainder:

```
{"observed": 23, "in_blast_radius": 0, "outside_blast_radius": 23, "unknown": 0}
change_is_implicated: False
clusters: {'PRE_EXISTING:lint': 23}
```

**The conclusion that required ~15 manual forensic steps in M3–M9 is now produced
automatically.**

---

## Completion Gate (§24)

| Requirement | Status |
|-------------|--------|
| Real failure reproduced; raw evidence captured | ✅ |
| Failures clustered; dependency traced; capability identified; changes correlated | ✅ |
| Predicted vs actual blast radius compared; units confirmed | ✅ |
| Root vs cascade distinguished; classifications assigned; framework vs application separated | ✅ |
| Evidence correlated to units; provenance preserved; output actionable | ✅ |
| Framework gaps have regression tests; no test weakened | ✅ |
| Fixes only after diagnosis; no TypeScript repair loop; backend stable | ✅ |
| Original failure re-run; frontend build/test/typecheck green; backend green; framework green | ✅ |
| Local verification executable; CI path preserved (exit-code contract unchanged) | ✅ |
| Heavy verification (mutation, golden) still separated | ✅ |

### §25 Final success condition

> Did the verification system make it materially easier for an AI agent to understand why
> the frontend failed, what caused it, what must be inspected, and what must not be touched?

**Yes, demonstrably.** Before: a single red exit code implying the backend change broke the
frontend, with a hidden clean typechecker and an unrun build. After: per-phase status, an
explicit `change_is_implicated: False`, `in-blast-radius=0`, cascade clustering, a named
inspection order, and an explicit instruction not to modify the changed files.

---

## Handoff to VEA-2 Phase 2

Deliberately **not** done here (§15, §26):

| Item | Gap | Rationale |
|------|-----|-----------|
| `--junitxml` on all test commands | E-1 | Would not have answered any question in this diagnosis |
| Frontend section in `EvidenceSummary` | E-2 | Same |
| Key evidence by `VerificationUnit.id` | E-3 | Natural Phase 2 work, needs the evidence model first |
| Replace `_find_chain_for_failure()` keyword matching with graph traversal | E-4 | Attribution module now supersedes it for the frontend path |
| Narrow the credit-card over-prediction hop | §F | Correctness first; §21 defers optimization |
| 31 pre-existing React-hooks lint errors | APP | Separate workstream, needs its own diagnosis |
| `verification.yaml` module-path sync | GAP-003 | Carried over from Phase 1 |
