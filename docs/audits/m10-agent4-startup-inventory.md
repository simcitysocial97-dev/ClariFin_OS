# M10 Agent 4 — Startup Inventory

**Baseline:** `main @ bfcf336b5b7f46e759c7486f3eb02d0f8d92e14b`
**Scope:** every way this repository can be started, and its classification.
**Ownership:** `start.sh`, `start.bat`, `servers/**`, `scripts/launch.sh`,
`scripts/bootstrap.sh`, root `package.json` scripts, operator documentation.

## Classification vocabulary

| Class | Meaning |
| --- | --- |
| `CANONICAL` | The one official way to do this. Everything else defers to it. |
| `VALID SECONDARY` | Genuinely useful, deliberately narrower than canonical, documented as such. |
| `DUPLICATE` | Reimplements something already covered; kept only if it adds reach. |
| `OBSOLETE` | Superseded, replaced, or no longer meaningful. |
| `BROKEN` | Cannot succeed as written. |
| `UNSAFE` | Can succeed while harming state the user did not ask it to touch. |

## Search performed

Exhaustive across: root `*.sh`/`*.bat`/`*.ps1`/`*.cmd`; `scripts/`; `servers/`;
root and `frontend/package.json` scripts; `backend/` entrypoints;
`docker-compose*`; `Makefile`/`justfile`; `.husky/`; `backend/scripts/`;
`tools/`; Python `__main__` and `[project.scripts]` in `pyproject.toml`; and the
git history for deleted or renamed launchers still referenced by documentation.

### Negative results (searched, nothing found)

| Searched for | Result |
| --- | --- |
| `docker-compose*` (any depth ≤ 3) | none |
| `Makefile` / `makefile` / `justfile` / `Justfile` | none |
| `*.ps1` / `*.cmd` (any depth ≤ 3, outside `.venv`) | none |
| Root `run.sh`, `dev.sh`, `serve.sh`, `bootstrap.sh` | none — only `start.sh`/`start.bat` |
| Second frontend launcher | none — `frontend/package.json` is the only frontend `scripts` block |
| Python `__main__` startup entry | none; the backend is started via `uvicorn src.api:app` |
| `[project.scripts]` console entry points | exactly one: `verify = runtime.foundation.verification.cli.cli:cli` (verification, not an app launcher) |

## Inventory

### A. Full application (backend + frontend)

| # | Entry point | Class | Evidence |
| --- | --- | --- | --- |
| 1 | `scripts/launch.sh start` | **CANONICAL** | Declared canonical by `start.sh:6-8` ("single source of truth"), `scripts/bootstrap.sh:146`, and `AGENTS.md`. Implements validate → start → readiness → URLs. Retained and extended. |
| 2 | `./start.sh` (no args) | **CANONICAL (Unix entry)** | Thin wrapper; `exec bash scripts/launch.sh start`. Fixed: previously ignored all arguments. |
| 3 | `start.bat` (Windows) | **CANONICAL (Windows entry)** | Delegates to the same `scripts/launch.sh` over WSL2. Fixed: previously passed a Windows backslash path to `bash`, which cannot resolve inside WSL. |
| 4 | `npm start` (root `package.json`) | **VALID SECONDARY** | Did not exist before. Added as a discovery convenience that delegates to `./start.sh`. No logic of its own. |
| 5 | `npm run stop` / `restart` / `status` / `health` / `console` / `logs` / `check-env` / `bootstrap` (root) | **VALID SECONDARY** | Same — pure delegation to `./start.sh`. |
| 6 | `frontend/package.json` `dev` (`next dev`) | **VALID SECONDARY** | Next.js-native dev workflow with hot reload. Narrower than canonical (frontend only, no backend, no env validation). Retained deliberately; `scripts/launch.sh frontend` wraps it for launcher-managed use. |
| 7 | `frontend/package.json` `start` (`next start`) | **DUPLICATE of the frontend half of #1** | Invoked by `serve_frontend` inside the launcher. Retained: it is the primitive the canonical path composes, and removing it would break `npm run build && npm start` workflows. |
| 8 | `.venv/bin/python -m uvicorn src.api:app --port 8000` | **VALID SECONDARY** | Canonical backend *primitive* (`scripts/launch.sh start_backend`), documented in `launch.sh:9-10`. Retained: the launcher composes it, so it must remain usable standalone for debugging. |
| 9 | `console_scripts: verify` (`pyproject.toml:80-81`) | **VALID SECONDARY (out of scope)** | Verification entry point, not an application launcher. Untouched. |

### B. Platform Console

| # | Entry point | Class | Evidence |
| --- | --- | --- | --- |
| 10 | `scripts/launch.sh console` | **CANONICAL (console)** | Did not exist before. Starts the frontend only, with no backend and no Python environment. Required because the console had no independent entry point. |
| 11 | `scripts/launch.sh platform` | **VALID SECONDARY** | Opens an already-running console in a browser. Previously **BROKEN** — see defects below. |
| 12 | `GET /platform/v1/*` on the backend | **VALID SECONDARY (data, not UI)** | `backend/src/routers/platform.py:80`. JSON API consumed by the console UI. |
| 13 | `frontend/app/platform/**` | **CANONICAL (console UI)** | The actual console. `console-state.tsx` shared across 4 pages. Serves at `http://localhost:3000/platform/`. |

### C. Development / environment

| # | Entry point | Class | Evidence |
| --- | --- | --- | --- |
| 14 | `scripts/bootstrap.sh` | **CANONICAL (environment)** | Creates/repairs the single `.venv`, runs `npm ci`, runs `env-doctor.sh`, prints a READY verdict. Own file; mandated by `AGENTS.md` rule 4. |
| 15 | `scripts/launch.sh check-env` | **VALID SECONDARY** | Did not exist before. Read-only environment validation that starts nothing. |
| 16 | `scripts/env-doctor.sh` | **CANONICAL (diagnostic)** | Owned by Agent 1. Called by `bootstrap.sh:108`. Not modified. |
| 17 | `scripts/verify.sh`, `verify-fast.sh`, `freeze-env.sh` | **VALID SECONDARY** | Verification tooling owned by Agent 1. Not startup methods. Not modified. |
| 18 | `.husky/pre-commit` | **VALID SECONDARY** | Git hook, not a startup method. Not modified. |
| 19 | `backend/scripts/scan_test_anti_patterns.py` | **OBSOLETE as a "launcher"** | Static analysis tool; not referenced by any startup path. Left untouched (removal not justified — it is a live tool, merely not a launcher). |

### D. Defects found (all pre-existing, all fixed)

| # | Defect | Class before fix | Proof |
| --- | --- | --- | --- |
| D1 | `check_platform` opened `http://localhost:8000/platform` | **BROKEN** | No such backend route exists. Live: `curl http://localhost:8010/platform` → `HTTP 404 {"detail":"Not Found"}`. The console is a Next.js route; real URL is `http://localhost:3000/platform/`. |
| D2 | `start.sh` ignored all arguments (`exec bash "$LAUNCHER" start`) | **BROKEN** | `./start.sh stop` would have *started* the application. Line 28 of the original file. |
| D3 | `start.bat` passed `"%WSL_SCRIPT_DIR%\scripts\launch.sh"` to `bash` | **BROKEN** | `wslpath` returns a POSIX path; appending backslashes yields a path `bash` cannot resolve. Line 54 of the original file. Not runtime-testable on this Linux host — fixed by construction and documented as such. |
| D4 | Backend readiness gated on `GET /docs` | **BROKEN (semantics)** | `/docs` is a static Swagger page that answers 200 from an open socket. It proved nothing about application usability. Replaced with `GET /ready`, the canonical probe (`backend/src/health.py:38`) which verifies DB + directories and returns 503 until satisfied. |
| D5 | Teardown swept `pgrep -f "next-server\|next start"` machine-wide | **UNSAFE** | Matches *any* Next.js server on the machine regardless of port. Live proof of the hazard: on the first validation run, `stop` was advertised as able to clean up a `next-server` belonging to a **different concurrent agent's worktree**. Replaced with port-scoped, per-PID re-validated matching. |
| D6 | `check_health()` defined with zero callers | **OBSOLETE / demonstrably unreachable** | `grep -n "check_health" scripts/launch.sh` returned only the definition. It also shelled out to bare `python3 -m json.tool`, violating the canonical `.venv` rule in `AGENTS.md`. Removed. |
| D7 | Root `package.json` had no `scripts` key | **OBSOLETE (missing)** | Held only `devDependencies`. Nothing discoverable for operators. Added pure-delegation scripts. |
| D8 | `servers/` was a dangling submodule gitlink | **BROKEN / demonstrably unreachable** | See the cleanup ledger. |
| D9 | Launcher PID files are not gitignored | **cross-owner finding** | `git check-ignore runtime/generated/launcher/state/backend.pid` returns no match; only `*.log` matches (`.gitignore:172`). `.gitignore` is not in my ownership; reported, not edited. |

## What was deliberately NOT deleted

| Item | Reason for keeping |
| --- | --- |
| `scripts/env-doctor.sh`, `verify*.sh`, `freeze-env.sh` | Owned by another agent; live, not obsolete. |
| `frontend/package.json` `dev` script | Real dev workflow with hot reload; a genuinely narrower path, not a duplicate. |
| `.husky/pre-commit`, `tools/**` | Not startup methods. |
| `scripts/bootstrap.sh` | The canonical environment entry point mandated by `AGENTS.md`. |
| `frontend/package.json` `start` script | The primitive the canonical launcher composes. |
| `backend/scripts/scan_test_anti_patterns.py` | A live analysis tool; "not a launcher" is not a reason to delete it. |

No other launcher exists to remove. The competing-"official"-methods problem was
resolved by making `scripts/launch.sh` genuinely canonical and demoting every
other path to a documented wrapper over it.