# VEA-5 M7 — CI Topology, Trigger & Ownership Audit

**Status:** DONE — 2026-08-12
**Type:** Read-only audit. **No workflow modified.** Deliverable is an evidence-backed topology matrix from which M8 can safely decide what needs changing.
**Scope:** All 9 existing workflows + the M5 `verification-reconcile` workflow, measured against the VEA-5 three-tier model (M1), the plan/reconciliation gate (M4/M5) and the evidence contract (M6).
**Verdict:** AUDIT COMPLETE — evidence matrix produced; no consolidation recommended without M8 ownership decision.

---

## M7 rule (binding)

> No workflow deletion/consolidation based merely on apparent duplication.
> Produce an evidence matrix first. The output must answer:
> **"If we removed this workflow, which verification responsibility would become uncovered?"**

This audit honors that rule. It establishes the matrix, maps each workflow to the
three-tier model and the M5/M6 contracts, and computes the "uncovered responsibility"
for each workflow. It does **not** recommend removal.

## Method

For each workflow the following were extracted from the YAML and from the
`verify.py <profile>` → script delegation chain:

- trigger (push / PR / schedule / manual / release)
- branch + path filters
- profile invoked (`verify.py <profile>`)
- verification units (from the catalog / scripts)
- execution cost (timeout)
- evidence generated (artifacts)
- overlap with other workflows
- tier归属 (LOCAL / PR / DEEP)
- independent? redundant? mis-triggered? stale vs recovery branch?
- should failure block merge?

Staleness was measured concretely with `git diff --stat origin/main` on each
workflow file.

---

## Evidence matrix

| # | Workflow | Trigger | Path filters | Profile | Tier | Timeout | Evidence | Stale vs origin/main |
|---|----------|---------|--------------|---------|------|---------|----------|----------------------|
| 1 | backend-verify | push+PR | backend/**, runtime/** | `verify.py backend` | PR | 30m | backend-report, backend-evidence, shared maps | 0 lines (matches main) |
| 2 | frontend-verify | push+PR | frontend/**, backend routers/mappers, runtime/** | `verify.py frontend` | PR | 25m | frontend-report, frontend-evidence, shared maps | 0 lines (matches main) |
| 3 | quality | push+PR | (all) | `verify.py quick` | PR | 10m | quality-report, fast-checks-evidence, shared maps | **263 lines diverge** |
| 4 | verification-runtime | push+PR | runtime/**, backend engines/routers/mappers | `verify.py runtime` | PR | 30m | runtime-quality, perf, shared maps | 0 lines (matches main) |
| 5 | golden | schedule(nightly)+manual | (none) | `verify.py golden` | DEEP | 30m | golden-report(90d), golden-evidence | **127 lines diverge** |
| 6 | mutation | schedule(nightly)+manual | (none) | `verify.py mutation` | DEEP | 90m | mutation-report, shared maps | **216 lines diverge** |
| 7 | dependency-update | schedule(weekly)+manual | (none) | `run_dependency_checks.sh` | OPS | 15m | python/npm dependency reports | 0 lines (matches main) |
| 8 | playwright | push+PR (main/master/develop) | frontend/**, e2e/**, runtime/** | `verify.py playwright` | PR/UI | 60m | playwright-report, playwright-evidence | **162 lines diverge** |
| 9 | release | release published + manual | (none) | build (npm ci + next build) | RELEASE | 30m | frontend-dist(90d) | 0 lines (matches main) |
| 10 | verification-reconcile (M5) | push+PR | runtime/**, backend engines/routers/mappers | `verify.py plan/exec-evidence/reconcile` | PR gate | 30m | reconciliation-report | new (M5) |

### Shared-artifact observation (overlap)
Workflows 1–6 and 10 each re-upload the **same four shared artifacts** on every
run: `cross-layer-map`, `knowledge-index`, `verification-cache`,
`engineering-history` (14-day retention). This is systematic duplication of
*artifact publishing*, not of *verification responsibility* — the audit separates
the two (see Redundancy classification below).

---

## Per-workflow finding

### 1. backend-verify — PR, backend functional owner
- **Responsibility:** complete backend suite (unit + integration + property + contract) via `run_backend_verification.sh`.
- **Overlap:** shares the 4 shared artifacts with 2/3/4/5/6/10. No verification-unit overlap with frontend-verify.
- **Tier:** PR (change-scoped on backend/**).
- **Stale:** matches origin/main — current.
- **Merge block:** should block merge (primary backend gate).
- **If removed:** backend unit/integration/property/contract verification would be uncovered for push/PR. **Not redundant.**

### 2. frontend-verify — PR, frontend functional owner
- **Responsibility:** frontend lint/typecheck/build/test phases via `run_frontend_verification.sh`.
- **Overlap:** shared artifacts only; distinct unit set from backend-verify.
- **Tier:** PR.
- **Stale:** matches origin/main — current.
- **Merge block:** should block merge (primary frontend gate).
- **If removed:** frontend verification uncovered for push/PR. **Not redundant.**

### 3. quality — PR, fast cross-cutting gate
- **Responsibility:** `verify.py quick` — lint, format, typecheck, unit, architecture, meta (fast signal).
- **Overlap:** this is the **most likely apparent-duplication candidate** — it runs a subset of checks that backend-verify/frontend-verify also cover (lint/typecheck/unit). BUT it is the *fast* gate (10m) intended to fail fast before the heavier suites; backend-verify/frontend-verify do not include architecture/meta and are slower.
- **Tier:** PR.
- **Stale:** **263 lines diverge from origin/main** — the largest divergence. Highest-priority staleness review for M8.
- **Merge block:** currently the only workflow explicitly documented as "BLOCKS: Merging if it fails."
- **If removed:** fast fail-fast lint/format/architecture gate lost; slower suites would be the first signal. **Apparent overlap, not true redundancy — keep until M8 decides.** This is exactly the M7 rule: do not remove on apparent duplication.

### 4. verification-runtime — PR, runtime-framework owner
- **Responsibility:** `verify.py runtime` — the Engineering Runtime self-test + integrity.
- **Overlap:** shared artifacts only.
- **Tier:** PR (runtime/**).
- **Stale:** matches origin/main — current.
- **Merge block:** should block merge (protects the verification control plane itself).
- **If removed:** the runtime/framework that powers every other profile loses its own gate. **Not redundant — it gates the verifier.**

### 5. golden — DEEP, golden-regression owner
- **Responsibility:** `verify.py golden` — golden dataset regression (nightly).
- **Overlap:** none on verification responsibility (no other workflow runs golden).
- **Tier:** **DEEP** (schedule/manual only — correctly excluded from PR).
- **Stale:** **127 lines diverge from origin/main.**
- **Merge block:** should NOT block PR (it is scheduled); feeds M10 certification.
- **If removed:** golden dataset regression becomes uncovered entirely. **Unique ownership — not redundant.**

### 6. mutation — DEEP, mutation/测试有效性 owner
- **Responsibility:** `verify.py mutation` — mutation testing + survivor reporting.
- **Overlap:** none (mutation is uniquely owned here; M6 places it in DEEP test-effectiveness).
- **Tier:** **DEEP** (nightly, 90m — correctly excluded from PR).
- **Stale:** **216 lines diverge from origin/main.**
- **Merge block:** should NOT block PR (DEEP); feeds Track B4 effectiveness map.
- **If removed:** mutation effectiveness measurement becomes uncovered. **Unique ownership — not redundant.**

### 7. dependency-update — OPS, maintenance owner
- **Responsibility:** `run_dependency_checks.sh` — dependency/security health (weekly).
- **Overlap:** none with verification profiles. Distinct responsibility (supply-chain health).
- **Tier:** operational (neither PR nor DEEP verification; feeds M9 security evidence).
- **Stale:** matches origin/main — current.
- **Merge block:** informational; should not block merge (monitoring).
- **If removed:** dependency drift/security monitoring becomes uncovered. **Independent — not redundant.**

### 8. playwright — PR/UI, E2E owner
- **Responsibility:** `verify.py playwright` — end-to-end browser tests (E2E/UI).
- **Overlap:** shared artifacts only; distinct from functional suites.
- **Tier:** PR (UI integration) and feeds DEEP UI surface (M6-B).
- **Stale:** **162 lines diverge from origin/main.**
- **Merge block:** should block merge for frontend/E2E change paths.
- **If removed:** E2E/UI verification uncovered. **Unique ownership — not redundant.**

### 9. release — RELEASE, certification owner
- **Responsibility:** build frontend distribution + package release artifacts (NOT a verification profile).
- **Overlap:** none.
- **Tier:** release event.
- **Stale:** matches origin/main — current.
- **Merge block:** runs on `release published`, not on PR; its success is the release gate.
- **If removed:** release artifact build/publish becomes uncovered. **Independent — not redundant.**

### 10. verification-reconcile (M5) — PR gate, reconciliation owner
- **Responsibility:** `verify.py plan --tier pr` → `exec-evidence` (M6 v2) → `reconcile`. Implements the M5-A..E hard gates.
- **Overlap:** consumes the PR plan; does not re-run verification (delegates `verify.py runtime` for the profile step). Shares the 4 shared artifacts.
- **Tier:** PR gate.
- **Stale:** new in M5 — current by construction.
- **Merge block:** should become a required PR check (M8).
- **If removed:** the plan/reconcile gate (environment-vs-planning divergence) is lost. **Unique ownership — not redundant.**

---

## Redundancy classification (M7 critical output)

| Workflow | Apparent duplication | True redundancy? | Basis |
|----------|---------------------|-----------------|-------|
| quality | overlaps lint/typecheck/unit in backend/frontend-verify | **NO** (fast fail-fast gate; adds architecture/meta; 10m vs 25–30m) | M7 rule: apparent ≠ true. Keep pending M8. |
| shared-artifact re-upload (×7) | same 4 artifacts re-published every run | **YES (cosmetic)** — but it is artifact-publishing duplication, not verification-responsibility duplication. Candidate for a shared publish step, not workflow deletion. |
| golden / mutation / playwright | none on responsibility | **NO** — unique DEEP/UI ownership. |
| dependency-update / release | none | **NO** — independent operational/release responsibility. |
| verification-runtime | none | **NO** — gates the verifier itself. |

**Conclusion:** No workflow is truly redundant on verification responsibility. The
only genuine duplication is *shared-artifact re-publishing* (cosmetic, fixable by a
shared composite publish action without touching verification ownership). The
quality-vs-functional overlap is apparent only and must not trigger consolidation
without the M8 ownership decision.

---

## Three-tier mapping (acceptance criterion)

| Tier | Goal | Owning workflows (current) | VEA-5 contract |
|------|------|----------------------------|----------------|
| **LOCAL** (T1) | seconds/minutes; working-tree delta; no origin/main contamination | (developer machine) — none of the 9 run locally | M2 planner; not yet a CI artifact |
| **PR** (T2) | merge confidence; deterministic plan; explained exclusions; evidence v2; reconciliation | backend-verify, frontend-verify, quality, verification-runtime, playwright, verification-reconcile | M4 reconcile + M5 gate + M6 v2 evidence |
| **DEEP** (T3) | system health; expensive, scheduled/manual | golden, mutation (+ dependency-update feeds security; playwright also feeds DEEP UI) | M6-B Deep contract (13 surfaces) |

Observation: the 9 workflows already **implicitly** implement LOCAL/PR/DEEP
separation (PR = push/PR-triggered; DEEP = scheduled golden/mutation). M7 makes
this explicit and anchors it to the M6 contract. The gap is **LOCAL**: no CI
artifact represents the developer's working-tree scope yet — that is a Track A/M8
concern (the PR planner can emit a LOCAL plan for comparison, but no workflow runs
it pre-push).

---

## Track B / Track C ownership map (acceptance criterion)

| Track | Capability | Current owning workflow / surface | M6 contract surface |
|-------|-----------|-----------------------------------|---------------------|
| **B1 Coverage** | line/branch/critical-path coverage | backend-verify / frontend-verify (implicit via pytest-cov) | deep-coverage-analysis |
| **B2 Property/Contract** | property + contract + invariant tests | backend-verify (`run_backend_verification.sh`) | deep-backend-suite |
| **B3 Auto-gen** | candidate test generation + mutation effectiveness | (none yet) | — (future) |
| **B4 Mutation** | mutation score + survivors | mutation (DEEP) | deep-mutation-testing |
| **B5 Golden** | golden dataset regression | golden (DEEP) | deep-golden-regression |
| **B6 Large dataset** | scale/correctness/degradation | (none yet) | deep-large-dataset-regression |
| **C1 Real usage** | user-action causal path | (none yet — Track C start) | — (future) |
| **C2 Playwright/E2E** | navigation/flows/critical financial workflows | playwright | deep-playwright-e2e |
| **C3 UI/UX** | hierarchy/latency/a11y/empty states | (none yet) | deep-visual-ux-regression |

This map shows exactly where Track B/C evidence is **already produced** (B2/B4/B5/C2
via existing workflows) versus where it is **absent and must be built** (B1
explicit signal, B3, B6, C1, C3). M7 thereby scopes Tracks B/C without guessing.

---

## Staleness findings (actionable for M8)

Workflows diverging from `origin/main` (recovery branch only):

| Workflow | Divergence | Implication |
|----------|-----------|-------------|
| quality | 263 lines | highest — review before treating as authoritative gate |
| mutation | 216 lines | DEEP logic may differ from main; reconcile before M10 |
| playwright | 162 lines | E2E command/path differences vs main |
| golden | 127 lines | golden command differences vs main |

`backend-verify`, `frontend-verify`, `dependency-update`, `release`,
`verification-runtime` match `origin/main` exactly — current.

These divergences are the same four flagged in M0 forensics (golden/mutation/
playwright/quality). M7 confirms they are **branch-only evolutions** not yet
merged to `main`. M8 must decide whether to converge them to `main` (recommended)
before any topology change, so the audit compares like-for-like.

---

## M8 decision inputs (what M7 hands off)

1. **No verification responsibility is uncovered by any single removal** — the
   matrix answers "if removed, what becomes uncovered?" with a unique owner for
   every responsibility. → Consolidation is **not** evidence-justified today.
2. **Only cosmetic duplication** (shared-artifact re-publish) is real; fixable by a
   shared publish composite, not by deleting workflows.
3. **quality overlap is apparent, not true** — do not consolidate on that basis.
4. **Staleness** is concentrated in 4 workflows (quality/mutation/playwright/golden)
   vs origin/main — converge before topology decisions.
5. **LOCAL tier has no CI artifact** — a gap for M8 to close (pre-push LOCAL plan
   comparison or a developer-required check).
6. **M5 `verification-reconcile` should become a required PR check** (M8) — it is
   currently additive, not enforced.

---

## Deliverable status

- [x] All 9 + M5 workflows audited against the three-tier model.
- [x] Trigger / filters / profile / units / cost / evidence / overlap / tier /
      staleness / merge-block established for each.
- [x] "If removed, what becomes uncovered?" answered per workflow.
- [x] Redundancy classified per the M7 rule (no deletion recommended).
- [x] Three-tier mapping + M5/M6 contract linkage.
- [x] Track B/C ownership map produced.
- [x] Staleness evidence (git diff vs origin/main) included.
- [x] **No workflow modified.**

**M7 VERDICT: AUDIT COMPLETE — evidence matrix produced; no consolidation without M8 ownership decision.**
