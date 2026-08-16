# Program E — Quality Gate Root Cause Isolation

**Status:** Investigation Complete  
**Date:** 2026-08-07  
**Workflow:** Quality Gate (`.github/workflows/quality.yml`)  
**CI Run:** [#31203946933](https://github.com/simcitysocial97-dev/ClariFin_OS/actions/runs/31203946933)  
**Commit:** `08fdea46` — *Program D: Quality Gate stabilization fixes*

---

## 1. Exact Failing Verifier

| Field | Value |
|-------|-------|
| **Step** | `step-0001` |
| **Name** | `bash .github/scripts/run_fast_checks.sh` |
| **Status** | `failed` |
| **Duration** | `19.1s` |
| **Failure Title** | `ImportError: No module named 'src.core.db'` |
| **Failure Message** | `ModuleNotFoundError: No module named 'src.core.db'` |
| **Verification Step** | Check 4/6: Unit tests (`pytest tests/unit/`) |
| **Owning Script** | `.github/scripts/run_fast_checks.sh` |
| **Owning Module** | `pytest 8.3.0` — plugin loader (`tests.fixtures.database`) |

### Stack Trace (reproduced locally in clean clone)

```
File "/tmp/clarifin-ci-sim/backend/tests/fixtures/database.py", line 24, in <module>
    from src.core.db.schema import create_all, run_migrations, verify_schema
ImportError: Error importing plugin "tests.fixtures.database": No module named 'src.core.db'
```

---

## 2. Failure Pipeline

```
verification profile: quick
        ↓
verification registry: runtime/foundation/verification/registry/registry.py
        ↓
planner: runtime/foundation/verification/planner/planner.py
        ↓
selected verification: quick-run (scope=QUICK, capability=quick)
        ↓
script: bash .github/scripts/run_fast_checks.sh
        ↓
tool: pytest 8.3.0
        ↓
failure: ImportError during pytest_load_initial_conftests
```

### Pipeline Details

1. **Profile:** `quick` — lightweight quality gate (ruff, black, mypy, unit, architecture, meta).
2. **Registry:** Maps `quick` capability to workflow `quick` → script `run_fast_checks`.
3. **Planner:** With 2 changed files (`runtime/generated/cross-layer-map-v2.json`, `runtime/generated/knowledge-index.json`), resolves scopes to `[QUICK]`, selects 1 target (`quick-run`), builds 1 step.
4. **Script:** `run_fast_checks.sh` runs 6 checks sequentially. Check 4 (`pytest tests/unit/`) fails first.
5. **Tool:** pytest 8.3.0 attempts to load `backend/tests/conftest.py`, which registers `pytest_plugins = ["tests.fixtures.database", ...]`.
6. **Failure:** `tests.fixtures.database` imports `src.core.db.schema`, which does not exist in the committed repository.

---

## 3. CI vs Local Comparison

### Repository State

| Aspect | CI | Local |
|--------|----|-------|
| **Commit** | `08fdea46` (clean checkout) | `08fdea46` (dirty working tree) |
| **Changed files** | `2` (generated artifacts from bootstrap) | `19` modified + `2` untracked |
| **Missing files** | `backend/src/core/db/*.py` (6 files) | Present on disk, but untracked + ignored |

### Environment

| Aspect | CI | Local |
|--------|----|-------|
| **Python** | `3.12.13` (hostedtoolcache) | `3.12.3` |
| **Python command** | `python` | `python3` |
| **Runner OS** | `ubuntu-latest` | `linux` |
| **pytest version** | `8.3.0` (pinned in `backend/requirements.txt`) | `9.0.2` (unpinned, system-wide) |
| **Dependencies** | Pinned via `pip install -r backend/requirements.txt` | Mixed versions |

### Generated Artifacts

| Aspect | CI | Local |
|--------|----|-------|
| **verification-report.md** | Not generated (job failed before upload) | Stale — generated from previous commit state |
| **verification-cache.json** | Seeded as `{}` by bootstrap | Stale — `last_commit=22ed278d` |
| **execution artifacts** | Not uploaded (upload steps skipped) | Empty files (Executor cleanup bug) |

### Divergence Summary

The single decisive difference is **repository cleanliness**:

- **Local:** `backend/src/core/db/schema.py` and 5 sibling files exist on disk. They were created/edited locally but never committed. The `.gitignore` rule `src/` (line 89) causes git to ignore the entire `backend/src/core/db/` tree.
- **CI:** Clean checkout at `08fdea46` lacks these 6 files. When pytest loads `tests.fixtures.database`, it crashes with `ImportError: No module named 'src.core.db'`.

---

## 4. Root Cause Classification

**Primary Root Cause:** `Repository cleanliness`

### Evidence

1. `.gitignore` line 89 contains `src/` — a pattern that matches `backend/src/` at any directory level.
2. `backend/src/core/db/schema.py` exists locally (32 KB, last modified 2026-08-07 20:22) but is **not tracked in git**.
3. `git ls-tree HEAD -- backend/src/core/db/` returns empty output — the directory does not exist in commit `08fdea46`.
4. `backend/tests/fixtures/database.py` (tracked) imports `src.core.db.schema` (untracked).
5. `backend/src/db.py` (tracked) also imports `src.core.db.schema`.
6. Reproduced in clean clone: `cd backend && pytest tests/unit/` fails with the exact same `ImportError`.

---

## 5. Minimal Repair Recommendation

### Affected Files

- `backend/src/core/db/__init__.py`
- `backend/src/core/db/config.py`
- `backend/src/core/db/connection.py`
- `backend/src/core/db/schema.py`
- `backend/src/core/db/transaction.py`
- `backend/src/core/db/health.py`
- `.gitignore`

### Smallest Possible Correction

1. **Change `.gitignore` line 89** from `src/` to `/src/` so the rule only ignores a root-level `src/` directory, not `backend/src/`.
2. **Add the 6 missing files** in `backend/src/core/db/` to git.

### Expected Blast Radius

- **Low.** Only affects test execution in clean checkout environments.
- No runtime logic changes.
- No verification logic changes.
- No workflow changes.
- No architecture changes.

### Verification Required After Repair

1. `git checkout main && git clean -fdx && python runtime/verify.py quick` must exit `0`.
2. `git ls-files backend/src/core/db/` must list all 6 files.
3. `git check-ignore -v backend/src/core/db/schema.py` must return no output.

---

## 6. Supporting Evidence Files

- `runtime/generated/quality-gate-root-cause.json`
- `runtime/generated/quality-gate-evidence.json`
- `runtime/generated/quality-gate-ci-vs-local.json`
- `runtime/generated/quality-gate-repair-plan.json`
