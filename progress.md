# M9-C1 Execution Progress

## Objective
Correct the proven CI environment/dependency failures identified by the M9 Execution Forensic Verdict.

## Current Status
IN_PROGRESS — Milestone 1 complete; Milestone 2 in progress.

---

## Milestone 1 — Repository dependency authority audit

### Files inspected
- `.github/actions/setup-python-runtime/action.yml`
- `.github/actions/bootstrap-runtime/action.yml`
- `.github/actions/setup-node-runtime/action.yml`
- `backend/requirements.txt`
- `backend/requirements-frozen.txt`
- `backend/pyproject.toml`
- `frontend/package.json`
- `frontend/package-lock.json`
- `.github/workflows/quality.yml`
- `.github/workflows/backend-verify.yml`
- `.github/workflows/verification-runtime.yml`
- `.github/workflows/frontend-verify.yml`
- `.github/workflows/mutation.yml`
- `.github/workflows/verification-reconcile.yml`
- `.github/workflows/dependency-update.yml`
- `.github/workflows/playwright.yml`
- `.github/workflows/release.yml`
- `.github/scripts/run_fast_checks.sh`
- `.github/scripts/run_backend_verification.sh`
- `.github/scripts/run_frontend_verification.sh`
- `.github/scripts/run_mutation_selective.sh`
- `.github/scripts/run_runtime_verification.sh`

### Findings

#### Python dependency authority
- Canonical runtime/test dependencies: `backend/requirements.txt`
- Frozen lockfile: `backend/requirements-frozen.txt` (contains older versions: pytest==8.3.0, pytest-asyncio==0.25.2)
- Composite action: `.github/actions/setup-python-runtime/action.yml`
  - Installs `backend/requirements.txt` first
  - Then hardcodes additional verification tooling: pyyaml, ruff, black, mypy, coverage, pytest, pytest-cov, pytest-xdist, pytest-timeout, hypothesis, mutmut
- All verification workflows use `bootstrap-runtime` -> `setup-python-runtime`

#### Redundant / duplicate authorities
- `pyyaml` is in `backend/requirements.txt` AND hardcoded in the action
- `pytest` is in `backend/requirements.txt` AND hardcoded in the action
- `pytest-cov` is in `backend/requirements.txt` AND hardcoded in the action
- `mutmut` is NOT in `backend/requirements.txt` but IS hardcoded in the action

#### Frontend dependency authority
- Canonical: `frontend/package.json` + `frontend/package-lock.json`
- Composite action: `.github/actions/setup-node-runtime/action.yml`
  - Runs `npm ci` in the frontend directory
- All frontend workflows use `setup-node-runtime`

#### Critical observation from CI execution evidence
- Quality Gate workflow run 31655294526 shows `bootstrap-runtime` successfully installing pytest 9.1.1 and mutmut 3.7.0
- The "Verify environment" step confirms `pytest 9.1.1`
- This contradicts the forensic verdict's claim that "pytest executable missing from CI PATH" for workflows using the canonical bootstrap
- The forensic workflow (m9-forensic-diagnostic-lab.yml) used a custom minimal bootstrap that intentionally bypassed the canonical actions, explaining the missing tools in that specific run

#### Decision
Per user instruction: "Do not reopen those conclusions unless new execution evidence directly contradicts them." The new CI evidence does contradict the forensic verdict's specific claim about pytest/mutmut absence in canonical workflows. However, the user's objective remains: "Restore reproducible CI execution... by ensuring that every verification workflow receives the complete dependency environment."

The minimal correction is to align the composite action with the canonical dependency declaration, eliminating duplicate authorities and ensuring `mutmut` is declared in `backend/requirements.txt`.

---

## Milestone 2 — Minimal dependency correction

### Changes made

#### 1. `backend/requirements.txt`
- Added `mutmut>=3.7.0` to the Testing section
- This makes `mutmut` part of the canonical dependency declaration

#### 2. `.github/actions/setup-python-runtime/action.yml`
- Removed redundant hardcoded packages from "Install verification tooling" step:
  - `pyyaml` (already in `backend/requirements.txt`)
  - `pytest` (already in `backend/requirements.txt`)
  - `pytest-cov` (already in `backend/requirements.txt`)
  - `mutmut` (now in `backend/requirements.txt`)
- Kept hardcoded packages NOT in `backend/requirements.txt`:
  - `ruff`, `black`, `mypy`, `coverage`, `pytest-xdist`, `pytest-timeout`, `hypothesis`

### Rationale
- Eliminates duplicate dependency authorities
- Prefers canonical `backend/requirements.txt` over hardcoded action lists
- Maintains the action's role as canonical verification-tool installer for packages not in requirements.txt
- No production verification logic was modified

---

## Milestone 3 — Clean-environment validation
*Pending*

## Milestone 4 — Direct verification script validation
*Pending*

## Milestone 5 — Framework-level validation
*Pending*

## Milestone 6 — GitHub Actions validation
*Pending*

## Milestone 7 — Regression and scope protection
*Pending*

## Milestone 8 — Certification
*Pending*
