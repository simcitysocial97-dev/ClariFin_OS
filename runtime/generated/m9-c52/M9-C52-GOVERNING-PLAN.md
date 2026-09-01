# M9-C52 — Verification Control-Plane Integration & End-to-End Enforcement

## M9-C52-GOVERNING-PLAN

**Frozen baseline:** `runtime/generated/m9-c52/m9-c52-baseline.json` (immutable).
**Repository SHA:** b8914c4333c48d36d9db2805c04d8775bedba86a (working tree carries the certified-but-uncommitted C47/C48/C49/C50/C51 surface; fingerprinted per-file in the baseline).

---

## 1. Objective

M9-C52 does NOT create a new verification architecture. It makes the certified C42 / C48 / C49 / C50 / C51
components behave as **one coherent control plane** from repository change through final certification:

```
repository change -> change detection -> capability discovery -> capability graph
  -> blast-radius resolution -> verification planning -> capability-aware execution
  -> evidence capture -> measurement truth -> diagnosis -> strengthening decision
  -> targeted revalidation -> certification
```

with **no silent bypasses**. The control plane must ENFORCE its answer at execution boundaries, not merely report it.

## 2. Certification state at freeze (M52.0)

| Check | State |
|---|---|
| C51 certification artifact | present: `runtime/generated/m9-c51/CERTIFICATION.md` |
| C51 tests | 33/33 passed |
| C50 tests | 24/24 passed |
| ruff | 0 errors (after 8 pre-freeze fixes, see below) |
| black | clean (after 6 pre-freeze reformat files) |
| mypy (backend strict) | 0 errors, 242 files |
| C51 catalog | 44 capabilities, 13 profiles |
| C51 graph | 44 nodes, 20 edges |
| C51 bypass audit | 7 scenarios classified |
| C51 latent audit | 49 findings, no deletions |
| C51 configuration authority | pytest/ruff/black/mypy/mutmut/hypothesis/frontend/CI encoded |

**Pre-freeze discrepancy found (recorded, not hidden):** C51 certified "Ruff: 0 errors, Black: clean", but the
working tree carried 51 ruff errors / 5 black violations in C47–C51 verification-framework files. Fixed pre-freeze
(auto-fixable lint + 3x `F821 undefined sys` in `strengthening_pipeline.cmd_strengthen_survivor` — a latent
NameError on the shadowed route; `import sys` added). Revalidated: 57/57 C50+C51 tests, ruff 0, black clean,
mypy 0. The C51 claim discrepancy itself is recorded in `m9-c52-baseline.json.pre_freeze_fixes`.

**Frozen findings carried into C52:**
- `strengthen-survivor` is **double-dispatched** in `runtime/verify.py`: reachable `forensic_cli.run_strengthen_survivor`
  (line 1461) shadows unreachable `strengthening_pipeline.cmd_strengthen_survivor` (line 1508). M52.2 resolves ownership.
- **28 CLI routes** (reconciled; C51 had documented 14) lack capability catalog metadata. M52.3 classifies all 28.
- Catalog `notes` metadata is per-character-corrupted in 9 entries (type error: str passed where `tuple[str,...]`
  expected). M52.1 fixes and re-certifies the catalog.

## 3. Phase plan

| Phase | Contract | Gate |
|---|---|---|
| 52.0 | Freeze C51: baseline, fingerprints, findings | baseline.json immutable |
| 52.1 | Catalog completeness: reconcile 44 capabilities vs repo; fix notes corruption; classify latent (no deletions) | catalog-certification.json |
| 52.2 | `strengthen-survivor` ownership resolved with deterministic resolution + regression tests | route-authority.json |
| 52.3 | All 28 unmapped CLI routes classified (command/impl/capability/profile/evidence/exec/diagnostic/strengthening/alias/derivation) | cli-capability-matrix.json |
| 52.4 | Unified change→capability→plan contract (composed from C50 blast-radius + C51 resolution + C42.27 evidence planner) | verification-decision.json |
| 52.5 | Execution enforcement boundary: executor refuses out-of-scope / stale / unresolvable / incompatible / scope-broadening runs; records full rationale | executor-enforcement (module + tests) |
| 52.6 | Bypass resistance: classify every bypass path SAFE/CONTROLLED/INTENTIONAL_LOW_LEVEL_ESCAPE/BYPASS_RISK/BLOCKING_BYPASS | bypass-enforcement.json |
| 52.7 | Pipeline spine enforcement: each stage's implementation/input/output/authority/evidence/failure/bypass/coverage proven | pipeline-enforcement.json |
| 52.8 | Real repository scenarios A–J executed through the real framework (not synthetic-only) | end-to-end-scenarios.json |
| 52.9 | Evidence/certification integrity: fail-closed verdicts CERTIFIABLE/NOT_CERTIFIABLE/CERTIFICATION_BLOCKED/INSUFFICIENT_EVIDENCE (C42 taxonomy, no new verdicts) | evidence-integrity.json |
| 52.10 | Strengthening handoff verification (C42.31/C43 integration; human auth mandatory) | strengthening-integration.json |
| 52.11 | Cross-capability dependency enforcement (direct/transitive/shared-infrastructure/UNAFFECTED) | cross-capability-impact.json |
| 52.12 | Configuration authority enforcement incl. deliberate drift tests | configuration-authority.json |
| 52.13 | Control-plane efficiency measurement (legacy vs targeted) | efficiency.json |
| 52.14 | Full regression (C42/C48/C50/C51/C52 + backend/frontend + static + CLI smoke + scenario harnesses) | regression.json |
| 52.15 | Final certification engine G1–G30 | certification.json + certification.md + forward-convergence-report.md |

## 4. Hard constraints (from charter, binding)

1. Preserve certified C42/C48/C49/C50/C51 architecture and their evidence semantics.
2. No duplication of planner / blast-radius engine / capability resolver / evidence model / failure taxonomy.
3. No deletion of latent capability implementations; classify instead.
4. No production-behavior changes made to satisfy verification.
5. Human authorization boundary preserved for production changes and test-strengthening acceptance.
6. C42 measurement policy preserved: targeted for localized change; full campaign only on justified triggers.
7. Every new relationship carries an explicit derivation source.
8. Every enforcement decision is explainable; every certification reproducible from artifacts.
9. `EXECUTION_PROGRESS.md` maintained continuously (milestone, timestamps, executed evidence, failures, root cause, remediation, revalidation).

## 5. Implementation approach (integration, not duplication)

- **Change detection:** reuse `change_surface.py` (C50) + git.
- **Capability discovery:** reuse `capability_resolver.py` (C48) + C51 catalog.
- **Blast radius:** reuse `compute_blast_radius()` (C50) — single engine.
- **Planning:** reuse `evidence_planner.py` (C42.27) + C50 `control_plane` plan composition; M52.4 adds a thin canonical contract object that WRAPS these calls (no new planner).
- **Execution enforcement:** M52.5 adds an `enforce_*` guard layer in front of existing executors (`execution_orchestrator.py` C49, `executor_pipeline.py` C42.28) that validates the plan contract before dispatch and refuses fail-closed. The guard is the only new component; it consumes, never replaces, the executors.
- **Certification:** M52.9/52.15 compose a certification engine over existing evidence artifacts + M52.4 decision + M52.5 execution records. Verdict vocabulary is the C42 one.
- **Bypass/pipeline/dependency/config phases** are *audits that become executable* (tests + CLI), consuming C51's static audits.

## 6. Testing

- All new behavior gets deterministic pytest in `runtime/tests/test_m9_c52*.py`.
- End-to-end scenarios A–J executed against the **real** working tree (git-based, real files) with a controlled, fully reverted working copy.
- Full regression at M52.14 through the canonical gate (`.venv` only, per AGENTS.md).

## 7. Failure policy

Any certification gate that cannot execute due to true environment limits is classified `ENVIRONMENTAL_LIMITATION`
and excluded from the verdict only with explicit documentation. Found defects are classified honestly
(`DEFECT_FOUND_AND_FIXED` or open) — never absorbed into `NON_BLOCKING` without an explicit rule.
