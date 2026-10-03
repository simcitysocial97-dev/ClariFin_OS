# M10 Agent 4 — Obsolete-Script Cleanup Ledger

**Baseline:** `main @ bfcf336b5b7f46e759c7486f3eb02d0f8d92e14b`
**Rule applied:** nothing is deleted for being old. Every removal requires an
evidence-backed reason from exactly: `unused` | `obsolete` | `duplicate` |
`replaced` | `generated` | `demonstrably unreachable`.

---

## Removals

### 1. `servers/` — submodule gitlink removed

| Field | Value |
| --- | --- |
| **Reason** | **demonstrably unreachable** |
| **Evidence** | See below |

`servers/` was recorded in the index as a gitlink (mode `160000`) pointing at
commit `ada8803def51fe8ec710117e02b034a576fb61c0`. It can never be populated:

```
$ git ls-files -s servers/
160000 ada8803def51fe8ec710117e02b034a576fb61c0 0	servers

$ git cat-file -t ada8803def51fe8ec710117e02b034a576fb61c0
fatal: git cat-file: could not get object info      <- object absent

$ git log --all --oneline -- .gitmodules | wc -l
0                                                   <- no mapping, ever

$ git submodule status
fatal: no submodule mapping found in .gitmodules for path 'servers'
```

Git itself errors on it. The working directory is empty, there is no `.gitmodules`
in the repository or anywhere in its history, and the referenced object is not in
the object database — so no URL can be recovered and no developer can populate
it. History shows it was only ever a pointer: `2cccdac3` added it, `c2304f25`
and `16520c29` moved the pointer.

Impact of removal: `git submodule status` no longer errors for anyone cloning or
working in this repository.

### 2. `check_health()` in `scripts/launch.sh` — function removed

| Field | Value |
| --- | --- |
| **Reason** | **demonstrably unreachable** (+ violating the canonical `.venv` rule) |
| **Evidence** | See below |

The function was defined but never invoked by any command in the dispatch table:

```
$ grep -n "check_health" scripts/launch.sh
1136:check_health() {          <- definition only; zero call sites
```

`cmd_health` was the command actually wired to `health`, so this was orphaned
code. It additionally shelled out to a bare system interpreter, violating
`AGENTS.md` rule 1 ("Always run Python commands through the root `.venv`"):

```bash
curl -s http://localhost:8000/health | python3 -m json.tool   # AGENTS.md violation
```

Keeping it would have left a second, subtly wrong health implementation in the
canonical launcher.

---

## Rewrites (not deletions)

These files were **rewritten, not removed**. Each retained its responsibility and
is cited as the canonical path; the rewrites fixed real defects.

| File | Reason for retention | What changed |
| --- | --- | --- |
| `scripts/launch.sh` | The canonical launcher; declared canonical by `start.sh`, `bootstrap.sh`, `AGENTS.md` | Added environment validation, `/ready` gating, independent `console` command, port-scoped teardown, `check-env`; fixed the console URL; removed unsafe machine-wide sweeps |
| `start.sh` | Canonical Unix entry point | Arguments now forwarded (`./start.sh stop` previously *started* the app) |
| `start.bat` | Canonical Windows entry point | Fixed the WSL path bug (backslash path passed to `bash`) |
| `package.json` | Root manifest; `scripts` key was entirely absent | Added pure-delegation npm scripts |
| `scripts/bootstrap.sh` | Canonical environment bootstrap mandated by `AGENTS.md` | Unchanged — already correct |

---

## Retained deliberately (considered, not deleted)

| Item | Why it stays |
| --- | --- |
| `scripts/env-doctor.sh` | Live diagnostic, called by `bootstrap.sh:108`. Owned by another agent. |
| `scripts/verify.sh`, `verify-fast.sh`, `freeze-env.sh` | Live verification tooling. Not startup methods. Owned by another agent. |
| `frontend/package.json` `dev` | Real hot-reload dev workflow; narrower than canonical, not a duplicate. |
| `frontend/package.json` `start` | The primitive `serve_frontend` composes; removing it would break `npm run build && npm start`. |
| `scripts/launch.sh backend` / `frontend` / `serve` | Genuinely narrower single-component commands, useful for debugging. |
| `.husky/pre-commit` | Git hook. |
| `backend/scripts/scan_test_anti_patterns.py` | A live static-analysis tool. "Not a launcher" is not grounds for deletion. |
| `tools/**` | Development/diagnostic/generator tooling, not startup methods. |
| `[project.scripts] verify` | Verification console script, not an application launcher. |

---

## Found but out of my ownership — reported, not edited

| Finding | Detail | Suggested owner action |
| --- | --- | --- |
| Launcher PID files are not gitignored | `git check-ignore runtime/generated/launcher/state/backend.pid` returns no match; only `*.log` matches (`.gitignore:172`). The launcher writes PID files there, so they surface in `git status`. | Add `runtime/generated/launcher/` to `.gitignore`. I staged explicitly to avoid committing them, but the rule belongs in the tracked file, which is not in my ownership. |
| Pre-existing startup references in docs | `docs/architecture/FRONTEND_BACKEND_RUNTIME_INTEGRATION.md`, `docs/M9-C10-forensic-report.md`, `docs/progress.md` mention `launch.sh`/`uvicorn`/`npm run dev`. | Historical audit reports should stay as-is (they are point-in-time records). The operator-facing contract is `README.md` + `docs/audits/m10-agent4-canonical-startup.md`. |

---

## Net effect

One canonical launcher (`scripts/launch.sh`), two cross-platform entry wrappers
(`start.sh`, `start.bat`), one independent console entry point
(`launch.sh console`), one environment bootstrap (`bootstrap.sh`). No competing
"official" startup method remains, and no multiple-canonical ambiguity is left for
an operator to resolve.