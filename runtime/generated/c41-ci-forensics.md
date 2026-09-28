# M9-C41 — CI Dependency Lifecycle & Mutation Forensics

**Status: CONDITIONAL** — Finding A refuted; Finding B requires nightly CI confirmation.

## Finding A — "next: not found, add npm ci"

**Claim**: Add `working-directory: ./frontend` + `npm ci`.

**Forensic result — NOT REPRODUCED (false positive):**

- `.github/workflows/playwright.yml` → `setup-node-runtime` action runs `npm ci` (working-directory `frontend`).
- `.github/scripts/run_playwright_tests.sh` runs `npm run build && npx playwright test`.
- `runtime/verify.py playwright` profile command: `cd frontend && npm run build && npx playwright test ${PLAYWRIGHT_PROJECT}`.
- CI lifecycle is already correct: `checkout → setup-node(npm ci) → setup-playwright → verify.py playwright (build+test) → upload artifacts`.

The recommended `npm ci` addition is **redundant**. The only place `npm start` failed was a LOCAL run that skipped the build step — a local usage error, not a CI defect. `python runtime/verify.py playwright` correctly builds first.

## Finding B — "mutation exited 1, score < 80%"

**Claim**: Mutation score fell below 80%.

**Forensic result — UNVERIFIED:**

- `mutation.yml` is a **nightly scheduled** job (`cron: 0 2 * * *`) + `workflow_dispatch`; NOT part of the per-PR gate (C40 reported Mutation = CI_REQUIRED).
- `.github/scripts/run_mutation_selective.sh`: `mutmut run`, exit-code semantics `0=success,1=infra,2/4/8=survivors/timeout/slow`, threshold **80%** in `backend/tests/mutation/mutation_config.toml`.
- Threshold is identical locally and in CI; corpus is identical; `mutmut run` is read-only (no source mutation persisted).
- **Not executed this session** (long-running nightly job). Threshold is treated as authoritative and **NOT lowered**.

**If nightly shows genuine survivors**: add behaviorally-meaningful tests (never tests whose sole purpose is killing a mutant). Threshold synchronization already confirmed.

## Authoritative Dependency Lifecycle (verified)

fresh runner → checkout → setup-node (npm ci) → setup-playwright → verify.py playwright (build + test, matrix sharded by `PLAYWRIGHT_PROJECT`) → upload artifacts. Single installation authority; runtime parity confirmed.
