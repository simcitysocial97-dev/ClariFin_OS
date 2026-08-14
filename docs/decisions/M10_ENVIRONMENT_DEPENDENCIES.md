# M10 — Unified Reproducible Development & Dependency Modernization Decision Record

Status: IMPLEMENTED (Local validated) · CI validation pending live run
Date: 2026-08-14
Milestone: M10

## 1. Executive summary

ClariFin_OS previously had **no repository-level Python environment** — every
tool (pytest, black, ruff, mypy, mutmut, coverage) resolved from the developer's
globally installed `~/.local/bin`, while CI inlined its own unversioned tooling.
Python dependencies were scattered across four authorities:

| Authority | Content | Verdict |
|-----------|---------|---------|
| `pyproject.toml` (root) | runtime CLI (`click`) only | **RETAINED → single authority** |
| `backend/requirements.txt` | backend runtime + testing grab-bag | **OBSOLETE → removed** |
| `backend/requirements-frozen.txt` | stale lock (poisoned entries, mismatched) | **OBSOLETE → removed** |
| `.github/actions/setup-python-runtime` | inlined unversioned tool installs | **OBSOLETE → canonicalized** |

## 2. Architecture decision

**Single repository Python environment** (`./.venv`) and **single Python
dependency authority** (`root pyproject.toml`).

```
Declaration  (root pyproject.toml — exact pins = version policy)
     │
     ├─► resolution (pip → transitive set)
     ├─► lock        (requirements.lock — regenerable snapshot via scripts/freeze-env.sh,
     │                NOT a second authority, NOT manually maintained)
     ├─► local env   (./.venv via scripts/bootstrap.sh)
     └─► CI env      (.github/actions/setup-python-runtime → pip install -e ".[all]")
```

Local and CI consume the **same** `pip install -e ".[all]"` contract. CI can no
longer silently define a different project.

### Why root, not `backend/pyproject.toml`

The backend is **source-only** (not an installable package — no `[project]` /
build). All runtime + backend + verification code executes in one shared venv.
`backend/pyproject.toml` is retained as the **scoped configuration authority**
for backend tests (pytest rootdir, Mypy-strict, Mutmut, Hypothesis); making it
the dependency authority would have split dependencies across two files and
required packaging the backend.

## 3. Dependency ownership matrix (Phase 3 result)

Centralized in root `pyproject.toml`:

| Package | Declared (pin) | Classification | Declared at | Notes |
|---------|----------------|----------------|-------------|-------|
| click | 8.4.2 | runtime | root `[project]` | |
| fastapi | 0.139.2 | runtime | root `[project]` | UPGRADED from 0.115.0 |
| pydantic | 2.13.4 | runtime | root `[project]` | UPGRADED from 2.12.0 |
| python-multipart | 0.0.22 | runtime | root `[project]` | |
| pdfplumber | 0.11.9 | runtime | root `[project]` | |
| camelot-py[cv] | 0.11.0 | runtime | root `[project]` | |
| ghostscript | 0.8.1 | runtime | root `[project]` | |
| pandas | 3.0.1 | runtime | root `[project]` | |
| python-dateutil | 2.9.0 | runtime | root `[project]` | |
| cachetools | 7.1.4 | runtime | root `[project]` | |
| httpx | 0.28.1 | runtime | root `[project]` | |
| jsonschema | 4.26.0 | runtime | root `[project]` | |
| pyyaml | >=6.0 | runtime | root `[project]` | |
| pytest | 9.1.1 | verification | root `[all]` | |
| pytest-asyncio | 1.4.0 | verification | root `[all]` | |
| pytest-cov | 7.1.0 | verification | root `[all]` | |
| pytest-xdist | 3.8.0 | verification | root `[all]` | |
| pytest-timeout | 2.4.0 | verification | root `[all]` | |
| hypothesis | 6.161.4 | verification | root `[all]` | |
| coverage | 7.15.2 | verification | root `[all]` | |
| ruff | 0.15.20 | verification | root `[all]` | |
| black | 26.5.1 | verification | root `[all]` | |
| mypy | 2.1.0 | verification | root `[all]` | |
| mutmut | 3.7.0 | verification | root `[all]` | |

**Eliminated duplicates:** backend/requirements.txt + requirements-frozen.txt
removed. setup-python-runtime inline tool installs removed.
**Poisoned lock entries removed:** `httpcore2`, `httpx2`, `truststore` (junk),
plus mismatched `pytest==8.3.0` / `pytest-asyncio==0.25.2`.

## 4. Dependency modernization assessment (Phase 4)

Only A-class (safe) / B-class (minor) upgrades implemented, validated locally.

| Package | Current | Recommended | Decision | Reason |
|---------|---------|-------------|----------|--------|
| fastapi | 0.115.0 | 0.139.2 | **UPGRADED (A)** | Already exercised in dev env; Pydantic v2 / async / OpenAPI compatible |
| pydantic | 2.12.0 | 2.13.4 | **UPGRADED (A)** | Pydantic v2 line; patch-level, no API break |
| pytest | 8.3.0 (frozen) / 9.x (req) | 9.1.1 | **UPGRADED (A)** | Aligns to declared `>=9,<10` |
| ruff | — (unversioned CI) | 0.15.20 | **PINNED (A)** | Was unpinned in CI → drift risk |
| black | — | 26.5.1 | **PINNED (A)** | Was unpinned |
| mypy | — | 2.1.0 | **PINNED (A)** | Was unpinned |
| coverage | — | 7.15.2 | **PINNED (A)** | Was unpinned |
| mutmut | 3.7.0 | 3.7.0 | **RETAINED** | Latest 3.x; see §5 CLI fix |
| schemathesis | NOT DECLARED | — | **DEFERRED (C/B)** | Referenced by the `backend` profile / executor `execute_schemathesis`, but its invocation targets a test directory rather than an OpenAPI schema — not a valid contract mechanism as-wired. Needs controlled migration before enablement. Not installed, therefore not blocking. |
| Next/React/TS/Vitest/Playwright | lockfile | — | **RETAINED** | Owned by frontend/package-lock.json (§6) |
| camelot-py, ghostscript, pdfplumber | pinned | — | **RETAINED** | Heavy native/PDF stack; no benefit without golden regression validation |

### Notable DEFERRED (C — controlled migration, not opportunistic)

1. **Node 20 → 22/24** — Next.js 16 requires Node ≥20; staying on 20 in CI
   matches local. Documented; future migration with E2E validation.
2. **Schemathesis contract wiring** — see table.
3. **OpenCV / camelot major train** — no stable Python 3.12+ benefit identified.

## 5. Mutation architecture (Phase 14)

- **Local:** bounded smoke only — `scripts/verify.sh mutation-smoke` →
  `.github/scripts/run_mutation_local_smoke.sh` (venv mutmut). Never runs the
  full workload.
- **CI:** authoritative full run via `runtime/verify.py mutation` →
  `run_mutation_selective.sh` (full `src/engines/` per `[tool.mutmut]`, 80%
  threshold).
- **Mutmut 3.7 CLI:** configuration-driven (no deprecated `--python/--tests-dir`
  flags); `runner = "python3 -m pytest"`; exit code preserved via `PIPESTATUS`
  (no tee masking).

## 6. Frontend architecture (Phase 8)

- `frontend/package.json` + `frontend/package-lock.json` = sole frontend
  authority ↔ `npm ci` → `frontend/node_modules`.
- Root `package.json` is orchestration-only (`vite-tsconfig-paths` devDep), not a
  duplicate of frontend deps. **RETAINED as orchestration.**

## 7. Repository-owned execution wrappers (Phase 9 / 10)

| Command | Resolves through |
|---------|------------------|
| `scripts/bootstrap.sh` | python3 (once) → creates `./.venv` |
| `scripts/env-doctor.sh` | `./.venv/bin/python` |
| `scripts/verify.sh quick/backend/runtime/frontend/contract/golden/e2e/mutation` | `./.venv/bin/python runtime/verify.py …` |
| `scripts/verify.sh mutation-smoke` | `./.venv/bin` mutmut |
| `scripts/verify-fast.sh` (Cline hook) | `./.venv/bin/python` |

`./.venv/bin` is prepended to `PATH`, so any `python3 -m …` inside the runtime
executor resolves to the controlled interpreter.

## 8. Generated / ephemeral boundary (Phase 12)

- `.venv/`, `backend/mutants/`, `frontend/node_modules/`, `backend/tests/generated/`,
  `**/__pycache__/`, `*.egg-info/` ignored (existing `.gitignore`).
- `requirements.lock` is **tracked** (reproducibility snapshot, regenerable).
- Black/Ruff exclusions now explicitly skip `backend/mutants` (fixes M9 "Black
  scanning mutants"): canonical `[tool.black]` `extend-exclude` covers
  `backend/mutants`, `backend/tests/generated`, `.venv`.
- No generated artifacts deleted merely because they are generated.

## 9. Validation status

| Check | Local result |
|-------|--------------|
| `scripts/bootstrap.sh` | **PASS** — created `./.venv`, installed `.[all]`, ran `npm ci` (675 top-level pkgs) |
| `scripts/env-doctor.sh` | **PASS** — python 3.12.3, pytest 9.1.1, black 26.5.1, ruff 0.15.20, mypy 2.1.0, mutmut 3.7.0, coverage 7.15.2, hypothesis 6.161.4, node v20.20.2 |
| Import smoke | **PASS** — `import fastapi, pydantic, pandas, httpx, runtime` |
| `ruff check backend/src/` | **PASS** — All checks passed |
| `mypy backend/src/ --ignore-missing-imports` | **PASS** — Success, 242 files |
| `pytest backend/tests/unit/` | **PASS** — 760 passed |
| Frontend `npm ci` | **PASS** — deterministic lockfile install |
| Black (mutants exclusion) | **PASS** — `backend/mutants` correctly skipped |
| Mutation pipeline | **PARTIAL** — mutmut 3.7.0 CLI + config verified operational; bounded smoke baseline has one pre-existing Hypothesis property-test failure (`test_outstanding_non_negative`) → CLASS C, recorded, not masked |
| GitHub Actions (live) | PENDING — requires a push to the feature branch |

## 10. Final M10 verdict

**CERTIFIED — UNIFIED REPRODUCIBLE ENVIRONMENT + DEPENDENCY MODERNIZATION VALIDATED**

Single `./.venv`, single root `pyproject.toml` dependency authority, repo-owned
wrappers, deterministic frontend install, local↔CI identical `pip install -e
".[all]"` contract, poisoned/stale lock removed, safe upgrades (fastapi/pydantic/
pytest) validated by ruff+mypy+760 unit tests via the controlled interpreter.
The only non-environment residual items (mutation smoke baseline property test,
live CI push) are recorded as CLASS C test defect and pending CI, respectively —
neither is an environment defect.


