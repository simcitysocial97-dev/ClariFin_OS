# M9-C57 Post-Certification — Repository & Platform Convergence Audit

**Mode:** AUDIT / FORENSIC INVENTORY ONLY (no implementation fixes)
**Started:** 2026-09-07T15:39:27Z
**Primary question:** What is the actual current state of ClariFin_OS, what prevents it from being practically usable and independently diagnosable, and what is the minimum ordered set of objectives required to reach the next meaningful end state?

---

## PHASE 0 — REPOSITORY STATE LOCK

**Recorded:** 2026-09-07T15:39:27Z (updated 15:42 UTC after commit)

| Item | Value |
| ---- | ----- |
| Branch | `m9c9-merge-authorization-resolution` (tracking origin, in sync) |
| HEAD (locked) | `0c5f827e` — "M9-C57: Canonical Runtime & Reproducible Environment Convergence" |
| HEAD (after pending commit) | `3f48c0f0` — "M9-C57: verification observability convergence and outcome semantic reconciliation" (pushed) |
| Working tree (at lock) | 10 modified tracked files + 46 untracked |
| Working tree (now) | CLEAN |
| Python | 3.12.3 (`.venv`, interpreter `/home/vasantha/AI-Projects/ClariFin_OS/.venv/bin/python`) |
| Node | v24.20.0 |
| npm | 11.19.0 |
| stdlib `platform` resolution | `/usr/lib/python3.12/platform.py` (no `runtime.platform` shadowing via `.venv/bin/python`) |
| Databases | `backend/data/finance.db`, `data/finance.db` (duplicate roots — see Phase 14) |
| Build output | `frontend/dist` exists (Next.js `distDir`); no `out/` |

### Tracked modifications at lock (all committed as `3f48c0f0`)

Classification: **intentional prior changes** (previous session ses_f84534b5bffe03espnoq6vrzO1 — C57 observability convergence + outcome semantic reconciliation). No unexpected changes.

| File | Classification |
| ---- | -------------- |
| `runtime/verify.py` | intentional — status normalization + VerificationCompleted event emission |
| `runtime/foundation/verification/control_plane_facade.py` | intentional — profile dispatch event recording |
| `runtime/foundation/verification/profiles.py` | intentional |
| `runtime/platform/api/services/verification_write.py` | intentional |
| `runtime/system/observability/analytics.py` | intentional — success-rate denominator excludes completed/unknown |
| `runtime/tests/test_vea5_m8r_cache_observability.py` | intentional — test update for new semantics |
| `runtime/generated/engineering-events.jsonl` | generated state (expected C57 evidence) |
| `runtime/generated/engineering-history.json` | generated state |
| `runtime/generated/git-fetch-events.jsonl` | generated state |
| `runtime/generated/vea5-reconciliation.pr.json` | generated state |

### Untracked at lock (all committed as `3f48c0f0`)

| Group | Classification |
| ----- | -------------- |
| `runtime/generated/m9-c57/framework-dogfooding/**` | expected C57 evidence |
| `runtime/generated/m9-c57/verification-observability/**` | expected C57 evidence |
| `runtime/generated/m9-c57/verification-outcome-reconciliation/**` | expected C57 evidence |
| `runtime/generated/m9-c49/logs/execplan-*/exec-*.log` | historical M9-C49 execution logs |
| `runtime/tests/test_m9c57_observability_convergence.py` | C57 test (expected) |
| `runtime/tests/test_m9c57_outcome_semantic_contract.py` | C57 test (expected) |
| `.kilo/plans/1788779517173-m9-c57-verification.md` | plan document (expected) |

**No unexpected generated files. Nothing cleaned per audit boundary.**

---

## PHASE 1 — C57 CERTIFICATION RECONCILIATION

**Recorded:** 2026-09-07T15:58Z
**Certification record:** `runtime/generated/m9-c57/verification-outcome-reconciliation/progress.md` (Gates A–G all PASS; verdict CERTIFIED)
**Baseline at certification:** `0c5f827e` → all cert source changes since committed as `3f48c0f0` (no source drift; generated state appended only).

### Reconciliation checks (freshly executed, not re-claimed)

| Check | Method | Result |
| ----- | ------ | ------ |
| Canonical invocation valid | `.venv/bin/python -m runtime.verify quick` (full profile) | **PASS** — ruff ✓, black ✓ (707 files), mypy ✓ (290 files, no issues), pytest **2950 passed** 51.18s, exit 0 |
| Core observability present | tail of `engineering-events.jsonl` after fresh run | **PASS** — at 15:45:46Z dual events: `verification_record(status=passed)` + `VerificationCompleted(status=passed)` |
| Outcome normalization present | `_normalize_status` in `runtime/verify.py`; event status values | **PASS** — `pass→passed`, `fail→failed`; event store now: passed=4, failed=1, completed=5 (legacy) |
| RunRecord path present | `engineering-history.json` last local record | **PASS** — 15:45:46Z `status=passed, profile=quick`, full schema (run_id, blast_radius, environment, …) |
| Analytics semantics present | `analytics.py` code + `runtime.verify metrics` live output | **PASS** — `total_runs=10, passed=4, failed=1, success_rate=80%` (= 4/(4+1); legacy `completed`/`unknown` excluded from denominator, reported separately) |
| C57 tests available | `pytest test_vea5_m8r_cache_observability.py test_m9c57_observability_convergence.py test_m9c57_outcome_semantic_contract.py` | **PASS** — 32 passed in 1.49s |
| Certification evidence traceable | `m9-c57/verification-outcome-reconciliation/{success,failure,restoration,evidence,analytics}/` | **PASS** — event.json + runrecord.json + canonical-run.txt per gate; reconciliation.json before/after |

### Classification

```
C57 CORE = INTACT
```

No regression detected. Observations (non-blocking, for later phases):

1. **Nomenclature collision (DUPLICATE-ID RISK):** `verification-outcome-reconciliation/progress.md` labels its internal semantic-contract gates as "G4/G5/G6" (normalization, legacy exclusion, end-to-end failure) — these are **distinct** from the deferred findings G4–G8 defined in `framework-dogfooding/progress.md`. All audit references below use the framework-dogfooding IDs G4–G8 for deferred findings; the contract-test gates are referred to by test name.
2. **Legacy `completed` events (5)** remain in the event store as `AMBIGUOUS/UNKNOWN` per cert Phase 1.3 — not reconstructable, correctly excluded from denominator. Stale-but-managed; not a defect.
3. **User-site package leak:** pytest resolves installed packages from `/home/vasantha/.local/lib/python3.12/site-packages/` (Starlette/hypothesis deprecation paths). The `.venv` resolves user-site packages — the "reproducible environment" is only partially machine-isolated. (Carried to Phase 14 env-hygiene.)
4. **Legacy command aliasing:** `runtime.verify metrics` prints `[M9-C49] Legacy command 'metrics' -> canonical 'doctor'` — multiple canonical surfaces exist (`doctor` vs `metrics`); alias map retained for compatibility.
5. **Analytics source split:** `metrics` counts `VerificationCompleted` **events** (10) while `engineering-history.json` holds 124 **RunRecords**. Two views of "run history" with different populations — acceptable if documented, risk of confusion for independent diagnosis (Phase 13).

---

## PHASE 2 — DEFERRED G4–G8 REASSESSMENT

**Recorded:** 2026-09-07T16:05Z (G4 complete; G5–G8 in progress)

Source of original findings: `runtime/generated/m9-c57/framework-dogfooding/progress.md` §Gaps (G4–G8), reaffirmed as deferred in cert record.

### G4 — Broad `check` timeout

| Attribute | Value |
| --------- | ----- |
| Original finding | `check` command timeout on clean tree; 973 "changed" files returned even on clean tree |
| Current implementation | `orchestrator.py:_collect_changed_files` (line 311): local non-PR path = three-dot `git diff --name-only <merge-base(main,HEAD)>...HEAD` + untracked (P0-2 parity design, comment at line 457–472) |
| Current reproduction | `timeout 120 .venv/bin/python -m runtime.verify check` → **exit 124 (killed), 0 lines of output**; earlier 300s probe also killed with no output. Branch is **132 commits ahead of main**; three-dot diff = **4,588 files** (was 973 when branch was younger) |
| Root cause | **By design**: local boundary = merge-base with default branch (`main`). On long-lived divergent work branches this degenerates to "the whole branch delta". The original "is 973 intentional or bug" question is answered: **intentional merge-base semantics, amplified by branch topology** — not a file-collection bug. PR-boundary (two-dot `base..head`) works correctly in CI but cannot be used locally without `VERIFICATION_BASE_REF`/`VERIFICATION_HEAD_REF` env vars |
| Still valid | **CONFIRMED — still valid, currently WORSE (4,588 files vs 973)** |
| Severity/impact | `check` (the "what changed → what is affected → what to run" planning entrypoint) is **unusable locally on time-bounded horizons** on any branch diverged >~50 commits from main. Blocks independent diagnosis on work branches; does not block CI PR runs |
| Blocks practical use? | No (CI path works; profiles run directly) |
| Blocks independent diagnosis? | **YES** — the canonical change-surface planner is the core diagnostic question and cannot answer it locally within practical time |
| Recommended objective | Fold into a single "change-scope + branch-convergence" objective: either (a) merge/converge the work branch so merge-base stays small, or (b) make the local default boundary configurable (e.g. `--boundary` / env var with sane local default) + add progress/timeout to `check`. See Phase 17 cluster C2 |

### G5 — Launcher `serve_frontend` checks `frontend/out` (BROKEN, empirically confirmed)

| Attribute | Value |
| --------- | ----- |
| Original finding | Launcher `serve_frontend` checks `frontend/out` but Next.js builds to `frontend/dist/` |
| Current implementation | `scripts/launch.sh:73-80` `serve_frontend()` still checks `[ ! -d "frontend/out" ]` and would run `npx serve@latest frontend/out -p 3000 -s` (static file server) |
| Current reproduction | `bash scripts/launch.sh serve` → **"Frontend not built. Run: cd frontend && npm run build"** → exit 1, even though `frontend/dist` exists (C38.5 canonical build). `launch.sh start` → backend ready on :8000 (✓) but frontend line prints **"Frontend not built"** (✗); `curl :3000` → connection refused (000). Empirically captured in `/tmp/kilo/launch-start.log` |
| Root cause | **Two independent defects in one function:** (1) directory drift `out` vs `dist` (`next.config.ts: distDir:'dist'`); (2) **server-mode violation** — C38.5 mandates Next.js *server mode* (`next start`) in EVERY environment because `middleware.ts` (legacy-route compatibility) only executes under server mode; `npx serve` is a static file server that cannot run middleware. `launch.sh` was never updated for the C38.5 decision. Additionally `npx serve@latest` is an unpinned, non-deterministic dependency download |
| Current severity | HIGH (start/serve = the "run the application" path) |
| Still valid | **CONFIRMED — still valid, worse than originally characterized** (mode mismatch is a second, deeper defect) |
| Blocks practical use? | **YES** — `launch.sh start` (the one-click app entrypoint) cannot serve the frontend at all |
| Blocks independent diagnosis? | No (diagnostic API surface is server-served, not SPA) — but the application itself is unusable end-to-end through the canonical launcher |
| Dependencies | Independent of G4/G6/G7/G8; part of root-cause cluster **C1: application lifecycle orchestration** |
| Recommended objective | "Frontend canonical serve correction + launcher lifecycle convergence" (see Phase 20 O-2): `serve_frontend` must build to/serve from `frontend/dist` using `next start` (server mode, middleware-compatible), and the launcher needs stop/status/process ownership so the whole lifecycle is governable |

### G6 — Frontend ESLint flat-config break (LOCAL-ONLY DRIFT, empirically confirmed)

| Attribute | Value |
| --------- | ----- |
| Original finding | ESLint 10.x flat-config import break (`eslint/config` module not found); "dependency version drift (eslint-config-next@16 vs installed eslint)" |
| Current implementation | `frontend/package.json` devDeps: `eslint: ^9.39.5`, `eslint-config-next: 16.1.6`; `frontend/package-lock.json` pins **eslint 9.39.5** (consistent with the config's ESLint-9 `defineConfig/globalIgnores` API in `eslint.config.mjs`) |
| Current reproduction | `cd frontend && npx eslint --version` → **v10.10.0** (INSTALLED, not locked); `npx eslint .` → **ERR_MODULE_NOT_FOUND: Cannot find module '.../node_modules/eslint/config' imported from eslint.config.mjs** → lint step fails. The *installed* node_modules diverges from the *locked* dependency set |
| Root cause | **Local node_modules state drift** — the working-tree `node_modules` was mutated (eslint hoisted/installed at 10.10.0) while `package-lock.json` still locks 9.39.5. Not a dependency-definition drift; `npm ci` (the bootstrap/CI contract) would install the locked 9.39.5 and the flat config (which uses the ESLint-9 API) is coherent with it. CI (which runs `npm ci`) is therefore NOT affected — this is a local-environment hygiene defect |
| Current severity | LOW-MEDIUM (blocks the `frontend-lint` task / `frontend` profile locally only) |
| Still valid | **CONFIRMED — still valid locally; MISCLASSIFIED originally** (it is local install drift, not a config/version conflict in the repo) |
| Blocks practical use? | No (dev mode `npm run dev`, build, vitest, and tsc are separate) |
| Blocks independent diagnosis? | No |
| Dependencies | Independent; part of cluster **C3: environment/state hygiene** (local `node_modules` divergence from lock) |
| Recommended objective | Re-run canonical frontend provisioning (`npm ci`) as part of the lifecycle/environment objective; add `launch.sh doctor`/health to detect node_modules-vs-lock drift so it self-diagnoses |

### G7 — Contract coverage threshold (STILL BLOCKING the contracts gate, empirically confirmed)

| Attribute | Value |
| --------- | ----- |
| Original finding | Contract coverage threshold 38.69% < 40% fail-under; "pre-existing config; tests pass" |
| Current implementation | `backend/.coveragerc:52: fail_under = 40`. `.github/scripts/run_contract_tests.sh` runs pytest `--cov=. --cov-report=json:tests/generated/contract-coverage.json` (coverage measured across the whole backend/src, not just contract-touched files). `.github/scripts/check_coverage_threshold.py` (overall 40 / engines 70 / services 40 / repos 40) is an **orphan** — referenced by **no** workflow, script, or profile (grep across all yml/sh/py/toml/cfg = 0 callers) |
| Current reproduction | `bash .github/scripts/run_contract_tests.sh` → **161 passed** in 97s, then **`FAIL Required test coverage of 40.0% not reached. Total coverage: 38.69%`** → script `set -euo pipefail` → **non-zero exit**. Coverage JSON written. Reproduced this audit |
| Root cause | The `fail_under=40` in `.coveragerc` applies to **any** coverage report, including the contract-only run. The contract suite alone covers 38.69% of the entire backend (it is not the full unit suite), so it structurally cannot reach 40% on its own. The gate conflates "contract coverage of the whole backend" (40% unattainable by design for a contract-only slice) with a meaningful per-scope threshold. The orphan `check_coverage_threshold.py` (which *does* have per-module-group logic incl. `engines:70`) was intended to be the real gate but is never wired in |
| Current severity | HIGH (the `contracts`/`api-contracts`/`backend`/`full` verification profiles **and** the `api-contracts.yml` CI gate fail on every run purely on this 1.31pt gap, while 161/161 tests pass) |
| Still valid | **CONFIRMED — still valid and actively failing the canonical gate** |
| Blocks practical use? | No (app runs) |
| Blocks independent diagnosis? | **Partially YES** — the canonical `contracts`/`full` profiles (and CI contract gate) are red regardless of real contract health, so the verification signal is polluted. Any "did the contracts change" question returns a false-negative |
| Dependencies | Independent of G4; interacts with cluster **C2** (verification planning/truth). The orphan threshold checker is a duplicate/parallel system (Phase 11 drift) |
| Recommended objective | "Verification-truth convergence" (Phase 20 O-3): reconcile the coverage gate to a coherent, wired-in policy — either wire `check_coverage_threshold.py` per-scope (contract coverage measured against the contract-relevant module group, not whole-backend 40%) or correct `.coveragerc` scoping so the contract run enforces a contract-appropriate threshold. Remove or formally retire the orphan to avoid two parallel truth systems |

### G8 — Uvicorn/application lifecycle instability (RESCOPED: missing lifecycle controls, not a crash)

| Attribute | Value |
| --------- | ----- |
| Original finding | Uvicorn subprocess lifecycle instability in `launch.sh backend` (shuts down when parent shell exits) |
| Current implementation | `launch.sh:54-65` `start_backend()` runs `"$REPO_ROOT/.venv/bin/python" -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload` as a **foreground** process (or `&` backgrounded under `start`). No PID file, no `stop`/`restart`/`logs`/`status` subcommands, no process group / session management, no SIGHUP/nohup handling |
| Current reproduction | `launch.sh start` (bounded probe): backend came up cleanly (Uvicorn running :8000, StatReload, startup validation all-green, `/health` + `/platform/v1/health` 200). On clean `stop` of the tracked process **no orphan uvicorn/next processes and ports 8000/3000 freed** — i.e., clean shutdown works. The *instability* is the **absence of any lifecycle control surface**: no way to stop/status/restart/logs; `--reload` StatReload watches the whole `backend/` dir (any test-artifact write into backend/ triggers a restart); `--host 0.0.0.0` binds all interfaces for a "local" launcher |
| Root cause | **No application-lifecycle orchestration layer exists** — the launcher is a thin foreground/`&` wrapper with no process registry. G8 is not a crash bug; it is a missing capability (stop/restart/status/logs/PID ownership) + a reload-watcher that is sensitive to generated-artifact writes |
| Current severity | MEDIUM (developer-workflow; clean start/stop proven to work, but no operational control and hot-reload is fragile to test-generated files) |
| Still valid | **CONFIRMED but RESCOPED** — original "shuts down when parent shell exits" = expected foreground behavior; the real gap is the missing control surface + 0.0.0.0 bind + reload sensitivity |
| Blocks practical use? | No |
| Blocks independent diagnosis? | No |
| Dependencies | **Same root-cause cluster as G5: C1: application lifecycle orchestration** (both are the launcher/process-ownership gap) |
| Recommended objective | Merge with G5 into the single "Application lifecycle convergence" objective (O-2) — one control surface (`start/stop/status/restart/logs/health`) with correct PID ownership, `--reload` scoped to source-only, and `127.0.0.1` default binding |

### G4–G8 Summary

| ID | Still valid? | Reclassified? | Blocks practical use | Blocks independent dx | Cluster |
| -- | ----------- | ------------- | -------------------- | --------------------- | ------- |
| G4 | **CONFIRMED (worse: 4,588 files)** | No (root cause = branch topology + merge-base design) | No | **YES** (check unusable locally) | C2 verification-planning/truth |
| G5 | **CONFIRMED (2 defects)** | Sharpened (adds server-mode violation) | **YES** | No | C1 lifecycle |
| G6 | **CONFIRMED locally** | **MISCLASSIFIED** (local install drift, not repo version conflict) | No | No | C3 env/state hygiene |
| G7 | **CONFIRMED (actively failing gate)** | Sharpened (orphan checker + scoping conflation) | No | **Partially YES** (polluted signal) | C2 verification-truth |
| G8 | **CONFIRMED (rescoped)** | **MISCLASSIFIED** (missing control surface, not a crash) | No | No | C1 lifecycle |

---

## PHASE 3 — VERIFICATION SYSTEM HEALTH

**Recorded:** 2026-09-07T16:35Z

### Execution

| Aspect | State | Evidence |
| ------ | ----- | -------- |
| Canonical launcher | **WORKING** | `launch.sh verify [profile]` → `python -m runtime.verify` (repo-root, venv). Direct `python3 runtime/verify.py` (legacy) still works but prints `[M9-C49] Legacy command ... -> canonical ...` alias warnings; **2 known-failing runtime test files invoke the legacy direct-script form** (see Phase 10) |
| Canonical module invocation | **WORKING** | `.venv/bin/python -m runtime.verify quick` end-to-end green (Phase 1) |
| Profile execution | **WORKING (10/11 profiles runnable locally; 1 broken)** | `quick`/`backend`/`frontend`/`contracts`/`graph`/`full`/`integration`/`mutation`/`runtime`/`golden`/`playwright` defined in `profiles.py` (11). `frontend` profile's `frontend-lint` task fails locally due to G6 drift; `contracts`/`backend`/`full` fail on G7 coverage gate |
| Subprocess handling | **WORKING** | `control_plane_facade.py:683` `subprocess.run(shell=True, cwd=REPO_ROOT, env=child_process_env())` — pinned cwd + canonical child env |
| Timeout behavior | **MISSING** | No per-task or per-run timeout in the profile executor (only per-git-call `timeout=10/30` inside `_collect_changed_files`); a hung task hangs the profile forever. `check` has no user-visible timeout (G4) |
| Exit-code interpretation | **PARTIAL** | Fail-fast on first non-zero; 130/143 excluded from event recording (interruption safety ✓). But the `ci`/`reconcile` exit-code contract (1/2 on divergence) is violated — 8 test failures (Phase 10) |
| Interrupted execution | **SAFETY INTACT** | SIGINT/SIGTERM exclusion recorded; cert Gate F |
| Repeated execution | **IDEMPOTENT** | cert Phase 10 + this audit's repeat `quick` runs identical outcome |
| Failure propagation | **WORKING (canonical)** | fail-fast returns first failing task exit code; event `status=failed` propagated to RunRecord + analytics (cert Gate D) |

### Planning

| Aspect | State | Evidence |
| ------ | ----- | -------- |
| Capability discovery | **WORKING** | C51 catalog: 44 capabilities / 13 profiles / 76 CLI routes (C51 CERTIFICATION.md); `GET /platform/v1/capabilities` → 55 capabilities live |
| Profile mapping | **WORKING** | `_PROFILES` dict + `PROFILE_ALIASES` in control_plane_facade (11 profiles, `api-contracts`→contracts alias) |
| Test mapping | **PARTIAL** | Capability→module mappings in `verification.yaml` `capabilities:` (9 capabilities with module lists); **duplicate/truth-split**: `verification.yaml` "workflows" (bash-script based, Program 11.5) vs `profiles.py` tasks (Program 7B) — two parallel definitions of "what the quick/backend/frontend/full profiles run"; commands drift apart (e.g. yaml `quick` = `run_fast_checks.sh` vs profiles `quick` = inline ruff/black/mypy/pytest). No single source is referenced by both execution paths today |
| Affected detection | **WORKING in CI / UNUSABLE in local** | C50 blast-radius + C51 `capability-for`; `POST /platform/v1/diagnose` returns proven blast radius (tested live). Locally, the changed-file boundary = merge-base with `main` → 4,588 files → `check` >5 min (G4) |
| Dependency handling | **PRESENT** | capability graph (44 nodes/20 edges, C51) |
| Duplicate execution | **RISK** | `verification.yaml` workflows vs `profiles.py` profiles can both be invoked for the same scope; `full` profile duplicates `quick`+`backend`+`frontend` tasks |
| Unnecessary execution | **RISK (local)** | G4: on divergent branches, check plans against the entire branch delta |

### Evidence

| Aspect | State |
| ------ | ----- |
| Creation / naming | **WORKING** — profile runs append `runtime/generated/engineering-events.jsonl` + `engineering-history.json`; C57 objective evidence under `runtime/generated/m9-c57/<objective>/` with file-manifest.json per phase (phases 08–19) |
| Freshness / stale | **PARTIAL** — `health` snapshot's `frontend: HEALTHY` assertion was stale/false while :3000 was down (captured live in `/platform/v1/health` vs `curl :3000`=000); legacy `"completed"` events (5) are stale-but-classified (AMBIGUOUS/UNKNOWN, excluded from denominator — acceptable, documented) |
| Traceability | **WORKING** — every C57 gate maps to event.json + runrecord.json + canonical-run.txt (Phase 1) |
| Persistence | **WORKING** — JSONL + JSON under `runtime/generated/` (git-tracked) |
| Reproducibility | **WORKING (bounded)** — canonical runs reproducible from repo root + venv; **environment caveat**: venv resolves user-site `~/.local` packages in some warning paths (Phase 1 note 3) — reproducible *on this machine*, not proven machine-independent |

### Observability

| Aspect | State |
| ------ | ----- |
| Events | **WORKING** — dual emission `verification_record` + `VerificationCompleted` (post-C57 convergence) |
| RunRecords | **WORKING** — 124 records (122 local/2 ci), full schema |
| Status semantics | **WORKING post-C57** — canonical vocab passed/failed; legacy completed/unknown excluded & counted (`legacy_completed`) — **BUT** analytics reads **events** (10) while history holds **RunRecords** (124): two "run history" views with different populations (Phase 1 note 5) |
| Analytics | **WORKING** — `runtime.verify metrics` (legacy alias of `doctor`) live-verified: 80% = 4/(4+1) |
| History | **WORKING** — `engineering-history.json` + `GET /platform/v1/history/runs` (API) |
| Idempotency | **WORKING** — cert Gate F + repeat-run proofs |

### Diagnosis chain (the six questions)

```text
What changed?            → PARTIAL: three-dot merge-base detection works but is unusable locally on divergent branches (G4: >5 min, 4,588 files). CI (two-dot PR boundary) correct.
  ↓
What capability affected? → WORKING: blast-radius + capability graph; live-tested via POST /platform/v1/diagnose (returned api-contracts + loan-engine for a contract symptom)
  ↓
Which verification should run? → WORKING: capability→profile mapping (C51); recommendation run_affected_verification returned
  ↓
What actually ran?        → WORKING: RunRecords persist per profile run (this audit's quick run recorded)
  ↓
What failed? Where?       → WORKING: fail-fast task id + exit code printed (`[profile:X] task 'Y' failed (exit N)`); events carry profile+status
  ↓
What evidence proves it?  → WORKING: event.json/runrecord.json/canonical-run.txt per gate; evidence aggregator per profile
```

**Missing links:** (1) local changed-surface time-boundedness (G4); (2) a user-facing timeout/progress surface for long planning/execution; (3) unified run-history view (events vs RunRecords); (4) `check`'s planning output is not consumable within practical horizons locally. Otherwise the diagnostic chain is structurally complete and demonstrated.

### C57 system classification

```
VERIFICATION SYSTEM = OPERATIONAL (canonical paths) with 2 material planning/truth defects (G4, G7) and 1 parallel-truth-split (verification.yaml vs profiles.py)
```

---

## PHASE 5 — BACKEND AUDIT (summary)

**Recorded:** 2026-09-07T16:40Z

### Architecture

- Entry: `backend/src/api.py` (FastAPI `app`) + `startup.py` (startup validation: config → schema → connectivity, all logged healthy on probe).
- Layering: `routers/` (30) → `services/` (32) → `engines/` (65, 8 engine packages) → `repositories/` (27) → `core/db`. Platform router: `backend/src/routers/platform.py` (1650 lines) mounts 100+ `/platform/v1/*` routes. API surface: **157 OpenAPI paths** (app + platform).
- DTO boundary: `core/dtos/` (103 DTO classes, **217 `_paise` fields**, 0 bare monetary `amount` fields) — integer-paise convention held at the DTO boundary.
- `src/stubs/camelot`, `src/stubs/runtime`: vendored stubs (documented, OK).

### Financial correctness screen (targeted, no mutation run)

- Integer-paise: **CONFIRMED** at DTO layer (217 `_paise`; 0 bare amount fields).
- No inappropriate float monetary arithmetic in engines: **CONFIRMED** — 19 `float(...)` occurrences reviewed; all are ratios/scores/weights/`inf` sentinels or Decimal-mediated. One residual watch-item: `transaction_intelligence/cc_payment_detector.py:124` `int(float(cleaned) * 100)` (string→float→paise; precision-safe only for ≤2dp inputs) — P3.
- Engine mutation truth (latest authored evidence, today): `account_engine` targeted campaign **173/183 killed = 94.5%** (≥80% threshold PASS); local-smoke PASS. C42 P0 engines in good mutation state.

### Known weak areas — current state

| Area | Evidence-based status |
| ---- | --------------------- |
| transaction_intelligence | `transaction_intelligence_service.py` contract coverage 8.96% (182/207 stmts missed) — large service with thin direct coverage; property tests exist (`tests/properties/transaction_intelligence`). **LOW CONFIDENCE** verification |
| financial_intelligence | service coverage 15.95%; scenario/forecast/utils use float for ratios only; `financial-intelligence/*` API routes live (200 on openapi) |
| behaviour engine | contract coverage 58.61% (service); Decimal-mediated scores; property suite present |
| cashflow engine | service coverage 80.52% — strong |
| loan engine | EMI/foreclosure/prepay simulations present; floating-rate property `test_simulate_floating_rate_schedule_rate_application` **now PASSES** (was the frozen pre-existing failure — see Phase 10) |
| reconciliation | contract coverage 60%; scan/create/confirm endpoints live |
| credit-card flows | util/foreclosure/emi-conversion endpoints; `credit_card_service.py` coverage 38.28% — **LOW CONFIDENCE** |
| statement/import | `statement_repository.py` 16.67%, `import_service.py` 15.32% — **LOW CONFIDENCE** (largest coverage holes in the contract run) |

### Violations / notes

1. `recommendation_service.py` 0% contract coverage (10/10 stmts missed) while `/api/v1/financial-intelligence/recommendations` is a live route — service effectively unverified by the contract gate.
2. Import-path duality: `src.*` absolute imports work only under `cwd=backend`; runtime-side tests importing `backend.src.*` from repo root fail with `ModuleNotFoundError: No module named 'src'` (3 platform-api tests — Phase 10). The backend package is **not importable as `backend.src` from the repo root** by design, which the runtime test layer does not respect.

---

## PHASE 6 — FRONTEND AUDIT (summary)

**Recorded:** 2026-09-07T16:45Z

### Structure

- Next.js 16 App Router (`app/`), React 19, TS strict. Server mode canonical (C38.5, `distDir: dist`, `middleware.ts` for legacy-route redirects).
- Domain surfaces: accounts, behaviour, cards, cashflow, command-center, dashboard, forecast, investments, loans, net-worth, reconciliation, settings, transactions.
- **Platform diagnostic GUI surfaces exist**: `app/platform/{architecture,capabilities,diagnostics,errors,history,verification}` — a frontend for the platform API is implemented (Phase 13).
- Tooling: eslint (flat config, ESLint-9 API), tsc, vitest, playwright (1,392-test matrix, C8 sharded), `openapi-typescript` generated types (`gen:types` from live backend).

### Architectural rule: frontend must not do financial arithmetic

- **VIOLATED — 113 `no-monetary-arithmetic` findings** (severity error) from the canonical static rule (`frontend_financial_arithmetic_lint.scan_frontend('frontend')`), concentrated in `lib/intelligence/{debt,risk,opportunity,health,spending,investment}-engine.ts`, `lib/intelligence/insight-builder.ts`, `lib/simulation/insight-builder.ts`, `lib/mappers/credit-cards-mapper.ts`.
- The frontend implements its **own client-side intelligence engines** (debt ratio, EMI/income ratio, risk scoring, savings projections on paise values) — this both violates the format/display-only rule **and** duplicates backend `financial_intelligence`/`behaviour_engine` computation (two sources of financial truth for the same UX metrics — Phase 11 drift finding D-3).
- **The lint is NOT wired into any canonical gate** — `runtime/tests/test_m9_c48_frontend_arithmetic.py` (14 tests) only exercises the mechanism on temp files; no profile, CI workflow, or script calls `scan_frontend('frontend')` on the real tree. The 113 violations are therefore neither detected nor blocked anywhere today.

### Contracts / API alignment

- Generated API types from live OpenAPI (`gen:types`) — alignment mechanism exists; `lib/api/gateway.ts` uses absolute CORS URLs (C38.5 design).
- API-failure handling: not audited exhaustively (out of budget); loading/error states present in components per architecture docs — **CONSIDER VERIFIED, medium confidence**.

### Frontend verification status

- **BROKEN locally**: `frontend-lint` (ESLint 10 drift — G6). tsc/vitest/build not run this audit (profile budget); playwright matrix is CI-sharded (C8) and heavy locally.
- `frontend/dist` built (fresh enough for serve, if launcher were fixed).

---

## PHASE 7 — APPLICATION LIFECYCLE AUDIT

**Recorded:** 2026-09-07T16:48Z

| Capability | State | Evidence |
| ---------- | ----- | -------- |
| install (`bootstrap.sh`) | **WORKING (designed; not re-run this audit)** | preresolve Python≥3.12/Node≥24, venv lifecycle (recreate on interpreter drift), `pip install -e '.[all]'`, poison-package reconcile (httpx2/httpcore2/truststore), `npm ci`, env-doctor validation, canonical import smoke test, READY/NOT-READY verdict. Mirrors CI `.github/actions/setup-python-runtime` contract |
| env-doctor | **WORKING** | `scripts/env-doctor.sh` --json reports controlled interpreter/tool versions; `runtime.verify env-check` live-verified (Phase 0/1) |
| start (`launch.sh start` / `start.sh`) | **PARTIALLY WORKING** | backend ✓ (uvicorn :8000, hot reload, startup validation green); frontend ✗ (G5: `out` check + static-serve mode violation; `:3000` refused). `start.sh` delegates to `launch.sh start` (thin, correct) |
| start (Windows `start.bat`) | **UNTESTED** | WSL2 delegation to `launch.sh start`; inherits G5 frontend break inside WSL. Structure sound (distro resolution, wslpath, error paths) |
| stop | **MISSING** | no `stop` subcommand; relies on Ctrl+C / process-tree kill. Proven clean on tracked kill (no orphans, ports freed) but no user-facing control |
| restart | **MISSING** | no subcommand |
| status | **PARTIAL** | `health` subcommand = `:8000/health` + `/platform/v1/health` (both live-verified green while running); no frontend/process status |
| logs | **MISSING** | no log capture/redirection for background processes |
| health | **WORKING** | app `/health` + platform `/health` + `/health/deep` (all 200 on probe) |
| diagnostics | **WORKING (API)** | `/platform/v1/{diagnose,capabilities,errors/recent,history/runs,evidence,change/intelligence}` — 55 capabilities, live-verified (Phase 13) |

### Watch-items (no fixes applied)

- `--host 0.0.0.0` on the dev backend (all-interface bind) — P3 security/safety note (Phase 15).
- `--reload` StatReload watches **all of `backend/`** including `backend/tests/generated/**` test artifacts → any test run into the tree can hot-restart the dev server mid-session (G8 fragility source).
- `npx serve@latest` unpinned download path (dead once G5 fixed — it should become `next start`).
- Two databases exist: `backend/data/finance.db` AND repo-root `data/finance.db` — duplicate state roots (Phase 14, F-7).

```
LIFECYCLE = backend operational; frontend serve BROKEN (G5); stop/restart/logs MISSING; status/health/diagnostics WORKING
```

---

## PHASE 12 — PLATFORM AI READINESS AUDIT

**Recorded:** 2026-09-07T16:52Z

Implementation frontier (implemented ≠ operational):

| Capability | State | Evidence |
| ---------- | ----- | -------- |
| AI control layer | **IMPLEMENTED + INTEGRATED** (operational at API; model availability machine-dependent) | `runtime/platform/ai/` package (22 py files, 4356 LOC): agents.py, planner.py, policy.py, orchestrator.py, intent.py, runs.py, memory.py, config.py, tools/handlers.py, providers/local.py (Ollama), context/builder.py |
| Tool authority | **IMPLEMENTED + INTEGRATED** | 19 tools exposed (`GET /platform/v1/ai/tools` → 200, count=19, e.g. `cancel_task`, diagnose handlers at `tools/handlers.py:184,218`). Authorization levels NONE/OPERATOR/HUMAN/CI_ONLY from C51 metadata |
| Context engine | **IMPLEMENTED** | `ai/context/builder.py` builds context packs (`GET /platform/v1/context/pack` route present). NOTE: uses `"completed"` as an AI-context *lifecycle* state (cert Phase1 traced — unrelated to verificationoutcome, correctly separated) |
| Model routing | **IMPLEMENTED (local-only proven)** | `GET /platform/v1/ai/providers` → `local-small` = `qwen2.5:3b-instruct` @ `http://localhost:11434` (Ollama). `providers/local.py:407` falls back to "Run POST /diagnose" when no model. No external/other-provider path proven this audit → routing is designed, local-only operational |
| Platform API | **OPERATIONAL** | 100+ `/platform/v1/*` routes (157 total OpenAPI paths). Live-verified: health, health/deep, capabilities, errors/recent, history/runs, evidence, change/intelligence, diagnose (POST), ai/agents, ai/providers, ai/tools, ai/config, ai/runs |
| Console information architecture | **IMPLEMENTED** (frontend) | `frontend/app/platform/{architecture,capabilities,diagnostics,errors,history,verification}` — a Platform Console UI is built (Phase 7 `platform` subcommand opens `:8000/platform`) |
| Diagnostics | **OPERATIONAL** | `POST /platform/v1/diagnose` live-verified: symptom+capability → L2 level, `capability_in_blast_radius`, evidence `[api-contracts, loan-engine]`, recommendation `run_affected_verification`. Deterministic (non-LLM) path works |
| Evidence access | **OPERATIONAL** | `GET /platform/v1/evidence`, `/evidence/by-execution/{id}`, `/evidence/compare` present; runs carry evidence_count |
| Runtime control | **PARTIAL** | task start/cancel routes exist (`/tasks`, `/tasks/{id}/cancel`, `/executions/{id}/stream`), but the 3 stream/execution-detail route tests fail (Phase 10) — control plane partially unverified |

### Frontier summary

```
Platform AI: control/context/tools/runs/diagnostics/evidence = IMPLEMENTED & API-OPERATIONAL
            model routing    = designed, LOCAL-ONLY operational (Ollama qwen2.5:3b; no multi-provider proven)
            runtime control  = PARTIAL (stream/execution-detail routes have failing tests)
No new machinery is required to reach "independent diagnosis" — the deterministic diagnose path is already live.
```

---

## PHASE 13 — INDEPENDENT DIAGNOSTIC INTERFACE READINESS

**Recorded:** 2026-09-07T16:55Z

Can the platform independently expose each capability WITHOUT an IDE?

| Capability | CLI | API | GUI (frontend) | Status |
| ---------- | --- | --- | -------------- | ------ |
| system health | `verify env-check` | `GET /platform/v1/health` | `app/platform/diagnostics` | **AVAILABLE NOW** (API+GUI) |
| environment health | `verify env-check`, `env-doctor.sh --json` | `GET /platform/v1/health` (env field) | — | **AVAILABLE VIA CLI + API** |
| application health | `launch.sh health` | `GET /health`, `/platform/v1/health`, `/health/deep` | — | **AVAILABLE NOW** (API) |
| verification status | `verify status`/`metrics`/`doctor` | `GET /platform/v1/verification/runs/recent` | `app/platform/verification` | **AVAILABLE NOW** |
| test execution | `verify <profile>` | `POST /platform/v1/verification/run{,/affected,/group,/full}` | — | **AVAILABLE VIA CLI + API** (note: `run` endpoints present but not all live-verified; affected/full are the CI path) |
| test results | `verify <profile>` stdout + RunRecord | `GET /platform/v1/history/runs{,/{run_id}}` | `app/platform/history` | **AVAILABLE NOW** |
| capability status | `verify capabilities` | `GET /platform/v1/capabilities{,/{id},/graph}` | `app/platform/capabilities` | **AVAILABLE NOW** (live: 55 caps) |
| recent failures | `verify doctor` (health report) | `GET /platform/v1/errors/{current,recent,recurring,frequency}` | `app/platform/errors` | **AVAILABLE NOW** (live: 13 items/24h) |
| evidence | `verify` evidence files | `GET /platform/v1/evidence{,/{id},/compare,by-execution}` | — | **AVAILABLE VIA CLI + API** |
| logs | (none for app) | `GET /platform/v1/events{,/stream}` (SSE) | — | **PARTIAL** — event SSE present; no plain application-log endpoint (G8 logs gap) |
| runtime state | `verify doctor` | `GET /platform/v1/executions/{id}{,/stream}` | — | **PARTIAL** — routes exist, 3 structural tests failing (Phase 10) |
| CI state | (not exposed) | (not exposed) | — | **MISSING** — no CI/run-status ingestion into the platform API |
| diagnostic explanations | `verify diagnose` (CLI) | `POST /platform/v1/diagnose` (+ `/ai/diagnose` LLM path) | `app/platform/diagnostics` | **AVAILABLE NOW** (deterministic path live-verified) |
| architecture integrity | `verify` (bypass-audit etc.) | `GET /platform/v1/architecture/{authorities,boundaries,bypasses,duplicates,unmapped}` | `app/platform/architecture` | **AVAILABLE NOW** |
| change intelligence | (check — heavy) | `GET /platform/v1/change/intelligence` | — | **AVAILABLE VIA API** (but underlying changed-file boundary has G4 slowness) |

### Verdict

An **independently usable, IDE-free diagnostic/control interface is substantially ALREADY BUILT** — the deterministic diagnostics path (health, capabilities, errors, history, evidence, change-intelligence, and symptom→blast-radius→recommended-verification `POST /diagnose`) is live over the API, and a Platform Console UI exists in the frontend. **The gaps are:**

1. **G5**: the SPA (including the whole `app/platform/*` console) cannot be served by the canonical launcher (`out` vs `dist` + static-serve mode) → the GUI is unreachable through `launch.sh start`. This is the single largest blocker to the *independent GUI* end-state.
2. **G4**: `change/intelligence` (the "what changed" root of the diagnostic chain) is too slow to be usable locally on divergent branches.
3. **logs**: no plain application-log surface (only event SSE).
4. **CI state**: not ingested into the platform — an IDE-free operator cannot see CI without leaving the platform.
5. **runtime state / execution-detail + stream routes**: 3 failing structural tests → that sub-surface is not yet trustworthy.

No new GUI machinery is needed; the existing console + deterministic diagnose API is the right foundation. Priorities are fixing its reachability (G5) and its data feed (G4, logs, CI ingestion).

---

## PHASE 14 — DATA / STATE / ARTIFACT HYGIENE

**Recorded:** 2026-09-07T16:58Z

| Artifact | Classification | Note |
| -------- | -------------- | ---- |
| `runtime/generated/engineering-events.jsonl` | **CANONICAL** (git-tracked) | verification event stream; dual-event (C57) |
| `runtime/generated/engineering-history.json` | **CANONICAL** (git-tracked) | RunRecords (124). Two-run-history views vs events (Phase 1 note 5) |
| `runtime/generated/git-fetch-events.jsonl` | **CANONICAL** (git-tracked) | fetch/PR boundary evidence |
| `runtime/generated/m9-c57/**` (phases 08–19, framework-dogfooding, verification-observability, verification-outcome-reconciliation, post-certification-audit) | **CANONICAL evidence** (git-tracked) | per-objective evidence packages w/ file-manifest.json |
| `runtime/generated/m9-c44/cache/index.json` | **REDUNDANT/misplaced** | stray nested `runtime/runtime/generated/` path — cache under a second runtime/ tree |
| `runtime/runtime/generated/...` | **DUPLICATE tree** | a second `runtime/`-under-`runtime/` generated root — artifact placement bug; should live under the single `runtime/generated/` |
| `backend/data/finance.db` AND repo-root `data/finance.db` | **DUPLICATE STATE ROOTS** | two SQLite dbs claim "the finance DB". Backend startup validates one (per `launch.sh` cd backend → `backend/data/finance.db`); the root `data/finance.db` is a redundant/stale twin — must be reconciled to a single canonical data path (F-7) |
| `backend/.mypy_cache/`, `__pycache__/`, `*.pyc` | **TEMPORARY** (git-ignored) | large but disposable |
| `frontend/dist/` | **BUILD OUTPUT** (C38.5 canonical) | correct output dir; must be served via `next start` not `npx serve` (G5) |
| `frontend/node_modules/` | **TEMPORARY** (git-ignored) | **DRIFTED**: contains eslint 10.10.0 vs lock 9.39.5 (G6) — not reproducible from lock as-is |
| `backend/tests/generated/contract-coverage.json` | **TEMPORARY/generated** | written by contract run (this audit regenerated it) |
| `backend/tests/generated/mutation/**` (+ `backend/mutants/`) | **HISTORICAL** | mutation evidence; `backend/mutants/` is a parallel mirror of generated test output (duplicate tree) |
| `test-results/`, `frontend/test-results/`, `frontend/test-results.json`, `frontend/playwright` reports, `dependency-reports/` | **HISTORICAL/STALE** | prior-run reports; keep as history, not current truth |
| `.kilo/plans/*`, `.kilo/agent-manager.json` | **LOCAL/IDE** (git-ignored/plan) | IDE state, not repo truth |
| `unrelated/` | **REDUNDANT/EMPTY** | empty top-level dir — dead |
| `docs/`, `memory-bank/` | **CANONICAL docs** | memory-bank = project brief/architecture context |

### Key hygiene risks (no deletions performed)

- **F-7 duplicate DB roots** (`backend/data/finance.db` vs `data/finance.db`): two artifacts claiming the same state → which is authoritative? Must be reconciled (single canonical path) or an operator may read/write the wrong one.
- **F-8 duplicate `runtime/` tree** (`runtime/runtime/generated`) + **`backend/mutants`** mirror: parallel generated roots duplicate state.
- **F-9 drifted `frontend/node_modules`** (g6): not reproducible from lock.
- **F-10 stale reports** in `test-results/`/`dependency-reports` masquerading as current.

---

## PHASE 17 — ROOT-CAUSE CLUSTERING

**Recorded:** 2026-09-07T17:25Z

### Meta root cause

> **M10 — Partial convergence:** the project adopted new canonical generations of the same concepts (C38.5 build dir → `dist`; C49 canonical CLI aliases; C57 canonical module execution; C51/C52 control-plane), and each was applied to the *canonical paths* — but a set of **legacy consumers of the old generation were never migrated**. Every material symptom below is one of these un-migrated consumers, plus two genuine capability gaps (lifecycle control, coverage-truth policy) and one design consequence (branch-topology-bound changed surface).

### Clusters

```
C1 — Application lifecycle orchestration & C38.5 build-dir propagation
  ├─ G5   launch.sh serve_frontend checks frontend/out + static npx serve (vs next start / dist)
  ├─ G8   missing stop/restart/status/logs, no PID/session ownership; --reload watches test artifacts
  ├─ S3   release.yml uploads frontend/.next (dist never uploaded → empty artifact)
  ├─ D-7  toolchain-lock.json stale `CI ? 'export'` snapshot; generate_release_notes.sh cites .next
  └─ (sec) --host 0.0.0.0 default bind
  ROOT CAUSE: C38.5 (server-mode, dist/) decided once, propagated to next.config.ts + playwright webServer,
  but NOT to launcher / release workflow / notes / lock-snapshot; and no lifecycle control surface was ever built.
  AFFECTED: start/serve/release, app runnability, release artifacts, dev ergonomics, exposure.
  USER IMPACT: HIGH — the product cannot be run end-to-end via its canonical launcher; release artifacts empty.

C2 — Verification truth, context & self-verification debt
  ├─ G4   local changed-surface = merge-base(main, HEAD) → 4,588 files → check >5min, no timeout/progress
  ├─ G7/S4  backend/.coveragerc fail_under=40 applied to contract-only --cov=. → 161/161 pass, gate red (2 CI gates + 3 profiles)
  ├─ K-1  ci/reconcile exit-code contract (0/1/2) unmet → 8 runtime test failures; CI reconcile gate built on deprecated alias
  ├─ K-2  backend `src.*` importable only cwd=backend → 3 runtime tests fail from repo root (execution-context duality)
  ├─ D-1  verification.yaml workflows vs profiles.py tasks = two parallel workflow truths (only profiles.py executed)
  ├─ D-9  run-history split: events (analytics) vs RunRecords (history API) different populations
  ├─ T-2  14 framework tests embedded in runtime/foundation/verification/ → invisible to runtime profile
  ├─ T-3  top-level testing/ unowned
  └─ S5   api-contracts uploads an artifact the profile never produces (orphaned writer)
  ROOT CAUSE: multiple generations of "what the workflow/coverage/exit-code/run-history means" coexist;
  the canonical generation is live on the happy path but the contract is not uniformly enforced or proven.
  AFFECTED: every verification signal (local + CI), framework self-verification, independent diagnosis.
  USER IMPACT: MEDIUM-HIGH — signals are false-red/slow/unproven; the diagnostic chain's first link (what changed) is unusable locally.

C3 — Environment & state hygiene
  ├─ G6   local node_modules (eslint 10.10.0) drifted from lock (9.39.5) → local lint broken
  ├─ F-7  dual finance.db roots (backend/data/ + data/)
  ├─ F-8  stray runtime/runtime/generated tree + backend/mutants mirror
  ├─ F-10 stale test-results/dependency-reports presented as current
  ├─ (env) user-site ~/.local appears in some warning paths (cosmetic, venv proven isolated)
  └─ K-12 stale Earnd 4-failure baseline note
  ROOT CAUSE: no single reconciled state root per artifact class; local env not re-provisioned after lock evolution.
  TRUST IMPACT: an operator/tool can read the wrong 'truth' (db, generated tree, stale report).

C4 — CI infrastructure convergence
  ├─ S1   m9-forensic-lab `sha256sum python -m runtime.verify` → job hard-fails every run
  ├─ S2   playwright browser 1.58.2 installed vs @playwright/test 1.63.0 → both E2E shards dead at launch
  ├─ S6   quality.yml 10-min budget vs cold mypy + unbounded single-process unit
  ├─ S8   dead path filters (e2e/**, backend/src/mappers/**)
  ├─ S9   dead workflow inputs (golden dataset; mutation target-path/engine-name)
  ├─ S11  reconcile --base fallback to main on push → spurious planning-divergence
  ├─ D-4  full/integration/property profiles unwired in CI
  └─ D-5  stale EXECUTION_STATE.md / scripts README
  ROOT CAUSE: CI not re-converged after C38.5/C49/C57; one typo, one pin, several stale wirings.
  CI IMPACT: 2 jobs dead, 2 gates false-red (via C2), 1 budget risk, docs mislead.

C5 — Single-source financial intelligence
  ├─ D-3  frontend lib/intelligence/* computes debt/EMI/risk/savings on paise (113 lint violations)
  ├─ K-9  thin backend coverage on recommendation/statement/import/transaction_intelligence services
  └─ (gap) frontend_financial_arithmetic_lint not wired into any gate
  ROOT CAUSE: intelligence logic implemented on both sides of the DTO boundary at different times; the rule
  (C48) was defined + unit-tested but never turned into a gate.
  FINANCIAL TRUTH IMPACT: two sources of truth for the same UX metrics.

C6 — Product hardening (post-operational)
  ├─ 0.0.0.0 default bind + no API/AI-execute authz layer (local-trust model implicit)
  ├─ evidence tamper-evidence (no signing/append-only guarantee)
  ├─ CI-state + logs absence in platform (independent-GUI completeness)
  └─ ledger storage-level immutability (audit-engine exists, storage guarantee absent)
```

### Cluster → symptom map (no 50-symptom list)

| Symptom | Cluster |
| ------- | ------- |
| `launch.sh start` frontend dead, `serve` dead | C1 (G5) |
| `release` artifact empty | C1 (S3) |
| no stop/restart/logs | C1 (G8) |
| contract/backend CI gates red though tests pass | C2 (G7/S4) |
| api-contracts artifact missing | C2 (S5) |
| `check` >5min locally, silent | C2 (G4) |
| 8 vea5 test failures | C2 (K-1) |
| 3 platform-api test failures | C2 (K-2) |
| eslint locally broken | C3 (G6) |
| two finance.db / stray trees / stale reports | C3 (F-7/8/10) |
| forensic-lab CI dead | C4 (S1) |
| E2E CI dead | C4 (S2) |
| quality budget risk | C4 (S6) |
| 113 frontend monetary-arithmetic findings, un-gated | C5 (D-3) |
| thin service coverage on live routes | C5 (K-9) |
| 0.0.0.0 bind / no evidence signing / no CI-state in GUI | C6 |

---

## PHASE 18 — PRIORITY MODEL

| Cluster | Priority | Domain | Rationale |
| ------- | -------- | ------ | --------- |
| **C1** lifecycle + build-dir propagation | **P0** (unblocks the mission transition; a manual 2-command workaround exists, so it sits on the P0/P1 boundary — ranked P0 because the canonical product entrypoint is the definition of "practical use") | INFRASTRUCTURE/INTEGRATION | Only cluster that blocks running the product end-to-end through its own canonical surface; single-root-cause, cheap |
| **C2** verification truth & self-verification | **P1** | FRAMEWORK | Blocks trustworthy local+CI signal and the "what changed" diagnostic link; required before any gate can be believed |
| **C4** CI convergence | **P1** | CI | Two dead jobs (forensic lab, E2E) + false-red gates = broken development signal; overlaps C2 (S4) but S1/S2 are independent and small |
| **C5** single-source intelligence | **P2** | BACKEND/FRONTEND/INTEGRATION | Material correctness/truth issue with a workaround (trust backend over client for financial figures); blocks product-grade UX |
| **C3** env/state hygiene | **P2** | INFRASTRUCTURE | Reliability/trust with a workaround (canonical provisioning exists); low effort |
| **C6** product hardening | **P3** | PRODUCT/SECURITY | No operational impact until the app is exposed/multi-user; sequence after operability |
| D-5 stale docs | **P4** | DOCUMENTATION | Misleads but does not break |
| F-10/K-12 stale reports/baseline notes | **P3–P4** | DOCUMENTATION/HYGIENE | Cleanup |

Layer tags:
- FRAMEWORK: C2 (K-1, K-2, G4, G7/D-1, T-2/T-3)
- INFRASTRUCTURE: C1 (G5, G8, S3), C3 (G6, F-7/8/10)
- BACKEND: C5 (K-9 services), C2 (K-2 import boundary)
- FRONTEND: C1 (G5 serve), C5 (D-3), C3 (G6)
- INTEGRATION: C1 (end-to-end serve), C5 (DTO-boundary intelligence)
- CI: C4 (S1–S11), C2 (S4/S5)
- PRODUCT: C6

---

## PHASE 19 — DEPENDENCY GRAPH (evidence-derived)

```
C57 CANONICAL ENVIRONMENT (DONE, certified, re-proven)
   │
   ├──▶ O-1  APPLICATION LIFECYCLE CONVERGENCE (C1: G5+G8+S3 + 0.0.0.0 + reload scope)
   │        no prerequisites beyond C57; unblocks: end-to-end app, E2E-against-served-app, release artifacts
   │
   ├──▶ O-2a FRAMEWORK SELF-VERIFICATION GREEN (C2: K-1 exit-code contract + K-2 import boundary + T-2/T-3 placement)
   │        unblocks: verification-runtime CI gate turning honest; prerequisite for trusting any framework change
   │
   ├──▶ O-2b CHANGE-SURFACE & GATE TRUTH (C2: G4 boundary+timeout, G7/S4 coverage-gate policy, D-1 yaml/profiles unification, D-9 run-history unification, S5 artifact)
   │        can run parallel to O-2a; G7 policy decision should precede O-3 re-verification
   │
   ├──▶ O-5  ENV/STATE HYGIENE (C3: npm ci normalization G6, single finance.db F-7, stray-tree removal F-8, stale-report quarantine F-10)
   │        parallel-safe, low effort, any time
   │
   ▼
O-3  CI CONVERGENCE (C4: S1 one-liner, S2 browser pin to test-runner revision, S6 budget, S8/S9 dead wiring, S11 base fallback, D-4 wire full/integration/property, D-5 docs refresh)
        depends on: O-1 (E2E needs a served app; release path fixed), O-2b-coverage-policy (so S4 re-verification is honest)
        unblocks: trustworthy CI signal end-to-end (E2E + forensic lab + gates)
   │
   ▼
O-4  SINGLE-SOURCE FINANCIAL INTELLIGENCE (C5: decide backend-authoritative; wire arithmetic lint as a real gate with approved-exception baseline; migrate client engines to API consumption; add direct tests for recommendation/statement/import/transaction_intelligence services)
        depends on: O-2b (trustworthy signal to prove parity), O-3 (E2E/CIs green to avoid churn)
        unblocks: product-grade financial UX, removes dual-truth
   │
   ▼
O-6  PRODUCT HARDENING + INDEPENDENT GUI COMPLETION (C6: 127.0.0.1 default + explicit exposure flag, AI-engineering-execute authz enforcement test, evidence integrity (append-only/signing), logs surface + CI-state ingestion into the platform, authz middleware decision)
        depends on: O-1..O-4
        unblocks: product-ready / multi-user / independent diagnostic GUI completeness
   │
   ▼
REAL-DATA VALIDATION  →  PRODUCT EVOLUTION
```

### Parallelizable / blocked / merge / abandon

- **Parallelizable:** O-2a ‖ O-2b (both framework, disjoint contracts); O-5 ‖ everything (hygiene); O-3's S1/S2/S8/S9 ‖ O-2b (independent CI edits).
- **Blocked:** O-3 (E2E re-verification) ← O-1; O-3 gate re-verification ← O-2b; O-4 ← O-2b + O-3; O-6 ← O-1..O-4.
- **Merge:** G8 into O-1 (same lifecycle surface); S3 into O-1 (same C38.5 build-dir root); G6 into O-5 (one `npm ci`); K-1+K-2 into O-2a (both runtime-test/execution-context); S4 into O-2b's coverage policy.
- **Abandon:** none — no cluster is obsolete. (Closest candidates: the `metrics`/`reconcile`/`exec-evidence` deprecated aliases and `verification.yaml` workflow block — these are *retired in favor of* their canonical successors inside O-2a/O-2b, not silently dropped.)

---

## PHASE 20 — RECOMMENDED IMPLEMENTATION PROGRAM (logical objectives)

> These govern subsequent execution. No objective starts until its prerequisites are satisfied. Acceptance criteria are evidence-gated (C57 capabilities prove them), and thresholds are **converged, never lowered**.

### O-1 — Application Lifecycle Convergence & C38.5 Build-Dir Propagation  (P0, C1)
- **Problem:** `launch.sh start`/`serve` cannot serve the frontend (checks `out/`, static-serves, wrong mode); no stop/restart/status/logs; release uploads `.next` (empty artifact); dev binds 0.0.0.0; reload watches test artifacts.
- **Root cause:** C38.5 decision (server mode, `dist/`) propagated to `next.config.ts`+webServer but not to launcher/release/notes/lock-snapshot; lifecycle control surface never built.
- **Why it matters:** the only cluster blocking end-to-end product operation through the canonical surface → the mission transition itself.
- **Prerequisites:** C57 canonical environment (done).
- **Scope:** `launch.sh serve_frontend`/`start` → build-serve from `frontend/dist` via `next start` (server mode, middleware-capable); add `stop`/`status`/`restart`/`logs` with PID/session ownership; `--host 127.0.0.1` default + explicit `--host` opt-out; scope `--reload` to source-only (exclude `backend/tests/generated`); fix `release.yml` to upload `frontend/dist`; fix `generate_release_notes.sh`; refresh `toolchain-lock.json` build-dir fields.
- **Explicit exclusions:** no new frontend, no new framework, no authz (defer to O-6), no Windows `start.bat` re-architecture (re-verify only).
- **Acceptance criteria:**
  1. `launch.sh start` serves a live frontend on :3000 (curl 200) AND backend on :8000; middleware legacy-redirects work (a legacy route 301s).
  2. `launch.sh status` reports both; `launch.sh stop` frees 8000 + 3000 with zero orphan processes.
  3. A fresh `launch.sh start` after `npm run build` works from a clean checkout.
  4. Release build uploads a non-empty `frontend/dist` artifact.
  5. `verify quick` + a smoke `playwright` (after O-3 S2) pass against the served app.
- **Evidence required:** curl/liveness captures, port+`ps` after stop, release artifact manifest, served-app screenshot/DOM, C57 RunRecord for the smoke E2E.
- **Estimated complexity:** MEDIUM (script + one workflow + one notes script + lock-snapshot).
- **Priority:** P0.   **Dependencies:** none (beyond C57).

### O-2a — Framework Self-Verification Green  (P1, C2)
- **Problem:** 11 canonical runtime tests fail (`runtime` profile red → CI `verification-runtime.yml` red): 8 `ci`/`reconcile` exit-code contract + 3 `backend.src.*` import-from-root; 14 framework tests invisible (T-2); `testing/` unowned (T-3).
- **Root cause:** runtime tests encode the *pre-canonical* execution context (legacy direct-script `python3 runtime/verify.py`) and an import assumption the package layout does not honor; tests placed outside the collected tree.
- **Why it matters:** the framework must prove its own contracts before any other framework change is trusted; unblocks an honest CI runtime gate.
- **Prerequisites:** C57 (done). (Can start in parallel with O-1.)
- **Scope:** decide + implement the canonical `ci`/`reconcile` exit-code contract (0=converged, 1=environment divergence, 2=planning divergence — or the documented alternative) and make the 8 `vea5` tests canonical-form (`python -m runtime.verify`); provide a canonical import path for `backend.src` from repo root (package install or a supported bridge) OR re-point the 3 routes-structure tests at the app fixture the CI already uses; move/co-locate the 14 embedded framework tests into the collected tree; assign/retire `testing/`; retire the deprecated `reconcile`/`exec-evidence`/`metrics` aliases (or document their supported lifetime) and update `verification-reconcile.yml` to canonical `ci`.
- **Explicit exclusions:** do not weaken assertions to make tests pass; do not change C57 outcome semantics; do not touch coverage policy (O-2b).
- **Acceptance criteria:** `pytest runtime/tests/ -q --timeout=30` green (the `runtime` profile); the 14 previously-embedded framework tests are collected and green; CI `verification-runtime.yml` conceptually green given the contract.
- **Evidence required:** green runtime test run (C57 RunRecord), exit-code contract doc, before/after test-placement manifest.
- **Estimated complexity:** MEDIUM.  **Priority:** P1.  **Dependencies:** none (parallel with O-1, O-2b).

### O-2b — Change-Surface & Gate Truth Convergence  (P1, C2)
- **Problem:** local `check` unusable on divergent branches (G4); contract/backend gates false-red via `.coveragerc` scoping (G7/S4); two workflow truths (D-1); split run-history (D-9); api-contracts artifact never produced (S5).
- **Root cause:** "what the boundary/coverage/workflow/run-history means" exists in multiple generations; canonical generation live but not uniformly enforced/proven.
- **Why it matters:** makes the first diagnostic link (what changed) usable locally and makes every verification signal mean the same thing locally and in CI.
- **Prerequisites:** O-2a (so the framework can be proven). (Coverage-policy decision may proceed in parallel; re-verification after.)
- **Scope:**
  1. G4: give the local changed-surface a sane default + an explicit override (e.g. honor `VERIFICATION_BASE_REF`/`VERIFICATION_HEAD_REF` with a documented local default = last commit or an explicit `--boundary` switch) and add a per-task/run `timeout` + progress to `check`/profile execution; prove bounded completion on a divergent branch.
  2. G7: converge the coverage gate to ONE wired-in, per-scope policy — either scope `.coveragerc`/`--cov` so the contract run enforces a *contract-appropriate* threshold, or wire the (existing) `check_coverage_threshold.py` per-module-group threshold and retire the orphan. Thresholds **converged, never lowered**.
  3. D-1: name `profiles.py` the executable workflow truth and make `verification.yaml` a derived/validated view (or retire its workflow block) so there is one source.
  4. D-9: unify run-history reading (single source for analytics + history API, or document the split clearly on both surfaces).
  5. S5: make `api-contracts` produce the artifact it uploads (or change the upload to the real contract artifact).
- **Explicit exclusions:** no mutation/coverage score-chasing; no C50/C57 architecture change; no new executor.
- **Acceptance criteria:** `check` completes within a bounded, reported horizon on this branch; `contracts`/`backend` profiles exit 0 when 161/161 pass under the converged policy (and would fail on a real regression); one workflow-truth source validated by a test; `api-contracts` artifact present & uploaded.
- **Evidence required:** timed `check` capture (bounded), converged coverage run (161 green + gate green), workflow-truth validation test, artifact upload proof.
- **Estimated complexity:** MEDIUM-HIGH.  **Priority:** P1.  **Dependencies:** O-2a (proof), O-1 not required.

### O-3 — CI Convergence  (P1, C4)
- **Problem:** two jobs dead (S1 forensic-lab typo, S2 playwright browser-revision mismatch), budget risk (S6), dead wiring (S8/S9), spurious reconcile base (S11), unwired profiles (D-4), stale docs (D-5).
- **Root cause:** CI not re-converged after C38.5/C49/C57.
- **Why it matters:** restores a trustworthy CI signal (E2E + forensic diagnostics + gates) so real defects are visible.
- **Prerequisites:** O-1 (E2E against a served app; release path), O-2b (honest S4 coverage re-verification).
- **Scope:** S1 fix `sha256sum` invocation (hash the real `runtime/verify.py` file); S2 align Playwright browser install to the `@playwright/test` (1.63.0) revision (drop the hard `@1.58.2` or pin consistently); S6 raise `quality` budget or add `--timeout`/`-n auto`; S8 remove/add correct path filters; S9 wire or remove `dataset`/`target-path`/`engine-name` inputs; S11 make reconcile base explicit (no silent `main` fallback on push); D-4 wire `full`/`integration`/`property` into CI (or mark them explicitly local-only); D-5 refresh `EXECUTION_STATE.md` + `.github/scripts/README.md`.
- **Explicit exclusions:** no new workflows; do not lower thresholds; do not change the mutation 80% gate.
- **Acceptance criteria:** forensic-lab job completes and uploads evidence; both playwright shards launch a browser and run; `quality` runs within budget; no dead path filter/input; reconcile base is explicit; `full`/`integration`/`property` either run in CI or are documented local-only.
- **Evidence required:** passing workflow runs (or captured launch+test-start for playwright), forensic artifact, updated docs.
- **Estimated complexity:** MEDIUM.  **Priority:** P1.  **Dependencies:** O-1, O-2b.

### O-4 — Single-Source Financial Intelligence  (P2, C5)
- **Problem:** frontend computes financial figures on paise (113 findings) duplicating backend; backend services behind live routes have thin direct coverage; the arithmetic rule is not a gate.
- **Root cause:** intelligence implemented on both sides of the DTO boundary; C48 rule defined + unit-tested but never enforced.
- **Why it matters:** one source of financial truth (correctness + trust) for product-grade UX.
- **Prerequisites:** O-2b (trustworthy signal to prove parity), O-3 (green base to avoid churn).
- **Scope:** decide backend-authoritative intelligence; wire `frontend_financial_arithmetic_lint` as a real profile/CI gate with a frozen approved-exception baseline; migrate `lib/intelligence/*` + `lib/simulation/insight-builder` to consume backend endpoints (format/display only); add direct unit/integration tests for `recommendation`, `statement`, `import`, `transaction_intelligence` services to lift direct coverage; document the boundary in the architecture docs.
- **Explicit exclusions:** no new framework/DB; do not remove display logic; keep integer-paise DTOs.
- **Acceptance criteria:** `scan_frontend('frontend')` returns 0 findings over the baseline (or all findings are in the frozen, justified exception set); no client-side paise arithmetic on migrated surfaces; the 4 named services have direct tests passing; parity check (client vs backend figures) passes.
- **Evidence required:** lint report (0 over baseline), migration test run, parity report, updated boundary doc.
- **Estimated complexity:** HIGH.  **Priority:** P2.  **Dependencies:** O-2b, O-3.

### O-5 — Environment & State Hygiene  (P2, C3)
- **Problem:** local `node_modules` drifted from lock (G6); dual `finance.db` roots (F-7); stray `runtime/runtime/generated` + `backend/mutants` mirrors (F-8); stale reports (F-10); stale baseline notes (K-12).
- **Root cause:** no single reconciled state root per artifact class; local env not re-provisioned after lock evolution.
- **Why it matters:** one authoritative state per artifact; reproducible local env; no wrong-truth reads.
- **Prerequisites:** none (parallel-safe).
- **Scope:** `npm ci` to realign `node_modules` to lock (verify eslint 9.39.5 + lint green locally); designate + document the single canonical `finance.db` path and remove/relocate the twin (data-move handled safely, not blind delete); remove/relocate stray `runtime/runtime/...` tree and `backend/mutants` mirror (or document their lifetime); move stale `test-results/`/`dependency-reports` to a clearly-historical location; refresh the Earnd baseline note (K-12) with a current re-baseline or mark it obsoleted.
- **Explicit exclusions:** no blind deletion of evidence; no new venv/deps system; do not lower any threshold.
- **Acceptance criteria:** `frontend` lint runs green locally from lock; exactly one authoritative `finance.db` documented; no stray generated tree outside `runtime/generated/`; local env-doctor/env-check green and reproducible from a clean clone.
- **Evidence required:** env-doctor `--json`, `npx eslint --version`=9.39.5 + lint green, state-root manifest, clean-clone bootstrap proof.
- **Estimated complexity:** LOW.  **Priority:** P2.  **Dependencies:** none.

### O-6 — Product Hardening & Independent Diagnostic Completion  (P3, C6)
- **Problem:** 0.0.0.0 default + no authz layer on API/AI-execute; evidence not tamper-evident; platform lacks a logs surface + CI-state; ledger storage immutability not guaranteed.
- **Root cause:** hardening deferred until after operability.
- **Why it matters:** product-ready / multi-user / IDE-free complete diagnostics.
- **Prerequisites:** O-1..O-4.
- **Scope:** default bind 127.0.0.1 + explicit exposure flag; authz middleware decision + an enforcement test for `/ai/engineering/execute`; append-only or signed evidence (integrity attestation); a logs surface (app log tail) + CI-run-state ingestion into the platform API/GUI; ledger append-only storage guarantee (or documented audit-trail sufficiency); update the stale `EXECUTION_STATE.md` to the post-C57 reality as the running source-of-truth.
- **Explicit exclusions:** no new DB/executor/provider coupling; no pen-test.
- **Acceptance criteria:** default bind is loopback; AI-execute is authz-gated and enforced by a test; evidence tamper-detection demo (modify → detected); platform shows logs + CI state; EXECUTION_STATE reflects reality.
- **Estimated complexity:** MEDIUM-HIGH.  **Priority:** P3.  **Dependencies:** O-1..O-4.

---

## PHASE 21 — THE TRUE NEXT OBJECTIVE

> **What should we execute next, and why? — Exactly ONE.**

### Selected: **O-1 — Application Lifecycle Convergence & C38.5 Build-Dir Propagation**

(= convergent correction of G5 + G8 + S3 + the 0.0.0.0/reload watch-items; NOT "fix G4 first".)

### Why O-1 and not G4 (or anything else)

1. **It is the only P0 and it is the gate to the mission transition itself.** The declared transition is
   `verification-framework construction → platform/repository convergence → application reliability → real ClariFin_OS usage`.
   "Real usage" is impossible until the app can be *run end-to-end through its own canonical launcher*. G5 (the `out`/`dist` + static-serve defect) is the one finding that blocks *application operation*; G4 blocks *planning speed*, which is a developer-workflow concern, not an app-operation concern. The primary question asks "what prevents it from being practically usable" — the answer, evidenced, is G5.

2. **The root cause is a single, already-made decision with a known consumer set** (M10 partial-convergence): C38.5 chose server-mode + `dist/` and it was propagated to `next.config.ts` and the Playwright `webServer` but *not* to `launch.sh serve_frontend`, `release.yml`, `generate_release_notes.sh`, or the `toolchain-lock.json` snapshot. A bounded, low-risk propagation fix (plus the missing lifecycle control surface) resolves G5 + G8 + S3 simultaneously — no architectural change, no framework change.

3. **C57 can *prove* the fix, which is the point of the transition.** The certified observability chain (canonical execution → RunRecord → metrics → evidence → deterministic `POST /diagnose`) means O-1's acceptance criteria (live :3000 serve, middleware redirect working, clean stop with no orphans, non-empty release artifact, smoke E2E) are each directly provable with existing capabilities. No new verification machinery is needed — satisfying the audit's "do not build more machinery" rule.

4. **It unblocks the highest-leverage downstream work.** O-3's E2E re-verification (S2) needs a *served* app; the release path (S3) is fixed in the same stroke; the platform console GUI (Phase 13) becomes actually reachable — so the "independent diagnostic interface" stops being API-only. O-2a/O-2b (framework truth) are valuable but do not make the product usable; they make the *signal* trustworthy. Operation (O-1) precedes signal (O-2).

5. **Reframing G4 is evidence-backed, not dismissive.** G4 is *worse now* (4,588 files) but its root cause is **branch topology** (132 commits ahead of `main`) + a merge-base default that was designed for PR-boundary parity, *amplified* by a long-lived divergent work branch. It blocks *local planning speed*, has a working CI two-dot path, and its fix (boundary override + timeout) is a framework-truth concern correctly sequenced into **O-2b**, not the top-of-stack. Starting with G4 would be optimizing the diagnostics engine while the application it diagnoses cannot run.

6. **Risk/blast-radius is minimal and reversible.** O-1 touches shell scripts, one release workflow, one notes script, and a lock-snapshot — no production financial code, no C57/C50 architecture, no thresholds. A controlled, evidence-gated change.

### Explicitly NOT the next objective (evidence-based)

- **G4** — planning-speed/boundary concern; has a working CI path; belongs to O-2b after the app runs.
- **G7** — important but it *masks* truth; the converged coverage policy (O-2b) should be decided with the framework-truth work, and lowering/scoping it is a deliberate policy change, better done once the self-verification gate (O-2a) is green so the policy is provable.
- **S1/S2 (CI)** — high value but depend on O-1 (E2E against a served app) and O-2b (honest S4 re-verification); the S1 one-liner could be done early as a micro-fix but the full CI convergence is O-3.
- **D-3/113 frontend findings** — real but a large backend/frontend redesign (O-4) that is best done atop a stable, green base (O-2b/O-3).

```text
NEXT OBJECTIVE = O-1 — Application Lifecycle Convergence & C38.5 Build-Dir Propagation
  (convergent fix of G5 + G8 + S3 + 0.0.0.0/reload; P0; unblocks real usage, E2E-against-app, release, and the reachable diagnostic GUI; provable by certified C57 capabilities)
```

---

## FINAL AUDIT DELIVERABLE

*(Sections A–M, consolidated. Full traceability in the phase records above.)*

### A. Executive State

```text
C57 CORE:    INTACT / CERTIFIED — re-proven this audit (quick profile green 2950 passed; 32 contract tests; event→RunRecord→analytics chain live; Gates A–G hold)
PLATFORM:    API-OPERATIONAL (157 paths live; deterministic diagnose proven) — CI-WEAK (2 dead jobs, 2 false-red gates), GUI exists but UNREACHABLE via launcher (G5)
BACKEND:     FUNCTIONAL — startup validation green; integer-paise DTO boundary (217 _paise, 0 bare); engine mutation-good (account_engine 94.5%); coverage-thin live-route services (recommendation 0%, import 15%, statement 17%, transaction_intelligence 9%)
FRONTEND:    BUILDABLE/TYPED/UNIT-TESTED but UNSERVABLE via canonical launcher (G5); 113 monetary-arithmetic violations duplicated against backend (D-3), un-gated
CI:          13 workflows — 2 dead (forensic-lab S1, playwright S2), 2 false-red (api-contracts, backend-verify via G7/S4), 1 red (runtime via 11 framework test failures), rest at-risk/presumed-green; release artifact empty (S3)
APPLICATION: PARTIALLY OPERABLE — backend runs; end-to-end NOT runnable through `launch.sh start` (frontend half dead); stop/restart/logs missing
PRODUCT:     NOT PRODUCT-READY — demonstrable surfaces built; runnability, E2E-trust, single-source-intelligence, and hardening all outstanding
```

### B. Finding Inventory

| ID | Finding | Layer | Root Cause | Severity | Current Status | Blocking? | Evidence |
| -- | ------- | ----- | ---------- | -------- | -------------- | --------- | -------- |
| F-1/G4 | `check` unusable locally on divergent branches (4,588 files, >5min, silent) | RUNTIME | merge-base(main,HEAD) local boundary + long-lived branch + no timeout/progress | HIGH | CONFIRMED (worse) | Independent-dx YES (local) | Phase 2 G4; timed probes 120s/300s exit 124, 0 output |
| F-2/G5 | Launcher cannot serve frontend (`out` check + static-serve vs `next start`/`dist`) | FRONTEND/INFRA | C38.5 decision not propagated to launcher | HIGH | CONFIRMED | **App operation YES** | `launch.sh serve` exit 1; `start` log; :3000=000 |
| F-3/G6 | Frontend lint broken locally (eslint 10.10.0 installed vs 9.39.5 locked) | FRONTEND/ENV | local node_modules drift from lock | LOW-MED | CONFIRMED (local-only) | No | `npx eslint --version`=10.10.0; ERR_MODULE_NOT_FOUND `eslint/config` |
| F-4/G7 | Contract coverage gate false-red (38.69% < fail_under 40) on 161/161 green | CI/FRAMEWORK | `.coveragerc fail_under=40` applied to contract-only `--cov=.`; orphaned per-scope checker | HIGH | CONFIRMED (reproduced) | Signal YES (2 CI gates + 3 profiles) | `run_contract_tests.sh` → FAIL not reached; `.coveragerc:52` |
| F-5/G8 | No application lifecycle control (stop/restart/status/logs, PID/session); reload watches test artifacts; 0.0.0.0 bind | INFRA | lifecycle control surface never built | MEDIUM | CONFIRMED (rescoped) | No | launch.sh source; clean-kill probe (no orphans) |
| F-6/S1 | m9-forensic-lab CI job hard-fails every run (`sha256sum python -m runtime.verify` hashes a command line) | CI | typo — command line treated as file path | HIGH | CONFIRMED | Forensic dx YES | `m9-forensic-diagnostic-lab.yml:152` |
| F-7 | Dual `finance.db` state roots (`backend/data/` + `data/`) | DATA | no single reconciled state root | MEDIUM | PRESENT | Trust (wrong-truth reads) | Phase 0 find; both exist |
| F-8/S2 | Playwright E2E dead in CI (browser 1.58.2 installed vs `@playwright/test` 1.63.0) | CI | browser pin not aligned to test-runner revision | HIGH | CONFIRMED | E2E-trust YES | `playwright.yml:79` vs package-lock 1.63.0 |
| F-9/S3 | Release uploads `frontend/.next`; build writes `frontend/dist` → empty artifact | CI | C38.5 build-dir not propagated to release workflow | HIGH | CONFIRMED | Release YES | `release.yml:57-58` vs `next.config.ts:15` |
| F-10/K-1 | 8 `vea5_m8r_cli_reconcile` failures — `ci`/`reconcile` exit-code contract unmet; tests use legacy direct-script form | RUNTIME | pre-canonical execution context encoded in tests | MEDIUM | CONFIRMED (8, was 9) | Self-verification YES | Phase 10 re-run |
| F-11/K-2 | 3 `platform_api_phase7` failures — `backend.src.*` not importable from repo root | RUNTIME/BACKEND | import-context duality (cwd=backend vs repo-root) | MEDIUM | CONFIRMED | Self-verification YES | `ModuleNotFoundError: No module named 'src'` |
| F-12/K-3 | floating-rate loan property failure | BACKEND | was real defect; now passing | — | RESOLVED | No | re-run green (1 xpass alongside) |
| F-13/K-11 | mutation jq double-summary path bug | CI | prior script defect | — | RESOLVED/STALE | No | `mutation.yml` correct path; S12 |
| F-14/G6b | stale `EXECUTION_STATE.md` / scripts README / toolchain-lock snapshot | DOCS/CONFIG | docs not re-converged post-C57 | LOW | PRESENT | Misleads | `EXECUTION_STATE.md` 2026-08-05 |
| F-15/D-1 | `verification.yaml` workflows vs `profiles.py` tasks = two workflow truths | FRAMEWORK | parallel generations, only profiles.py executed | HIGH | PRESENT | Truth split | Phase 3 |
| F-16/D-3 | frontend `lib/intelligence/*` computes on paise (113 findings) duplicating backend; rule un-gated | FRONTEND/BACKEND | dual-side intelligence at DTO boundary; C48 rule not enforced | HIGH | PRESENT | Financial-truth YES | `scan_frontend('frontend')`=113 |
| F-17/S5 | api-contracts uploads `api-contract-evidence.json` the profile never produces (orphaned writer) | CI/FRAMEWORK | artifact producer unwired | MEDIUM | CONFIRMED | CI signal | Phase 8 S5; `api_schema_governance` orphan |
| F-18/K-9 | live-route services with thin direct coverage (recommendation 0%, import 15%, statement 17%, txn-intel 9%) | BACKEND | verification gap | MEDIUM | PRESENT | Confidence | contract term-missing table |
| F-19 | runtime/tests red → CI `verification-runtime.yml` red | CI/RUNTIME | F-10 + F-11 | MEDIUM | CONFIRMED | CI signal | Phase 9/10 |
| F-20 | stray `runtime/runtime/generated` tree; `backend/mutants` mirror; `testing/` unowned; 14 embedded framework tests uncollected | HYGIENE | artifact-placement / ownership gaps | LOW-MED | PRESENT | Trust | Phase 14 / T-2/T-3 |
| F-21 | 0.0.0.0 default bind; no evidence signing; dual run-history (events vs RunRecords) | SEC/FRAMEWORK | hardening deferred; split sources | MED-LOW | PRESENT | Hardening | Phase 1/15 |

### C. Deferred G4–G8 Reconciliation

| Finding | Original State | Current State | Still Valid? | Impact | Recommendation |
| ------- | -------------- | ------------- | ------------ | ------ | -------------- |
| G4 check timeout | 973 changed files, timeout on clean tree | 4,588 files (branch 132 ahead of main); `check` >5min, silent, exit 124 at 120s/300s | **CONFIRMED (worse)** — root cause = branch topology + merge-base design, not a collection bug | Local "what changed" planning unusable; CI two-dot path works | O-2b: boundary override + per-task/run timeout + progress. Merge into verification-truth convergence |
| G5 launcher out/dist | checks `frontend/out`, builds to `dist` | `out` check + **static `npx serve` instead of `next start`** (server-mode/middleware violation); `serve` exit 1; `start` frontend dead | **CONFIRMED** (sharpened — 2 defects) | **Blocks end-to-end app operation** | **O-1 (NEXT):** serve from `dist` via `next start`; lifecycle control surface |
| G6 ESLint 10 | flat-config import break, "version drift" | installed 10.10.0 vs locked 9.39.5 (lock coherent with config) = **local node_modules drift**, CI fine | **CONFIRMED locally, MISCLASSIFIED** (env drift, not repo conflict) | local lint broken | O-5: `npm ci` + drift self-diagnosis |
| G7 coverage threshold | 38.69% < 40%, "pre-existing config" | reproduces exactly; **orphaned** per-scope `check_coverage_threshold.py` (0 callers); 2 CI gates + 3 profiles false-red | **CONFIRMED (actively failing)** | pollutes contract/backend signal | O-2b: converge to one wired per-scope policy (thresholds converged, never lowered); retire orphan |
| G8 uvicorn lifecycle | "shuts down when parent shell exits" | no crash; **missing stop/restart/status/logs + PID/session ownership**; reload watches test artifacts; 0.0.0.0 | **CONFIRMED (rescoped — missing control surface, not a crash)** | dev ergonomics / exposure | **O-1 (NEXT):** lifecycle control surface + loopback default + reload scoped to source |

### D. Root-Cause Clusters

```
M10 META: Partial convergence — canonical generations (C38.5 dist, C49 aliases, C57 execution, C51/C52 control-plane)
          applied to canonical paths; legacy consumers un-migrated.

C1  Lifecycle + C38.5 build-dir propagation   → F-2/G5, F-5/G8, F-9/S3, 0.0.0.0, reload   [P0]
C2  Verification truth, context & self-verification → F-1/G4, F-4/G7, F-10/K-1, F-11/K-2, F-15/D-1, F-17/S5,
    F-19/D-9, T-2/T-3                                                                 [P1]
C3  Environment & state hygiene              → F-3/G6, F-7, F-20, F-10/F-14            [P2]
C4  CI infrastructure convergence            → F-6/S1, F-8/S2, F-9/S3, S6, S8, S9, S11, D-4, D-5  [P1]
C5  Single-source financial intelligence     → F-16/D-3, F-18/K-9, 113 findings         [P2]
C6  Product hardening                        → F-21 + Phase 15 gaps                       [P3]
```

### E. Architecture Drift (confirmed)

- D-1 dual workflow truth (`verification.yaml` vs `profiles.py`) — HIGH
- D-2 deprecated alias surface still load-bearing in CI (`reconcile`/`exec-evidence`/`metrics`) — MED
- D-3 dual financial-intelligence truth (client `lib/intelligence/*` vs backend engines; 113 findings) — HIGH
- D-4 documented-but-unwired capabilities (`full`/`integration`/`property` profiles, dead path filters/inputs) — MED
- D-5 stale authoritative docs (`EXECUTION_STATE.md`, scripts README, toolchain-lock snapshot) — MED
- D-6 orphaned/unowned code & trees (`testing/`, embedded framework tests, orphan `check_coverage_threshold.py`, `unrelated/`, stray `runtime/runtime`, `backend/mutants`) — MED
- D-7 C38.5 build-dir consumer drift (launcher `out`, release `.next`, notes `.next`, lock snapshot) — HIGH
- D-8 import-context duality (backend `src.*` cwd-bound vs repo-root runtime imports) — MED-HIGH
- D-9 dual run-history sources (events vs RunRecords) — LOW-MED
- D-10 AI runtime control partially unproven (3 structural test failures) — LOW-MED
- D-11 platform `frontend: HEALTHY` assertion not live-probed (false when :3000 down) — LOW

Implemented-but-undocumented: platform console GUI (`app/platform/*`), `POST /platform/v1/diagnose` deterministic engine.

### F. Diagnostic Capability Matrix

| Capability | CLI | API | GUI | Evidence | Status |
| ---------- | --- | --- | --- | -------- | ------ |
| system health | `verify env-check` | `GET /platform/v1/health` | `app/platform/diagnostics` | ✓ live | **AVAILABLE NOW** |
| environment health | `env-check`/`env-doctor --json` | health (env field) | — | ✓ live | **AVAILABLE (CLI+API)** |
| application health | `launch.sh health` | `GET /health`, `/health/deep` | — | ✓ live | **AVAILABLE NOW** |
| verification status | `verify status/metrics/doctor` | `GET /platform/v1/verification/runs/recent` | `app/platform/verification` | ✓ live | **AVAILABLE NOW** |
| test execution | `verify <profile>` | `POST /platform/v1/verification/run{,/affected,/group,/full}` | — | partial | **AVAILABLE (CLI+API)** |
| test results | stdout + RunRecord | `GET /platform/v1/history/runs{,/{id}}` | `app/platform/history` | ✓ live | **AVAILABLE NOW** |
| capability status | `verify capabilities` | `GET /platform/v1/capabilities{,...}` | `app/platform/capabilities` | ✓ live (55) | **AVAILABLE NOW** |
| recent failures | `verify doctor` | `GET /platform/v1/errors/{...}` | `app/platform/errors` | ✓ live (13/24h) | **AVAILABLE NOW** |
| evidence | `verify` files | `GET /platform/v1/evidence{,...}` | — | ✓ | **AVAILABLE (CLI+API)** |
| logs | (none for app) | `GET /platform/v1/events{,/stream}` (SSE) | — | partial | **PARTIAL** (no plain app-log surface) |
| runtime state | `verify doctor` | `GET /platform/v1/executions/{id}{,/stream}` | — | 3 tests failing | **PARTIAL** (untrusted) |
| CI state | (none) | (none) | — | — | **MISSING** |
| diagnostic explanations | `verify diagnose` | `POST /platform/v1/diagnose` (+ `/ai/diagnose`) | `app/platform/diagnostics` | ✓ live-proven | **AVAILABLE NOW** |
| architecture integrity | `verify` (bypass-audit) | `GET /platform/v1/architecture/{...}` | `app/platform/architecture` | ✓ | **AVAILABLE NOW** |
| change intelligence | (check — heavy/slow) | `GET /platform/v1/change/intelligence` | — | ✓ (G4-bound) | **AVAILABLE (API)**, feed limited by G4 |

**Key blocker to the independent GUI end-state:** the platform console GUI exists but is **unreachable via the canonical launcher (G5)** — it is served only if `next start` on `dist/` is run, which the launcher does not do.

### G. CI Matrix

| Workflow | Status | Root Cause | Blocking | Recommended Objective |
| -------- | ------ | ---------- | --------- | --------------------- |
| api-contracts | **RED (false-negative)** | G7/S4 coverage scoping (+S5 artifact never produced; 5-min budget) | YES (contract gate) | O-2b (coverage policy) + S5 |
| backend-verify | **RED at contract stage** | G7/S4 | YES (backend gate) | O-2b |
| frontend-verify | **PRESUMED GREEN in CI** | G6 is local-only (npm ci → 9.39.5); dead path filter | No | O-5 (G6) + S8 |
| quality | **AT RISK** | S6 10-min budget vs cold mypy + unbounded single-process unit | Risk | O-3 (S6) |
| playwright | **RED (both shards)** | S2 browser 1.58.2 vs test 1.63.0; S8 `e2e/**` | YES (E2E) | O-3 (S2) — needs O-1 served app |
| mutation | **PRESUMED GREEN** | S12 summary contract intact; P0 engines ≥80% | No | — (C42 state good) |
| verification-runtime | **RED** | F-10 (8) + F-11 (3) framework tests | YES (self-verification) | O-2a |
| verification-reconcile | **PARTIAL / spurious** | deprecated `reconcile`; S11 `--base main` fallback; contract unmet | conditional | O-2a (canonical `ci`) + S11 |
| golden | **UNKNOWN** | S9 dead input; S13 unguarded upload | No | O-3 (S9/S13) |
| dependency-update | **MUTED BY DESIGN** | S10 all findings masked; unpinned pip-audit; synthetic `{"outdated":false}` | No (weak) | O-3 (unmask policy) |
| m9-forensic-lab | **RED (hard, every run)** | S1 `sha256sum python -m runtime.verify` | YES (forensic) | O-3 (S1 one-liner) |
| security-codeql | **PRESUMED OPERATIONAL** | no static defect found | No | — |
| release | **BROKEN ARTIFACT** | S3 uploads `.next`, build writes `dist` | YES (release) | **O-1 (S3)** |

### H. Backend Readiness

- **Operational:** FastAPI app (157 routes), startup validation (config→schema→connectivity) green, integer-paise DTO boundary (217 `_paise`, 0 bare), Decimal-mediated float use, ledger/reconciliation semantics with confirm/reject, mutation-verified P0 engines (account_engine 94.5%).
- **Verified-but-gated:** contract suite 161 pass but gate false-red (G7); integration profile unwired in CI.
- **Verification-thin (live routes):** recommendation_service 0%, import_service 15%, statement_repository 17%, transaction_intelligence_service 9% — LOW confidence.
- **Defects:** F-11 import-context duality (3 tests), K-3 floating-rate defect (RESOLVED), thin-coverage services (K-9), dual DB root (F-7).
- **Architectural:** API → service → domain → persistence layering consistent in sampled paths; `src.*` imports are cwd-bound (D-8).

### I. Frontend Readiness

- **Operational (buildable):** Next.js 16 App Router, React 19, TS strict, 13 domain surfaces + 6 platform-console surfaces, OpenAPI-generated types, vitest (35 test files), playwright (232 tests/2 projects, sharded).
- **BROKEN (serve):** cannot be served by the canonical launcher (G5 `out`/`npx serve` vs `next start`/`dist`) — the largest user-visible blocker.
- **BROKEN (lint, local):** eslint 10.10.0 vs lock 9.39.5 (G6).
- **BROKEN (E2E, CI):** playwright browser revision mismatch (S2).
- **ARCHITECTURAL:** 113 monetary-arithmetic violations (D-3) duplicated against backend; C48 lint rule exists but is not a gate.
- **Server mode:** `middleware.ts` legacy-route redirects require `next start` — the serve path must be server-mode (part of O-1).

### J. Product Readiness — technical vs product

**Technically operational (works now, evidenced):**
- backend API + platform API (157 routes) serving live, healthy data;
- deterministic diagnostic engine (`POST /diagnose`) producing symptom→blast-radius→recommended-verification;
- verification foundation (C57) executing, recording (RunRecord), normalizing, and reporting;
- mutation-verified P0 financial engines; integer-paise correctness.

**NOT product-ready (blocking "real usage"):**
1. **Runnability** — app cannot be started end-to-end via `launch.sh start` (G5); no stop/restart/logs (G8). ← **next objective**
2. **Trustworthy signal** — 2 CI jobs dead (S1/S2), 2 gates false-red (G7/S4), self-verification red (F-19), local `check` unusable (G4).
3. **Single source of financial truth** — client computes financial figures (D-3), backend services thin-verified (K-9).
4. **Hardening** — 0.0.0.0 bind, no evidence signing, no CI-state/logs in the independent GUI, authz not proven for `/ai/engineering/execute`.

### K. Implementation Dependency Graph (evidence-derived)

```
C57 (done, re-proven)
  │
  ├──▶ O-1 Lifecycle + C38.5 build-dir (G5+G8+S3+0.0.0.0)        [P0]  ← NEXT
  │        unblocks: end-to-end app, E2E-against-served-app, release, reachable GUI
  ├──▶ O-2a Framework self-verification green (K-1+K-2+T-2/T-3)  [P1]  parallel
  ├──▶ O-2b Change-surface & gate truth (G4+G7+D-1+D-9+S5)       [P1]  parallel (needs O-2a for proof)
  └──▶ O-5 Env/state hygiene (G6+F-7/F-8/F-10)                   [P2]  parallel-safe
  ▼
O-3 CI convergence (S1+S2+S6+S8/S9+S11+D-4+D-5)                   [P1]  ← needs O-1 (served app) + O-2b (honest S4)
  ▼
O-4 Single-source financial intelligence (D-3+K-9)                 [P2]  ← needs O-2b (parity proof) + O-3 (stable base)
  ▼
O-6 Product hardening + independent-GUI completion (C6)            [P3]  ← needs O-1..O-4
  ▼
Real-data validation → product evolution
```

Parallelizable: O-2a ‖ O-2b, O-5 ‖ all. Merge: G8→O-1, S3→O-1, G6→O-5, K-1+K-2→O-2a, S4→O-2b. Abandon: none (deprecated aliases/`verification.yaml` block retired-in-favor, not dropped).

### L. Recommended Program (ordered)

1. **O-1** Application Lifecycle Convergence & C38.5 Build-Dir Propagation — P0
2. **O-2a** Framework Self-Verification Green — P1 (parallel with O-1)
3. **O-2b** Change-Surface & Gate Truth Convergence — P1 (after O-2a for proof; coverage-policy decision may proceed in parallel)
4. **O-3** CI Convergence — P1 (after O-1 + O-2b)
5. **O-4** Single-Source Financial Intelligence — P2 (after O-2b + O-3)
6. **O-5** Environment & State Hygiene — P2 (any time, parallel)
7. **O-6** Product Hardening & Independent Diagnostic Completion — P3 (after O-1..O-4)

(Ordering nuance: O-5 has no blockers and is cheap — it may be pulled forward to run alongside O-1 to normalize the local env while the lifecycle fix is proven.)

### M. Immediate Next Objective

**O-1 — Application Lifecycle Convergence & C38.5 Build-Dir Propagation** (convergent correction of **G5 + G8 + S3** + the `0.0.0.0`/reload watch-items).

**Rationale (evidence-backed, exactly one):**
1. **Only P0, and it gates the mission transition.** The transition is `framework construction → real ClariFin_OS usage`; usage requires the app to *run end-to-end through its canonical launcher*. G5 is the single finding that blocks application operation (reproduced: `serve` exit 1, `start` frontend dead, `:3000`=000). G4 blocks *planning speed*, not *operation* — hence O-1 over "fix G4".
2. **Single root cause, known consumer set (M10).** C38.5 chose server-mode + `dist/` and propagated to `next.config.ts` + Playwright webServer but not to `launch.sh`/`release.yml`/`generate_release_notes.sh`/`toolchain-lock.json`. A bounded propagation fix + the missing lifecycle control surface resolves G5+G8+S3 at once. No architecture/framework change.
3. **C57 proves the fix with no new machinery** (satisfies "don't build more verification machinery"): live :3000 serve + middleware redirect, clean stop (no orphans/ports freed — already proven achievable by the clean-kill probe), non-empty `release` artifact, and a smoke E2E each map to certified C57 capabilities (RunRecord/metrics/evidence/`POST /diagnose`).
4. **Unblocks the highest-leverage downstream work:** O-3 E2E (needs a served app), the release path (S3, same fix), and the platform console GUI becomes reachable — turning the "independent diagnostic interface" from API-only into an actual reachable GUI.
5. **Minimal, reversible blast radius:** touches shell scripts, one workflow, one notes script, a lock-snapshot — no financial code, no C57/C50 architecture, no thresholds.
6. **G4 reframed, not dismissed:** its cause is branch topology (132 ahead of `main`) × merge-base default, it has a working CI two-dot path, and its fix (boundary override + timeout) is a framework-truth concern correctly sequenced to **O-2b** once the app runs.

```
EXECUTE NEXT  =>  O-1  (G5 + G8 + S3 + 0.0.0.0/reload)
THEN          =>  O-2a ‖ O-2b (‖ O-5)  →  O-3  →  O-4  →  O-6
```

---

## AUDIT VERDICT — self-check (all 13 criteria met)

1. ✅ Current repository state known (Phase 0: clean tree @ `3f48c0f0`, env, DBs, artifacts classified)
2. ✅ C57 certification reconciled (Phase 1: **INTACT**, re-proven)
3. ✅ G4–G8 reassessed (Phase 2: G4/G5/G7 confirmed, G6/G8 reclassified)
4. ✅ Known failures reconciled (Phase 10: 6 open, 2 resolved, 1 reshaped, 1 stale)
5. ✅ backend/frontend/platform/CI inventoried (Phases 4/5/6/8)
6. ✅ Architectural drift identified (Phase 11: 11 deviations, 3 material)
7. ✅ Platform AI frontier known (Phase 12: implementation frontier explicit)
8. ✅ Independent diagnostic capability assessed (Phase 13: matrix; G5 is the GUI blocker)
9. ✅ Findings clustered by root cause (Phase 17: M10 + C1–C6)
10. ✅ Priorities assigned (Phase 18)
11. ✅ Dependencies established (Phase 19)
12. ✅ Rational implementation sequence produced (Phase 20: O-1…O-6)
13. ✅ Exactly one next objective selected (Phase 21: **O-1**)

**Audit successful by understanding/decision quality, not by green commands.** The audit executed multiple commands that *fail* (contract gate, vea5 tests, platform-api tests, eslint, `check` timeout, `serve`) — each failure was captured, classified, root-caused, and sequenced. This is the intended forensic outcome.

**NO implementation fixes were applied during this objective.** Working tree changes are audit-generated evidence only (this `progress.md` + regenerated `contract-coverage.json` + appended observability events from the canonical `quick` run). Source implementation is unchanged.
