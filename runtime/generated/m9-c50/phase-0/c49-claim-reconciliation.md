# M9-C50 Phase 0 — C49 Claim Reconciliation

**Generated:** 2026-09-04T11:10:00+00:00
**Baseline HEAD:** `4c2e9d86046c5bc7ff1656bf6423d489b24a7cde` (branch `m9c9-merge-authorization-resolution`)

This is the truth-revalidation of C49 (reported maturity: **ARCHITECTURALLY_CONVERGED**)
against the actual repository state.

---

## 1. C49 Claims vs Repository Evidence

| # | C49 claim | Evidence method | Verdict | Evidence |
|---|-----------|-----------------|---------|----------|
| 1 | Operator CLI reduced to 9 canonical operations | Live `verify.py` invocation | **CONFIRMED** | 9 ops printed (`check plan run diagnose strengthen inspect certify ci doctor`); all classified CANONICAL |
| 2 | All legacy commands classified | `verify.py` no-arg surface + `_CLASSIFICATION` | **CONFIRMED** | Classification vocabulary CANONICAL/ALIAS/COMPATIBILITY/DEPRECATED/UNREACHABLE/INTERNAL |
| 3 | All legacy commands route through one canonical authority | Executed legacy commands show `[M9-C49] Legacy command X -> canonical Y` | **CONFIRMED** | `verify.py capability-inventory --json` routed to `plan` |
| 4 | Executor task matrix: mutation+unit executable, others blocking | Static inspect of `executor_pipeline.py::ADAPTERS` | **SUPERSEDED** | Working tree (uncommitted) now has real adapters for all 8 kinds |
| 5 | Mutation authority single | `executor_pipeline.py::adapt_mutation_task` + MutationOrchestrator | **PARTIAL / CONFIRMED** | Single mutmut authority claimed; dormant forensic/mutation result paths not yet proven unified |
| 6 | Capability completeness | `verify.py inspect capabilities` | **REJECTED (gap)** | 10 capabilities produce `unknown_evidence_kind` outside closed EVIDENCE_KINDS vocabulary |
| 7 | 112 frontend arithmetic findings | C48 `frontend-arithmetic-lint.json` | **CONFIRMED UNRESOLVED** | C49 report itself lists them as not remediated |
| 8 | 11 CI workflows still use legacy commands | `.github/workflows/*.yml` diff | **SUPERSEDED** | Working tree has migrated all 11 workflows to canonical commands (uncommitted) |
| 9 | 6 task kinds have blocking adapters only | `executor_pipeline` committed state | **SUPERSEDED** | Working tree implements real adapters |
| 10 | No second semantic authority | Static architecture review | **MOSTLY CONFIRMED / REMAINING DORMANT** | forensic_cli.py, blast_radius_cli.py still expose legacy DEPRECATED commands that must be proven to delegate |

---

## 2. Key Discrepancies Recorded

1. **C49 final report (FINAL_CONVERGENCE_REPORT.md) was written against SHA `35a31f50`**, but the
   current HEAD is `4c2e9d86` (a later commit). The report's recorded repository SHA is stale relative
   to the current baseline.

2. **Working tree is DIRTY (44 files).** The current HEAD does not contain the C50 executor-adapter,
   CI-migration, or event-store changes. Any maturity certification at HEAD must not claim evidence
   that only exists in the working tree.

3. **10 capability-issued evidence kinds** break the closed `EVIDENCE_KINDS` contract — direct
   contradiction of "evidence enters the common evidence model" and "no successful status without valid
   evidence".

4. **Frontend arithmetic (112 findings)** — C49 explicitly deferred; cross-layer obligation
   outstanding for C50 Phase 7.

5. **CI migration** claims in C49 deferred; now in-progress in working tree.

---

## 3. Independent Revalidation (representative real operations)

| Operation | Command | Exit | Result |
|-----------|---------|------|--------|
| Health / integrity | `verify.py doctor` | 0 | Health report generated |
| Capability catalog | `verify.py inspect capabilities` | 0 | 55 capabilities / 13 profiles / 10 issues |
| Obligation planning | `verify.py capability-inventory --json` | 0 | Obligation sets emitted |
| CLI governance | `pytest .../test_m9_c49_canonical_cli.py .../test_m9_c50_executor_adapters.py .../test_m9_c50_ci_convergence.py` | 0 | 99 passed, 4 skipped |
| Baseline collection | `verify.py env-check` footprint | 0 | envinfo emitted |

---

## 4. Conclusion

C49's central architectural claims (single 9-command control plane, classification of all legacy
tokens, canonical capability authority) are **independently confirmed** by live execution. However,
**full ARCHITECTURALLY_CONVERGED is not yet honest** because of the 10 unknown-evidence-kind
capability issues, the stale report SHA, and an uncommitted working tree containing C50 convergence
work. Phase 1+ must drive these to closure, not assume they are already converged.