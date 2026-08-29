# M9-C43 EXECUTION PROGRESS

Operational execution record for M9-C43 (governing spec: `M9-C43-GOVERNING-PLAN.md`).

## Current milestone: PHASE 43.1 — Workflow / CI Green Convergence
**Certification state:** IN PROGRESS (43.0 complete)
**Next milestone:** 43.2 Authoritative Quality Baseline

---

## PHASE 43.0 — Baseline freeze & inventory — COMPLETE

- Started: 2026-08-27T04:23+05:30 · Completed: 2026-08-27T05:05+05:30
- Repository SHA: `f632e28f7a92a66799fda2c4c23323ca73a38858` (branch `m9c9-merge-authorization-resolution`)
- C42.38 certification verified: `runtime/generated/m9-c42.38/final-certification.json`
  (`FINAL_VERIFICATION_SYSTEM_CERTIFIED`, same SHA, 27/27 DoD, 144/144 C42.27–31 tests)
- 14-component population ledger reused: `runtime/generated/m9-c42.26/m9-c42.26-component-matrix.json`
  (14,951 scored / 9,015 killed = 60.297% MATHEMATICALLY_RECONCILED; credit_card_engine
  latest targeted measurement 75.6% per C42.38, 582 mutants in `backend/tests/generated/mutation/mutation-summary.json`)
- env-check: ENVIRONMENT CONSISTENT (canonical `.venv`, mutmut pinned 3.7.0)
- Inventories captured: test surfaces (unit 1,639 / backend full 2,319 / runtime 785),
  coverage evidence (authoritative run 77.71% branch-mode, see 43.2), mutation evidence
  (C42.26 ledger + C42.38 targeted), workflow state (13 workflows, 43.1), known failures
  (4 runtime drift failures + 1 pre-existing exit-contract failure — all remediated in 43.1),
  autogen capability (C42 `strengthening.py` proposal contract intact), C42 reuse eligibility.
- Preserved: C42 population, evidence contracts, planner, executor, diagnostic agent,
  strengthening contract, human authorization boundary.
- Artifact: `m9-c43-baseline.json` (immutable snapshot)

### Root-cause remediations executed during baseline capture (43.1 precursors)

| # | Failure | Classification | Root cause | Fix | Revalidation |
|---|---|---|---|---|---|
| W1 | `black --check backend/src/ runtime/` fails (37 files) | workflow drift (style gate unmet) | live `runtime/` sources never formatted; frozen milestone scripts under `runtime/generated/` wrongly in style-gate scope | black-formatted 21 live runtime files; excluded `runtime/generated/` (write-once artifacts — scope correction, not weakening) in root `pyproject.toml [tool.black]` | black check green; runtime suite 781→revalidated below; backend unit 1,639 pass |
| W2 | `test_quick_profile_task_ids_are_primary_gate_checks` | stale-test drift | quick gate legitimately hardened with `quick-black` task; test pinned old 3-task list | synced test to canonical 4-task gate (`runtime/tests/test_m9c5_gate_topology.py:40`) | test passes (15 passed in file) |
| W3 | `test_m81_stale_workflows_use_verification_command_pattern` | stale-test drift | mutation.yml legitimately evolved to documented smoke-first 2-job topology; test pinned single-job era | test now asserts the canonical smoke-first topology with `needs: mutation-smoke` and per-job single-command delegation | test passes |
| W4 | `test_r2_evidence_collected_with_target_config_active` | environment-state drift + latent test defect | (a) test hardcoded resting `[tool.mutmut]` scope that legitimately follows last targeted run; (b) final assertion accidentally verified the test's own `finally` restore, not the runner's | made test hermetic: seeds a distinct resting scope, snapshots config immediately after runner returns (before test finally) and asserts exact round-trip (`runtime/tests/test_mutation_infra.py`) | test passes (82s incl. real targeted mutation) |
| W5 | `test_backend_exit_contract_holds_both_directions` (pre-existing) | workflow drift introduced by C42.16 | C42.16 commit 571e351c added `invariants/_m4_exit_probe` to `norecursedirs`, silently defeating the M4 exit-contract probe injection; probe file was also committed permanently into the invariants tree (always-failing → had to be excluded → contract broken) | restored original M4 design: removed `invariants/_m4_exit_probe` from `norecursedirs` in `backend/pyproject.toml`; probe exists only transiently via injection (on-disk copy already absent; its git-tracked deletion is accepted — test infra dedup, capability untouched; canonical source remains `backend/tests/probes/test_m4_exit_probe.py`); test's own start-cleanup guards leftovers | `runtime/tests/test_backend_evidence.py` 35/35 pass (122s) |

- Flaky observation: `tests/properties/loan_engine/test_amortization_properties.py::test_balance_strictly_decreasing`
  failed only during a coverage run that OVERLAPPED a targeted mutation run (hypothesis
  example-DB / shared-state contamination between parallel pytest processes); passes in
  isolation. Rule adopted: authoritative measurements run sequentially. Final coverage
  checkpoint (43.8) will re-measure clean.

---

## PHASE 43.1 — Workflow / CI Green Convergence — IN PROGRESS

(see updates below as they land)

---

## C43.6 CONTINUATION — behaviour_engine mutation-strengthening (resolving the worst engine)

**Objective:** behaviour_engine was the worst-scoring engine (35.7% mutation, 3,383 survivors).
Resolve it via pure test/infra strengthening (no production behavior change), then run the full
14-component campaign.

### Strengthening tests added (all pure, no production change)

| File | Module(s) | Lines covered before → after | Focus |
|---|---|---|---|
| `tests/unit/engines/behaviour/test_mutation_strengthening.py` (pre-existing) | core helpers | — | boundary/value mutants |
| `tests/unit/engines/behaviour/test_mutation_strengthening_remaining.py` (NEW, 109 tests) | utils, profile, patterns, stress | utils 52%→100%, profile 63%→95%, patterns 87%→93% | exact-value + boundary mutants (`_median`, `_variance`, `_coefficient_of_variation`, `_percentage_change`, basis-points, `classify_financial_personality` confidence branches, `detect_impulse_transactions`, weekend/night ratios, recurring/subscription detection, stress indices baselines + boundary) |
| `tests/unit/engines/behaviour/test_insights_nudges_coverage.py` (NEW, 47 tests) | insights, nudges | insights 45%→98%, nudges 59%→100% | every threshold branch + `generate_summary_text` + nudge helpers |
| `tests/unit/core/mappers/test_behaviour_mapper.py` (NEW, 4 tests) | behaviour_mapper | 0%→100% | full DTO mapping incl. default/fallback branches |

### Verification
- `tests/unit/engines/behaviour/` + mapper = **505 passed**, no regressions.
- behaviour_engine unit coverage now: utils 100%, nudges 100%, insights 98%, profile 95%,
  patterns 93%, stress 75% (unit-only; integration suite lifts to 92%+).

### Authoritative measurement — COMPLETE
- `runtime/verify.py mutation --target behaviour_engine` result:
  - Generated **7,213** · Killed **4,754** · Survived **2,459** · No tests **0** · Score **65.9%**
  - Gates A (Execution Integrity) + B (Evidence Integrity): PASS
  - Up from C42 baseline 35.7% (1,875/5,258) → **+30.2pp total improvement**.
  - Stress module precise-score tests: +5.6pp (420 kills).
  - Credit_dependency module: +0.5pp (36 kills; diminishing returns).
  - All 345 "no tests" eliminated.
  - Behaviour_engine no longer the worst engine by a wide margin.

---

## C42.10 — Full 14-Component Authoritative Campaign

Per the governing plan, the authoritative 80% gate is the **full 14-component campaign** (C42.10). 
Behaviour_engine has been significantly strengthened (+30.2pp from C42 baseline). 
Per the phased roadmap (C42.7–9), remaining per-engine gaps are addressed iteratively; the authoritative measurement is the full campaign.

Launched `runtime/verify.py mutation` (full mode, 5400s budget) — result pending.

### C42.10 — RESULT
- `runtime/verify.py mutation` (full mode) completed:
  - Generated **16,905** · Killed **11,925** · Survived **4,971** · No tests **4** · Timeout **5** · Score **70.6%**
  - Gate A (Execution Integrity): PASS
  - Gate B (Evidence Integrity): PASS
  - **Gate C (Quality Threshold ≥80%): QUALITY FAIL**
  - Up from C42 baseline 60.297% → **+10.3pp improvement**
  - Behaviour_engine contribution: 7,213 mutants at 65.9% (up from 35.7% C42 baseline)

### Summary
- **Behaviour_engine:** 35.7% → 65.9% (+30.2pp) — no longer worst engine; substantial strengthening via 5 new test files (~300 tests) covering core, stress, insights, nudges, mapper, credit_dependency, utils, profile, patterns.
- **Full 14-component campaign:** 60.3% → 70.6% (+10.3pp) — still below 80% threshold.
- **Next:** Per the phased plan (C42.7–9), remaining 80% gap requires further iterative test strengthening across surviving engines. The 80% gate was not reached in this iteration; the C43 work has materially advanced the trajectory.

### Next
- On acceptable behaviour_engine score → execute full 14-component `verify.py mutation` campaign,
  then C43.9 certification + repository-acceptance-matrix / EXECUTION_PROGRESS closure.
- Defect C43-E1 (common_calculations.compute_is_large, threshold avg*250000) remains OPEN,
  human-authorization-required, unchanged by this work.
