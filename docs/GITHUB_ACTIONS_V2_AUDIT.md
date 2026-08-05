# GitHub Actions V2 Audit

> **Generated:** 2026-08-05  
> **Scope:** Program 11.5 — GitHub Actions Architecture Finalization  
> **Reference:** `docs/GITHUB_ACTIONS_CONSTITUTION.md`

---

## 1. Workflow Inventory

| Workflow | Status | Purpose | Concurrency | Cancel |
|----------|--------|---------|-------------|--------|
| `backend-verify.yml` | ✅ KEEP | Backend verification | enabled | true |
| `frontend-verify.yml` | ✅ KEEP | Frontend verification | enabled | true |
| `quality.yml` | ✅ KEEP | Fast quality gate | enabled | true |
| `verification-runtime.yml` | ✅ KEEP | Runtime self-validation | enabled | true |
| `golden.yml` | ✅ KEEP | Golden regression (nightly) | enabled | **false** |
| `mutation.yml` | ✅ KEEP | Mutation testing (nightly) | enabled | **false** |
| `playwright.yml` | ✅ KEEP | E2E browser tests | enabled | true |
| `release.yml` | ✅ KEEP | Build + publish release | enabled | **false** |
| `dependency-update.yml` | ✅ KEEP | Weekly dependency health | enabled | true |

**Deleted in previous milestone (Program 11):**
- `backend.yml` — Retired, superseded by `backend-verify.yml`
- `ci.yml` — Retired, superseded by `quality.yml`
- `full-validation.yml` — Retired, superseded by `quality.yml`
- `nightly-property-tests.yml` — Removed, redundant with `mutation.yml`
- `frontend-build.yml` — Merged into `frontend-verify.yml`
- `frontend.yml` — Merged into `frontend-verify.yml`

---

## 2. Composite Action Inventory

| Action | Purpose | Used By |
|--------|---------|---------|
| `setup-python-runtime` | Python 3.12, pip cache, deps | `bootstrap-runtime` → all workflows |
| `setup-node-runtime` | Node.js 20, npm cache, frontend deps | frontend-verify, playwright, release, dependency-update |
| `setup-playwright` | Playwright browsers with cache | playwright |
| `bootstrap-runtime` | Canonical bootstrap: Python + cross-layer map + knowledge index + version validation | backend-verify, frontend-verify, quality, verification-runtime, golden, mutation, playwright, dependency-update |
| `upload-runtime` | Standardized artifact upload with retention policy | All workflows |

---

## 3. Validation Results

```
python3 .github/scripts/validate_actions.py

Workflows validated: 9
Composite actions validated: 5

ALL CHECKS PASSED
```

### Checks Performed

| Check | Rule | Result |
|-------|------|--------|
| YAML syntax — all workflows | Rule 4 | ✅ PASS |
| YAML syntax — all composite actions | Rule 4 | ✅ PASS |
| No inlined `actions/setup-python` | Rule 4 | ✅ PASS |
| No inlined `actions/setup-node` | Rule 4 | ✅ PASS |
| No inlined `actions/cache` | Rule 4 | ✅ PASS |
| No inlined `actions/upload-artifact` | Rule 3/4 | ✅ PASS |
| No inline artifact generation (build_cross_layer_map / save_index) | Rule 3 | ✅ PASS |
| Every verification workflow runs correct profile | Rule 8 | ✅ PASS |
| Every workflow has concurrency block | Rule 6 | ✅ PASS |
| No-cancel workflows in exception list | Rule 6 | ✅ PASS |
| Path filters on verification push triggers | Rule 7 | ✅ PASS (quality intentionally unfiltered) |
| `verify.py status` summary on every workflow | Rule 9 | ✅ PASS |
| No duplicated artifact names within a workflow | Rule 3/4 | ✅ PASS |
| All workflows use bootstrap-runtime | Rule 3 | ✅ PASS |
| All referenced scripts exist | Rule 1 | ✅ PASS |

---

## 4. Artifact Lifecycle Summary

| Artifact | Owner | Generation | Retention | Collision Risk |
|----------|-------|-----------|-----------|----------------|
| `cross-layer-map` | bootstrap-runtime | `build_cross_layer_map.py` | 14 days | None — shared upload |
| `knowledge-index` | bootstrap-runtime | `save_index()` | 14 days | None — shared upload |
| `verification-cache` | bootstrap-runtime | `verify.py` orchestrator | 14 days | None — shared upload |
| `engineering-history` | bootstrap-runtime | `verify.py` event store | 14 days | None — shared upload |
| `backend-report` | backend-verify | `verify.py backend` | 14 days | Unique |
| `backend-evidence` | backend-verify | `verify.py backend` | 30 days | Unique |
| `frontend-report` | frontend-verify | `verify.py frontend` | 14 days | Unique |
| `frontend-evidence` | frontend-verify | `verify.py frontend` | 30 days | Unique |
| `runtime-quality` | verification-runtime | `verify.py runtime` | 14 days | Unique |
| `runtime-performance` | verification-runtime | `verify.py runtime` | 30 days | Unique |
| `quality-report` | quality | `verify.py quick` | 14 days | Unique |
| `fast-checks-evidence` | quality | `verify.py quick` | 30 days | Unique |
| `golden-report` | golden | `verify.py golden` | 90 days | Unique |
| `golden-evidence` | golden | `verify.py golden` | 30 days | Unique |
| `mutation-report` | mutation | `verify.py mutation` | 90 days | Unique |
| `mutation-evidence` | mutation | `verify.py mutation` | 30 days | Unique |
| `playwright-report` | playwright | `verify.py playwright` | 30 days | Unique |
| `playwright-evidence` | playwright | `verify.py playwright` | 30 days | Unique |
| `frontend-dist` | release | `npm run build` | 90 days | Unique |
| `release-notes` | release | `generate_release_notes.sh` | 90 days | Unique |
| `python-dependencies` | dependency-update | `pip-audit` | 30 days | Unique |
| `npm-dependencies` | dependency-update | `npm audit` | 30 days | Unique |
| `dependency-health` | dependency-update | script | 30 days | Unique |

**Duplicated artifact names within a workflow:** 0  
**Cross-workflow artifact name collisions:** 0

---

## 5. Path Filter Analysis

| Workflow | Push Paths | PR Paths | Adequate? |
|----------|-----------|----------|-----------|
| `backend-verify.yml` | `backend/**`, `runtime/**` | same | ✅ |
| `frontend-verify.yml` | `frontend/**`, `backend/src/routers/**`, `backend/src/mappers/**`, `runtime/**` | same | ✅ |
| `quality.yml` | *(none)* | *(none)* | ✅ Intentional — fast gate on all |
| `verification-runtime.yml` | `runtime/**`, `backend/src/engines/**`, `backend/src/routers/**`, `backend/src/mappers/**` | same | ✅ |
| `golden.yml` | *(schedule only)* | *(schedule only)* | N/A |
| `mutation.yml` | *(schedule only)* | *(schedule only)* | N/A |
| `playwright.yml` | `frontend/**`, `e2e/**`, `runtime/**` | same | ✅ |
| `release.yml` | *(release only)* | *(release only)* | N/A |
| `dependency-update.yml` | *(schedule only)* | *(schedule only)* | N/A |

---

## 6. Concurrency Analysis

| Workflow | Group | Cancel | Correct? |
|----------|-------|--------|----------|
| `backend-verify.yml` | `${{ github.workflow }}-${{ github.ref }}` | true | ✅ |
| `frontend-verify.yml` | `${{ github.workflow }}-${{ github.ref }}` | true | ✅ |
| `quality.yml` | `${{ github.workflow }}-${{ github.ref }}` | true | ✅ |
| `verification-runtime.yml` | `${{ github.workflow }}-${{ github.ref }}` | true | ✅ |
| `golden.yml` | `${{ github.workflow }}-${{ github.ref }}` | false | ✅ Exception |
| `mutation.yml` | `${{ github.workflow }}-${{ github.ref }}` | false | ✅ Exception |
| `playwright.yml` | `${{ github.workflow }}-${{ github.ref }}` | true | ✅ |
| `release.yml` | `${{ github.workflow }}-${{ github.ref }}` | false | ✅ Exception |
| `dependency-update.yml` | `${{ github.workflow }}-${{ github.ref }}` | true | ✅ |

---

## 7. Local/CI Command Parity

| Workflow | CI Command | Local Equivalent | Parity |
|----------|-----------|-----------------|--------|
| `backend-verify.yml` | `python runtime/verify.py backend` | `python runtime/verify.py backend` | ✅ |
| `frontend-verify.yml` | `python runtime/verify.py frontend` | `python runtime/verify.py frontend` | ✅ |
| `quality.yml` | `python runtime/verify.py quick` | `python runtime/verify.py quick` | ✅ |
| `verification-runtime.yml` | `python runtime/verify.py runtime` | `python runtime/verify.py runtime` | ✅ |
| `golden.yml` | `python runtime/verify.py golden` | `python runtime/verify.py golden` | ✅ |
| `mutation.yml` | `python runtime/verify.py mutation` | `python runtime/verify.py mutation` | ✅ |
| `playwright.yml` | `python runtime/verify.py playwright` | `python runtime/verify.py playwright` | ✅ |
| `release.yml` | N/A (build) | N/A | N/A |
| `dependency-update.yml` | N/A (operational) | N/A | N/A |

---

## 8. Duplicated Steps Removed

| Duplicate Step | Source | Resolution |
|---------------|--------|------------|
| Inline `actions/setup-python` | All 9 workflows | Delegated to `bootstrap-runtime` → `setup-python-runtime` |
| Inline `actions/setup-node` | frontend-verify, playwright, release, dependency-update | Delegated to `setup-node-runtime` |
| Inline `actions/cache` | All workflows | Delegated to `bootstrap-runtime` / `setup-node-runtime` / `setup-playwright` |
| Inline `actions/upload-artifact` | All workflows | Delegated to `upload-runtime` |
| Inline `build_cross_layer_map.py` | Multiple workflows | Generated once by `bootstrap-runtime` |
| Inline `save_index()` | Multiple workflows | Generated once by `bootstrap-runtime` |
| Retired `backend.yml` | 12 jobs, duplicated backend-verify | Deleted — superseded |
| Retired `ci.yml` | 5 jobs, duplicated quality | Deleted — superseded |
| Retired `full-validation.yml` | 3 jobs, duplicated quality + runtime | Deleted — superseded |
| Retired `nightly-property-tests.yml` | 2 jobs, duplicated mutation | Deleted — redundant |
| Retired `frontend-build.yml` | 1 job, merged into frontend-verify | Deleted — merged |
| Retired `frontend.yml` | 2 jobs, merged into frontend-verify | Deleted — merged |

**Total workflows removed:** 6  
**Total workflows consolidated:** 2 → 1 (`frontend-build.yml` + `frontend.yml` → `frontend-verify.yml`)

---

## 9. Known Limitations

| Item | Status |
|------|--------|
| `quality.yml` has no path filter | ✅ Intentional — fast gate must run on all changes |
| Scheduled workflows have no path filter | ✅ Intentional — schedules run regardless of paths |
| Release workflow does not run `verify.py` | ✅ Intentional — release is a build pipeline, not a verification profile |
| `dependency-update.yml` does not run `verify.py` | ✅ Intentional — operational workflow, not a verification profile |

---

## 10. Constitution Compliance

| Constitutional Rule | Status |
|---------------------|--------|
| Rule 1 — No duplicated engineering logic | ✅ Enforced |
| Rule 2 — One responsibility per workflow | ✅ Enforced |
| Rule 3 — Single artifact generation | ✅ Enforced |
| Rule 4 — Identical setup via composite actions | ✅ Enforced |
| Rule 5 — Artifact retention policy | ✅ Enforced |
| Rule 6 — Concurrency configured | ✅ Enforced |
| Rule 7 — Path filtering | ✅ Enforced |
| Rule 8 — Delegate to `runtime/verify.py` | ✅ Enforced |
| Rule 9 — Job summaries via `verify.py status` | ✅ Enforced |
| Rule 10 — Local/CI parity | ✅ Enforced |

---

## 11. Validation Commands

```bash
# Primary validation — checks all workflows and actions against the constitution
python3 .github/scripts/validate_actions.py

# Expected output:
# Workflows validated: 9
# Composite actions validated: 5
#
# ALL CHECKS PASSED
```

---

## 12. Deliverables Produced

| Deliverable | Path |
|-------------|------|
| GitHub Actions Constitution | `docs/GITHUB_ACTIONS_CONSTITUTION.md` |
| V2 Audit Report | `docs/GITHUB_ACTIONS_V2_AUDIT.md` (this file) |
| Composite Actions (5) | `.github/actions/setup-python-runtime/`, `.github/actions/setup-node-runtime/`, `.github/actions/setup-playwright/`, `.github/actions/bootstrap-runtime/`, `.github/actions/upload-runtime/` |
| Validation Harness | `.github/scripts/validate_actions.py` |
| Verification Profiles (10) | `runtime/foundation/verification/profiles.py` |
| Cross-Layer Map Generator | `tools/generators/build_cross_layer_map.py` |
| Knowledge Indexer | `runtime/foundation/knowledge/indexer.py` |
| Execution Runtime | `runtime/verify.py` |
