# M9-C42.27 — Phase 11: CI Integration Boundary

This document records what the existing CI workflows must expose to the
verification graph, where the evidence is currently uncorrelatable,
and what duplicate / lost work currently exists. It is **not** a
plan to redesign CI workflows — it is the boundary map that the
graph architecture needs to function correctly.

## Workflow → Evidence Model Mapping

| Workflow | File | Local equivalent | Evidence kind(s) | Graph integration |
| --- | --- | --- | --- | --- |
| `quick-ruff` / `quick-black` / `quick-mypy` / `quick-unit` | (fast checks) | `bash .github/scripts/run_fast_checks.sh` | `static_lint` | `static` task; **discarded today** — no `EvidenceNode` produced |
| `backend-unit` / `backend-integration` / `backend-contract` / `backend-properties` / `backend-invariants` | `run_backend_verification.sh` | `python runtime/verify.py backend` | `unit_pass`, `property_pass`, `invariant_pass`, `contract_pass`, `integration_pass` | `unit`, `property`, `invariant`, `contract`, `integration` tasks; **partially captured** in `runtime/generated/verification-cache.json` |
| `frontend-unit` / `frontend-typecheck-build` | `run_frontend_verification.sh` | `python runtime/verify.py frontend` | `unit_pass`, `static_lint` | `unit` + `static` tasks; **partially captured** |
| `contract` (Schemathesis) | `run_contract_tests.sh` | `python runtime/verify.py contracts` | `contract_pass` | `contract` task; **captured** |
| `mutation-smoke` | `run_mutation_selective.sh --smoke` | `python runtime/verify.py mutation --smoke` | `mutation_score` (smoke) | `mutation` task; **captured** as smoke-classification |
| `mutation` (authoritative) | `run_mutation_selective.sh` | `python runtime/verify.py mutation` | `mutation_score` (authoritative) | `mutation` task; **captured** as full-classification |
| `playwright` | `run_playwright_tests.sh` | `python runtime/verify.py playwright` | `e2e_pass` | `e2e` task; **discarded** in evidence model |
| `golden` | `run_golden_tests.sh` | `python runtime/verify.py golden` | `golden_pass` | `golden` task; **discarded** |
| `coverage` | (in-script via coverage.py) | `python runtime/verify.py backend` (with coverage flag) | `coverage` | `coverage` task; **partial** — only in test runs that opt in |
| `runtime` | `run_runtime_verification.sh` | `python runtime/verify.py runtime` | `static_lint` + `unit_pass` | `unit` + `static`; **discarded** |
| `repo-architecture` | `run_full_verification.sh` | `python runtime/verify.py full` | (all of the above) | **partial** — collated report only |

## Duplicate execution (currently)

1. **Mutation smoke vs mutation full** — The smoke workflow runs a
   bounded subset and writes to the mutmut cache. The full workflow
   *does not reuse* the smoke results; it re-runs the same
   collection. The fix is to recognise that smoke is a *validity
   gate* for the full, not a separate measurement.

2. **Backend unit via fast-checks vs backend-unit workflow** — the
   `run_fast_checks.sh` script runs pytest on `tests/unit/` *and*
   the `run_backend_verification.sh` re-runs the same collection
   in its own subprocess. Today the second run is the only one
   that emits evidence; the first is logged but not recorded.

3. **Frontend vitest appears in two phases** — once in
   `quick-frontend-lint` and once in `frontend` (full). The fast
   check's result is not in the evidence model.

4. **Coverage measurement is re-derived per run** — there is no
   cumulative coverage fingerprint, so a passing coverage report
   from CI run N is not reusable for CI run N+1 unless the test
   surface is identical (which it usually is not).

## Evidence currently discarded

- `playwright` results: written to Playwright's own report
  directory; not parsed into `verification-cache.json`.
- `golden` results: similarly written to a per-run log; not
  fingerprinted for reuse.
- `runtime` self-test: written to `runtime/generated/runtime-evidence.json`
  but not joined to the verification graph.
- `fast-checks` results: stdout only; no JSON.

## Evidence currently impossible to correlate

- Mutation campaign's per-component *kill lists* — the runner
  produces aggregate counts, not the per-mutant decisions
  needed to recompute kill rate from a fingerprint.
- Playwright traces — video / trace artifacts are not
  hashed into a stable fingerprint.
- Coverage reports — `coverage.json` is per-run; cross-run
  fingerprinting requires source-file hash + test-file hash,
  which is not in the current schema.

## Workflow-specific assumptions

- `mutation` workflow assumes the full population must be run; C42.27
  invalidates this assumption for unchanged components.
- `quick-*` workflows assume they can be re-run on every PR without
  cost; the framework has no concept of "this PR is a docs-only
  change, skip the full backend unit suite".
- `backend` workflow assumes the result is per-run, not
  per-component — a regression in one engine fails the whole
  workflow exit code, which loses the per-component attribution.

## Places where CI results cannot currently be reused

| CI output | Reuse blocker |
| --- | --- |
| `verification-cache.json` | No population_id; cannot be matched to the C42.26 14-component population |
| `mutmut results` (in mutmut cache) | Per-component file under `backend/mutmut-cache/`; no aggregate fingerprint |
| `coverage.json` | No `component_id`; aggregate only |
| `playwright-report/` | No evidence schema; pure HTML/JSON trace |

## What C42.27 *does not* fix (deferred)

Per the C42.27 directive, this phase does **not** redesign CI
workflows. The boundary map above is the prerequisite for that
work. C42.28+ (forward convergence) can decide whether to:

1. Add `component_id` to all CI evidence schemas.
2. Add a CI-side PopulationSnapshot fingerprint emission.
3. Replace the per-run mutation cache with a per-component
   EvidenceFingerprint store.

For now, the verification graph operates on the C42.26 baseline
snapshots that already exist; CI workflows continue to write to
their existing locations. The graph consumes those snapshots
deterministically; it does not depend on a live CI read.

## Forward position

Once the graph layer is in production use and the boundary map
above is reviewed, the C42.27 measurement policy becomes
operationally enforceable:

> *Targeted mutation* — when a specific component has materially
> changed. *Full mutation campaign* — only when one of: population
> expansion, major verification architecture change, mutation
> infrastructure/toolchain change, mutation configuration semantics
> change, significant cross-component architectural change,
> periodic measurement checkpoint, final certification milestone.

The planner's output is the authoritative decision source for
which kind of measurement to take; the CI workflow merely
executes the decision.
