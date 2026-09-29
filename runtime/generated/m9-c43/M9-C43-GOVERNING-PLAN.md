# M9-C43 GOVERNING PLAN — Verification Quality Convergence & Final Certification

**Status:** AUTHORITATIVE SOURCE OF TRUTH for M9-C43 execution
**Branch:** `m9c9-merge-authorization-resolution`
**Base SHA:** `f632e28f7a92a66799fda2c4c23323ca73a38858` (C42.38 frozen SHA)
**Started:** 2026-08-27T04:23+05:30
**Predecessor:** M9-C42.38 `FINAL_VERIFICATION_SYSTEM_CERTIFIED` (14/14 components, 60.297% reconciled mutation, 27/27 DoD)

---

## 1. Mission

Use the CERTIFIED C42 verification system (no redesign) to converge the application
repository itself to final verification quality:

| Target | Threshold | Evidence class required |
|---|---|---|
| All required workflows GREEN | local execution or explicit ENVIRONMENTAL_LIMITATION | measured |
| Authoritative repository coverage | ≥ 80% | AUTHORITATIVE_MEASURED |
| Authoritative mutation score | ≥ 80% | AUTHORITATIVE_MEASURED (final campaign) |
| Automatic test generation | operational, evidence-driven, human-authorized | measured |
| Evidence-driven strengthening | executed against justified gaps | measured |
| Final certification | reproducible from artifacts | derived from artifacts only |

## 2. Governing loop

Measure → Diagnose → Generate → Strengthen → Targeted Revalidate → Freeze →
Authoritatively Remeasure → Correlate → Certify

## 3. Non-negotiable constraints (binding for C43)

1. C42 architecture is not redesigned/replaced/duplicated.
2. No deletion of orphaned/dead capability code.
3. No feature removal because it is hard to test.
4. No silent scope broadening; no gate weakening.
5. No fabricated CI evidence; simulated CI ≠ live CI.
6. Reconciled C42 mutation evidence (60.297%) is never claimed as a fresh campaign.
7. No repeated full mutation campaigns; targeted mutation for per-component changes.
   Full campaign ONLY at the final measurement checkpoint (43.9) — formally justified there.
8. No metric-only tests; no autonomous production-code modification; generated tests
   require human authorization; generated tests must prove behavioral discrimination.
9. No weakening/deleting existing passing tests to hit targets; no silent behavior change.
10. Every material decision represented in executable evidence; no narrative-only completion.

## 4. Baseline facts (frozen at 43.0)

- C42 population: 14,951 scored / 9,015 killed = **60.297%** (MATHEMATICALLY_RECONCILED).
- Distance to 80%: ≥ 11,961 killed required → **≥ +2,946 newly killed mutants**.
- Test suites: backend unit 1,639 · backend full 2,319 · runtime 785 (pre-C43 state).
- Coverage (measured 2026-08-27, sequential): **77.71%** (branch mode, .coveragerc scope).
- Survivors by component (worst first): behaviour_engine 3,383 · financial_intelligence
  1,000 · transaction_intelligence 437 · financial_events 250 · loan_engine 207 ·
  common_calculations 164 · credit_card_engine 142 · recommendation_engine 103 ·
  ledger_audit_engine 82 · reconciliation_engine 71 · cashflow_engine 44 ·
  account_engine 20 · core_domain_money 18 · balance_engine 15.

## 5. Phases and deliverables

### Phase 43.0 — Baseline freeze & inventory
Verify C42.38 certification; capture SHA; fingerprint C42 runtime surfaces (post 43.1
format-only drift reconciliation); inventory 14 mutation components, test surfaces,
coverage evidence, mutation evidence, workflow state, known failures, autogen
capabilities, C42 reuse eligibility.
→ `m9-c43-baseline.json` (immutable)

### Phase 43.1 — Workflow / CI green convergence
Inventory all 13 workflows; classify each GREEN / INTENTIONALLY_NON_AUTHORITATIVE /
ENVIRONMENTALLY_UNEXECUTABLE; run every locally-executable verify.py profile; fix root
causes (never bypass). Live GitHub Actions = ENVIRONMENTAL_LIMITATION unless executable.
→ `m9-c43-workflow-verification-matrix.json`, `m9-c43-workflow-certification.json`

### Phase 43.2 — Authoritative quality baseline
Coverage: statement/branch/function/component/capability/critical-path.
Mutation: reuse C42.26 ledger; targeted remeasurement only where invalidated.
Test health: pass/fail, flaky, slow, duplicates, property/contract/integration surfaces.
Every figure labeled MEASURED / REUSED / DERIVED / TARGETED / NOT_MEASURED /
ENVIRONMENTALLY_UNAVAILABLE.
→ `m9-c43-quality-baseline.json`

### Phase 43.3 — Coverage gap analysis
Gaps classified A–E per component/capability/module/function/branch; prioritized by
financial correctness > ledger > reconciliation > calculation > transaction > risk >
intelligence > runtime verification > other (not by line count).
→ `m9-c43-coverage-gap-analysis.json`, `m9-c43-coverage-priority-matrix.json`

### Phase 43.4 — Mutation survivor analysis
Reuse C42 taxonomy (Class A–E); per survivor: location, capability, hypothesis,
invariant, existing/missing test surface, expected discrimination; prioritized by
behavioral significance.
→ `m9-c43-mutation-survivor-analysis.json`

### Phase 43.5 — Controlled automatic test generation
Generator built on `runtime/foundation/verification/strengthening.py` + C42 proposal
contract. Evidence-driven inputs (survivor evidence, coverage gaps, capability, source
location, hypothesis, invariant, patterns). Canonical candidate output (all C42 fields).
Hard boundaries: no production fabrication, no self-approval, no autonomous production
modification, no test deletion/weakening; human authorization mandatory.
→ `m9-c43-test-generation-certification.json` + generator implementation

### Phase 43.6 — Evidence-driven strengthening
Generate → inspect → authorize → implement → targeted tests → targeted mutation →
regression → accept/reject, over prioritized gaps and Class-A survivors. Acceptance
requires behavioral discrimination evidence. Production defects found are documented
separately (Defect Ledger), never silently fixed under test-strengthening.
→ `m9-c43-strengthening-record.json` + generated tests linked to evidence

### Phase 43.7 — Targeted revalidation loop
Each changed component through the certified C42 targeted path: pre-evidence → test →
targeted tests → targeted mutation → discrimination comparison → regression →
fingerprint update → survivor reclassification → accept/reject. Unchanged components
keep reusable evidence. Aggregate maintained as AUTHORITATIVE_MEASURED +
AUTHORITATIVE_TARGETED + REUSABLE + MATHEMATICALLY_RECONCILED (never collapsed).
→ `m9-c43-targeted-revalidation.json`

### Phase 43.8 — Final coverage measurement freeze
FREEZE test/production changes; authoritative repository-wide coverage run (sequential,
uncontaminated). ≥ 80% AND no critical capability unjustifiably weak.
→ `m9-c43-final-coverage.json`

### Phase 43.9 — Final authoritative mutation campaign
Full repository-wide campaign over all 14 admitted components — justified here as the
FINAL CERTIFICATION MEASUREMENT. not_checked must be 0 (or justified+blocking);
population must reconcile; no scope reduction/source manipulation/test deletion.
If < 80%: Diagnostic Agent classifies the deficit; only genuine actionable gaps may
enter a remediation cycle, then remeasure. Certification requires stable final score.
→ `m9-c43-final-mutation.json`

### Phase 43.10 — Final workflow / CI certification
Re-run complete workflow certification against the FINAL SHA. LOCAL_GREEN vs
LIVE_CI_UNVERIFIED explicitly distinguished; no false LIVE_GREEN claims.
→ `m9-c43-final-workflow-certification.json`

### Phase 43.11 — Final verification quality certification
Certification engine evaluates: architecture preserved, quality thresholds, test
generation operating under human boundary, workflows green (or classified), evidence
reproducible, resource efficiency (actual savings recorded).
→ `m9-c43-final-certification.json`, `m9-c43-final-certification.md`,
  `m9-c43-forward-convergence-report.md`

## 6. Strengthening strategy (binding method for 43.6)

Priority order (kill budget per component, floor = 80%/component where feasible):

1. **behaviour_engine** (3,383 survivors, 35.7%) — dominant source of kills; pure
   behavior functions; property+golden discrimination tests.
2. **financial_intelligence** (1,000 survivors, 73.0%) — scenario/goal/optimization.
3. **transaction_intelligence** (437, 70.2%) — detectors with financial semantics.
4. **financial_events** (250, 64.5%) — lineage/walker behavior.
5. **common_calculations** (164, 56.4%) — shared arithmetic (high leverage).
6. **credit_card_engine** (142, 75.6%) — interest/metrics/foreclosure.
7. **recommendation_engine** (103, 63.5%), **ledger_audit_engine** (82, 56.8%),
   **loan_engine** (207, 84.0%, only if needed for aggregate), remainder.

Method rules:
- Tests assert independently-derived expected values (recomputed formulas, invariants,
  monotonicity, conservation laws, golden vectors) — never copies of implementation.
- Every generated test file carries an evidence header linking survivor ids / coverage
  gaps from the analysis artifacts.
- Per-target validation: targeted mutmut run; a batch is accepted only if it kills
  mutants it claims to kill (discrimination evidence), else reclassified/rejected.
- Class-B (equivalent) / Class-C (unreachable) survivors remain classified, never
  artificially killed.

## 7. Failure policy

Gate fails → classify via FailureKind taxonomy → diagnose → root cause → remediate →
targeted revalidate → update evidence → continue. Never: hide failures as limitations
unless meeting the established limitation definition, lower thresholds, remove failing
tests, shrink population, disable workflows, fabricate evidence.

## 8. Final evidence categories (never collapse)

AUTHORITATIVE_MEASURED · AUTHORITATIVE_TARGETED · REUSED · DERIVED ·
ENVIRONMENTAL_LIMITATION · DEFERRED · NOT_CERTIFIED

## 9. Definition of Done

G1–G27 exactly as specified in the M9-C43 task charter (all applicable gates must PASS
in `m9-c43-final-certification.json`).
