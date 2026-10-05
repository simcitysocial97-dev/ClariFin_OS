# M11 Task 15 — Platform Console cold-start readiness

**Agent:** 4 of 4 (Platform operations and startup)
**Branch:** `m11/parallelism-correctness`
**Scope:** `scripts/**`, `start.sh`, `start.bat`, Platform Console frontend routes/components, Platform API integration, startup/readiness diagnostics.

---

## 1. Verdict up front

**The premise of the task was wrong, and the measurement says so.**

There is no expensive application initialization to defer. The FastAPI lifespan
is **0.23 s**:

| Phase | Cost | How measured |
|---|---|---|
| `import src.api` (26 routers + platform router) | **16.3 s** cold-`.pyc`, 4.7 s warm-`.pyc` | `python -X importtime`, fresh interpreter |
| `run_startup_validation()` — the **entire** lifespan | **0.23 s** | phase probe, fresh interpreter |
| `GET /ready` (financial readiness) | **5.2 – 24.3 ms** | server-side `duration_ms`, two cold starts |
| `GET /health` (liveness) | **3.8 ms / 17.3 ms** | server-side `duration_ms`, two cold starts |
| first `build_health_snapshot()` | **33.6 s** | phase probe, fresh interpreter |

Corroborated in a live run: the launcher's own backend log shows
`Startup validation complete - all systems ready` and `Application startup
complete` within **0.78 s** of each other, immediately after a
`Database schema initialized and verified` — versus ~15.4 s of module import
*before* that point.

Deferring initialization would defer nothing. Precomputing the platform
snapshots at startup would convert a 0.23 s cost into a >15 s one. Both would
make the system worse.

### The real defect

`lib/api/gateway.ts` called `fetch(url, init)` with **no `AbortSignal`**. No
request could ever reject for taking too long, so every console page rendered
an indefinite `Loading…` across a 13.8–118.6 s window. That is the defect the
milestone exists to remove, and it is entirely in the frontend.

---

## 2. Measured cold-start timeline

Real `uvicorn` on an alternate port, launched the way the launcher launches it
(`cd backend` + `python -m uvicorn src.api:app`), `__pycache__` and every
generated cache dropped first, `FINANCE_DB_PATH` pointed at a copy of the live
database. Two full independent cold runs.

```
spawn -> first HTTP 200 (/health)           8.05 s | 11.68 s
1 GET /platform/v1/health   COLD        28.52 s | 13.81 s   (37.83 s / 18.52 s / 37.8 s on runs 3–5)
2 GET /platform/v1/health   warm         0.11 s |  0.01 s
3 GET /platform/v1/evidence COLD        118.57 s | 53.79 s
4 GET /platform/v1/capabilities COLD      5.37 s |  1.06 s
5 GET /platform/v1/errors/current COLD     3.34 s | 10.65 s
6 GET /platform/v1/tasks COLD             1.46 s |  4.77 s
7 GET /platform/v1/events?limit=8 COLD    0.04 s |  0.12 s
8 GET /platform/v1/health   warm         0.04 s |  0.05 s
9 GET /ready (financial)                  0.02 s |  0.07 s
```

**M10's `39 s` and `117 s` are both reproduced** (37.8 s; 118.6 s).

### Where the time goes

**(a) 16.3 s of the startup window is eager native imports in request routers.**
Self-time from `python -X importtime`:

| Library | Self time | Reached via |
|---|---|---|
| `camelot` | **8.35 s** | `src.routers.accounts` → `src.services.import_service` → `src.extraction.categorizer` → `camelot_extractor` |
| `cv2` | **3.69 s** | `runtime.platform.ai.tools.handlers` |
| `pandas` | **2.95 s** | `runtime.platform.ai` |

None of these are needed to serve a request until a CSV/PDF import or a
framework-integrity check actually runs.

**(b) The platform-health cold build is framework integrity, computed inside the
request.** `runtime/platform/api/services/health.py:55` calls
`fi_service.build_framework_integrity()`. Attributed in-process with the caches
dropped:

```
run_authority_drift_detection()      3.7 s   (4.5 s on a repeat call — NOT memoized)
ArtifactFreshnessDetector.check()   4.0 s   (4.0 s on a repeat call — NOT memoized)
K1–K9 self-tests                  ~18.0 s   (memoized 600 s, in-process only)
-> build_framework_integrity()[1st] 23.9 s
-> build_framework_integrity()[2nd]  5.9 s
```

**(c) `/platform/v1/evidence` is the 118 s.** It is the only console read with
**no snapshot cache**: `backend/src/routers/platform.py:603` calls
`evidence.build_evidence_list()` directly, while every sibling read goes through
`snapshot.get_or_build`. That builder constructs a `ControlPlane()`, shells out
for changed files, and runs `planner.plan()`.

It is also the only measured path whose cost scaled with host load:
**118.57 s at loadavg 8.34, 53.79 s at loadavg 12.76, 2.6 s in a quiet process.**
M10's 375 s is the same mechanism at higher contention.

### The 117 s / 375 s mechanism, proven

The platform endpoints are `async def` handlers that call **synchronous,
CPU/IO-heavy builders directly on the event loop**. One build stalls every other
in-flight request. Cold 5-way parallel burst — the console dashboard's exact
fan-out:

```
GET /platform/v1/health          0.419 s   server duration_ms=410.1
GET /platform/v1/capabilities    5.824 s   server duration_ms=5405.8
GET /platform/v1/events?limit=8  5.819 s   server duration_ms=5404.9
GET /platform/v1/errors/current  5.818 s   server duration_ms=5405.8
GET /platform/v1/tasks           5.816 s   server duration_ms=5405.8
```

Four requests issued milliseconds apart report **identical** `duration_ms`. They
were received at different times and released at the same instant. That is the
blocked event loop, and it is the whole of the "117 s" claim — not a slow
endpoint, a stalled *loop*.

---

## 3. The readiness decision (Task 15 item 4)

**Decision: startup readiness MUST NOT wait for full financial initialization —
and it already does not. No gate was changed.**

Evidence:

1. `/ready` answers in 5.2–24.3 ms once the socket is serving, and the lifespan
   that precedes it is 0.23 s.
2. The launcher gates the frontend on `/ready` only (`_wait_for_backend_ready`).
   That is correct and was left alone.
3. `cmd_console` starts the console frontend with **no backend at all**, so
   console-only operation was never blocked on financial initialization.
4. The expensive work is not initialization — it is first-request snapshot
   building, which happens *after* readiness and therefore *after* the operator
   has been told everything is up.

**Platform health cannot honestly be made available earlier** within frontend or
launcher scope. Making it cheap requires changing `build_health_snapshot`,
`build_framework_integrity` and `runtime/platform/cache.py` — all outside this
agent's ownership. See §7 for the exact changes.

**What the frontend *can* do, and did:** use `GET /health` — a constant-return
handler measured at 3.8–17.3 ms — as the console's readiness signal, so "backend
ready" is reported in milliseconds while the much more expensive platform data
reads are still building. That is the whole fix, and it needs no backend change.

---

## 4. The four operator-visible states

| State | Evidence | Operator action |
|---|---|---|
| **BACKEND UNAVAILABLE** | `fetch` raised `TypeError` — refused connection, or a cross-origin rejection | start / restart / check `CORS_ORIGINS` |
| **BACKEND STARTING** | `ApiTimeoutError` — our own abort fired, so the connection *was* accepted and nothing came back | **WAIT. Do not restart.** |
| **BACKEND READY** | `GET /health` answered 200 | none |
| **PLATFORM ENDPOINT FAILED** | the app answered `/health` 200 **and** a `/platform/v1/*` read failed or blew its deadline | investigate the endpoint, not the process |

The distinguishing evidence is transport-level, not a timer:
`ApiTimeoutError` is a **separate class** from `ApiError`, and
`classifyPlatformRead` takes the liveness verdict as an argument. Identical
transport evidence therefore produces opposite verdicts depending on whether the
fast probe already answered — which is exactly the pair that must not collapse.

### Verified in a real browser (Chromium, live Next.js console)

| Scenario | `platform-backend-status` | `console-unavailable[data-console-state]` | `data-console-timed-out` | Headline |
|---|---|---|---|---|
| nothing listening on `:8000` | `unavailable` | `unavailable` | `false` | `API UNAVAILABLE` |
| listener accepts, never answers | `starting` | `starting` | `true` | `BACKEND STARTING — WAIT, DO NOT RESTART` |
| `/health` 200 in 1.1 ms, `/platform/*` stalls | `ready` | `endpoint-failed` | `true` | `PLATFORM ENDPOINT FAILED — BACKEND IS SERVING` |
| backend healthy, platform answers | `ready` | *(no terminal state — live data)* | — | — |

Captured reason strings (verbatim):

```
starting      "The backend accepted the connection but did not answer GET /health
               within 3000 ms. It is still starting up."
endpoint-fail "/platform/v1/health did not answer within 20000 ms while the backend
               itself is healthy. The endpoint is stalled."
unavailable   "Nothing is answering on the backend address from this browser. Causes,
               in the order they occur: it is not running; it is still importing its
               module graph and has not bound the port; or it is running but this
               origin is not in its CORS allow-list (backend/src/startup.py reads
               CORS_ORIGINS)."
```

The CORS cause was found *by measurement*: a backend answering `/health` in
1.1 ms without `Access-Control-Allow-Origin` produced `unavailable`, because
`fetch` reports a cross-origin rejection as the same `TypeError` as a refused
connection. Without naming CORS, an operator would restart a healthy backend to
fix a header.

### Architecture authority: unchanged

The console still computes **no** health verdict. `DEGRADED` still means "I
cannot verify". Every status string comes from the backend; the frontend reports
only which state it is in and the backend's own reason. `ConsoleUnavailableState`
returns `null` for a `ready` verdict, so a logic bug cannot invert the message.

---

## 5. The smallest correct fix

### 5.1 Request deadlines (the actual fix)

`frontend/lib/api/gateway.ts`:

- `ApiTimeoutError` — a distinct class from `ApiError`, because "no response was
  produced" and "the server produced a 500" are different operator problems,
  and because a timeout is the only positive evidence of an accepted connection.
- `withDeadline()` — composes a caller's `AbortSignal` with a deadline, and
  reports which fired, so a caller abort is never mislabelled as a timeout.
- **Deadlines are applied by path**, not by call site:
  `resolveDeadline()` gives every `/platform/v1/*` request the deadline unless a
  caller explicitly opts out. An unbounded call site is precisely how this defect
  survived; there is now no way to reach the platform API without a deadline.
- `platformReadRetry` — no automatic retry for platform reads. Measured: on a
  cold burst four requests issued milliseconds apart returned at the same
  instant, so an automatic retry appends to a queue rather than bypassing it.
  With a 20 s deadline, `transientRetryPolicy` would have made the operator wait
  4 × 20 s. A control room must report a state; the retry is the operator's
  explicit action.

**Deadlines chosen from measurement, not taste:**

| Constant | Value | Basis |
|---|---|---|
| `LIVENESS_DEADLINE_MS` | 3 000 | `GET /health` measured 3.8–17.3 ms → ~170× margin |
| `PLATFORM_API_DEADLINE_MS` | 20 000 | clears the slowest *cached* read (5.4 s) by 3.7×; deliberately **short** of the 53.8–118.6 s cold builds so those are reported instead of waited out |

**Non-platform paths keep their pre-M11 unbounded behaviour.** This is a recorded
gap, not an oversight, and it is pinned by an explicit test so it cannot drift:
raising a deadline there requires measured worst-case latencies for the
financial API's paths, which this milestone **did not measure**. Inventing a
number there would convert a visible stall into an invisible failure.

### 5.2 States, not spinners

- `frontend/lib/platform/backend-status.ts` — the four-state classifier and
  `useBackendStatus()`. Driven by the liveness probe **only**, never by a
  platform read, so it is never blocked by one. Stops re-probing once ready.
- `frontend/components/platform/backend-status-bar.tsx` — a persistent strip in
  the console *shell*, so "is the backend up?" is answerable from any route,
  including routes whose data has not loaded. Server-rendered (verified present
  in the `/platform/` HTML).
- `frontend/components/platform/console-state.tsx` —
  `ConsoleUnavailableState` now renders the three terminal states from evidence.
  **The pre-M11 `console-unavailable` / `console-api-unavailable` selectors are
  preserved verbatim** — three Playwright specs (`platform-dashboard`,
  `platform-c67.2`, `m10-agent3-console`) use them as "the console reached a
  terminal state"; widening them would have silently changed what those specs
  assert. The new state is additive: `[data-console-state="..."]`.
- `frontend/app/platform/page.tsx` — the dashboard classifies its failures
  instead of collapsing them.
- The pre-M9 label "still working?" is gone. `ConsoleLoadingState` says
  `Waiting for the backend to start serving…` when liveness has not confirmed.

### 5.3 Launcher exposes platform readiness separately

`scripts/launch.sh`:

- `platform-status` — a new command reporting the same four states, bounded,
  exit 0 only when the platform API answers. Discovered because `health` could
  not answer "can the console show data yet?".
- `_http_state()` — uses `curl`'s exit code to separate `refused` (7) from
  `timeout` (28). A single `_http_code` reports `000` for both, which is why the
  launcher could previously not express `STARTING`.
- `_platform_readiness()` / `cmd_platform_status()` — the classifier.
- The startup banner and `health` now report Platform API readiness **separately
  from** financial readiness. Only a hard platform failure folds into the overall
  verdict; `STARTING` does not, because a slow platform build is not an
  unhealthy financial application.
- **The platform probe is non-gating.** Waiting out a 13.8–37.8 s build before
  printing the URLs would delay the message that tells the operator the console
  is already usable.
- `status` now reports the Platform API verdict and a console-only run. It
  previously looked only at `backend` and `frontend`, so an operator running
  `./start.sh console` was told `Overall: STOPPED` while the console was live —
  the same class of defect as the console's own missing states.

---

## 6. Before / after

| Behaviour | Before | After |
|---|---|---|
| Worst case a console page waits | **unbounded** (no deadline existed) | **20 s**, then a named state + retry |
| Cold-start page experience | `Loading platform state…` for 13.8–118.6 s | `BACKEND STARTING` + `Check again` within 3–20 s |
| States an operator can distinguish | 1 (`DEGRADED` / API unavailable) | **4** |
| Readiness signal | none (each page's own read) | `GET /health`, 3.8–17.3 ms, on every route |
| Backend readiness vs console data readiness | conflated | reported separately by `status`, `health`, `platform-status`, the banner and the strip |
| `./start.sh health` against a silent backend | **hung indefinitely** | terminates, bounded 5 s/probe |
| `stop` on a process it did not spawn | **killed it** | reports it, leaves it running |

The 13.8–118.6 s server-side costs are **unchanged** — they are backend work
outside this agent's ownership, and hiding them behind a longer timeout is
explicitly out of bounds. What changed is that the console now *reports* them
within 20 s instead of waiting them out in silence.

---

## 7. Changes needed in files this agent does not own

Route to Agent 3 / `main`.

**7.1 — `backend/src/routers/platform.py:603`, `list_evidence`:** route through
the snapshot cache, the same fix `get_errors_current` (`:765-775`) already
applied to itself:

```python
return _ok(snapshot.get_or_build("evidence", evidence.build_evidence_list, nocache=nocache))
```

plus `"evidence": 300` in `DEFAULT_TTL_SECONDS`
(`runtime/platform/cache.py:87-102`) and a `nocache` query parameter.
Effect: **53.8–118.6 s → ~1 ms warm**, and the console stops queueing behind it.

**7.2 — `runtime/platform/cache.py:69`, `SNAPSHOT_PATH` is CWD-relative — real
defect.** Measured two distinct caches alive at once:
`runtime/generated/platform/snapshot.json` (27 KB) and
`backend/runtime/generated/platform/snapshot.json` (111 KB). A launcher-started
backend (`cwd=backend/`) and a module-execution run (`cwd=repo root`, per
`AGENTS.md`) read and write **different caches**. This is the mechanism behind
"slow on my machine, fast on yours". Resolve from the repository root, not
`os.getcwd()`.

**7.3 — memoize the two framework-integrity detectors.** Only the K1–K9
self-tests are memoized (`framework_integrity.py:41-61`). `run_authority_drift_detection()`
(4.5 s per call) and `ArtifactFreshnessDetector.check()` (4.0 s per call) are
recomputed on every health read: **8.5 s of the ~19 s warm health build is pure
recomputation.**

**7.4 — deferred by design, do NOT do blind.** Running the builders via
`asyncio.to_thread` behind the existing per-domain single-flight in
`cache.get_or_build` would stop the burst from serialising. **NOT MEASURED** for
safety on this host; recommended only because the burst evidence in §2 is
unambiguous and the change is small.

**7.5 — not this agent's problem.** `behaviour_patterns` is a known-empty
surface and `behaviour/profile` returned 500; both already reported to Agent 3.
The console now degrades gracefully for both (named state + retry + a
non-indefinite wait), which is the only part that was mine.

---

## 8. Regression coverage

| File | Cases | Result |
|---|---|---|
| `frontend/lib/__tests__/gateway-deadline.test.ts` | 14 | pass |
| `frontend/lib/platform/__tests__/backend-status.test.ts` | 13 | pass |
| `frontend/lib/platform/__tests__/console-states.test.tsx` | 9 | pass |
| `frontend/lib/platform/__tests__/backend-status-bar.test.tsx` | 8 | pass |
| `scripts/test-platform-readiness.sh` | 12 | pass |
| `frontend/lib/__tests__/gateway-invariance.test.ts` (pre-existing guard) | 3 | pass |
| `frontend/lib/hooks/__tests__/` (pre-existing) | 3 files | pass |
| **Total vitest** | **8 files / 89 tests** | **pass** |

Also run: `tsc --noEmit` → **0 errors**; ESLint on all touched paths → **0
errors** (9 pre-existing `no-explicit-any` warnings in `app/platform/diagnostics*`,
not authored here).

`scripts/test-platform-readiness.sh` drives real TCP servers rather than mocking,
because the classifier *is* `curl`'s exit code. It asserts on the **absence** of a
kill for shutdown safety, since that cannot be read out of the launcher's own
output. It is hermetic: pids tracked in a file (not a shell array — an
array-based first version leaked 9 fixture servers through command-substitution
subshells) and a `console.pid` record removed by an `EXIT` trap.

Not wired into CI: `.github/**` belongs to Agent 2. It must be added there.

---

## 9. Launcher and shutdown safety

### Proven, with output

**Port conflict is diagnosed, never ignored.** `./start.sh start` with `:8000`
held by an unowned process aborts *before spawning anything*:

```
Preflight checks...
  Backend port 8000 occupied: LISTEN 0 2048 0.0.0.0:8000 ... users:(("python",pid=1704145,fd=6))
Aborting start: port conflict(s) detected. Resolve before retrying.
START_EXIT=1
```

**A failed start leaves no orphan.** With a `SyntaxError` in a peer file the
backend could not import; the launcher detected it, printed the exact
`file:line`, terminated its own process (`backend: exited gracefully (1s)`) and
exited non-zero. Post-failure: no new processes, `8010/3010` free, PID state dir
empty.

**`stop` is idempotent** — twice, both exit 0.

**Console teardown is complete.** A 5-process tree (`npm run dev` → `sh -c` →
`next dev` → `next-server` → a turbopack worker) terminated on one PGID;
no `next-server` survivors; port released; state dir empty.

### DEFECT FOUND AND FIXED — `stop` killed a process it did not spawn

Reproduced against the real stale process: `pid 1704145`,
`../.venv/bin/python -m uvicorn src.api:app --host 0.0.0.0 --port 8000`, started
17:43, **PPID 1** (re-parented to init because its process-group leader had
exited), **no PID record** in `runtime/generated/launcher/state/`.

```
$ ./scripts/launch.sh stop
Some ports still occupied. Attempting orphan cleanup...
  Killing backend orphan on port 8000: 1704145
```

`scripts/launch.sh` matched the listener's **command line alone**. A
command-line signature is not ownership — it can tell you a process *looks* like
a ClariFin component, never that this launcher started it. The M10 audit claimed
this path "re-validates each PID before signalling, so an unrelated service is
never terminated"; on this host that claim did not hold. A process from another
session, holding the canonical port, was destroyed by a `stop` that never spawned
it. The same defect existed in `cmd_restart`, which SIGKILLed on the same
predicate.

Fixed with `_port_listener_is_owned()`, which requires all three proofs:

1. a PID record exists for that component, **and**
2. the listener is that PID or shares its process group, **and**
3. the command line matches the component signature.

With no record, the listener is **reported and left running**:

```
  LEAVING UNOWNED backend-shaped listener on port 8000: PID 1997883
    It matches a ClariFin component but has no pid record for this
    launcher, so it was started by something else (another session,
    another worktree, or by hand). Not terminated.
    Command: /home/.../.venv/bin/python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
WARNING: Ports may still be in use:
  8000 (backend) still occupied
```

Re-verified end to end: an unowned ClariFin-shaped listener was left alive while
the owned console in the same `stop` was terminated and its port released. The
"still occupied" warning is now *accurate* — the port genuinely is held by a
process we refused to kill.

**Cost of the fix, stated plainly:** an orphan whose state directory was deleted
now needs a manual `kill`. That is the intended trade — a `stop` that can destroy
another session's server is not a safe shutdown.

### Second launcher defect fixed

`./scripts/launch.sh health` **hung indefinitely** against a backend that accepts
connections and never answers, because `_http_code` used `curl` with no
`--max-time`. That is exactly the cold-start shape. Fixed with
`HTTP_PROBE_MAX_TIME` (default 5 s; measured healthy probes are 3.8–24.3 ms).
`health` against a silent backend now terminates in ~35 s.

A third, minor: the post-sweep port re-check fired before a SIGTERM'd listener
had released its socket, so it warned about a port that was already free. Now
polled with a bounded 5 s grace.

### Note on `pid 1704145`'s interpreter

`../.venv/bin/python` with `cwd=backend/` resolves to the **canonical**
repo-root `.venv`. It was not a shadow `backend/.venv`. It was an orphan, not a
toolchain violation. (It was terminated by the pre-fix `stop` while reproducing
this; a later, correct `stop` left a replacement alive, and that was cleaned up
manually at the end of this task.)

---

## 10. Canonical reproducible operator workflow

`start.sh` / `start.bat` / `scripts/launch.sh` remain the canonical, simplest
entrypoint. Nothing new was required to operate the system.

```bash
# 0. First time only — the single canonical environment.
bash scripts/bootstrap.sh

# 1. Full application. Validates env, starts the backend, waits for GET /ready,
#    starts the frontend, prints the URLs.
./start.sh

#    Read the banner. It reports TWO different readiness facts on purpose:
#      Application / Platform Console / Backend API ... URLs
#      Platform API  READY | STARTING | ENDPOINT FAILED | BACKEND UNAVAILABLE
#    STARTING is normal on a cold start and does NOT block the URLs.

# 2. Cold-start question — "can the console show data yet?"
./start.sh platform-status          # exits 0 only when the platform API answers
./start.sh platform-status 60       # optional: longer bound, default 25 s

# 3. Everything the launcher knows.
./start.sh status                  # adds the Platform API verdict + console-only runs
./start.sh health                  # process + HTTP + platform; Overall is financial
./start.sh logs backend            # startup failures land here with file:line

# 4. Console only — no Python, no backend. Fully usable while the backend warms.
./start.sh console                 # -> http://localhost:3000/platform/

# 5. Deterministic shutdown. Idempotent; safe with nothing running.
./start.sh stop

# 6. Parallel instance without touching the canonical ports.
CLARIFIN_BACKEND_PORT=8010 CLARIFIN_FRONTEND_PORT=3010 ./start.sh
CLARIFIN_BACKEND_PORT=8010 CLARIFIN_FRONTEND_PORT=3010 ./start.sh stop
```

**Reading the console during a cold start**

| Strip shows | Do this |
|---|---|
| `BACKEND STARTING` | **wait.** Do not restart. The first read is building. Re-check via the strip's *Re-check* button or `./start.sh platform-status`. |
| `BACKEND UNAVAILABLE` | backend not running, still importing, or this origin is missing from `CORS_ORIGINS`. Check `./start.sh status` for the port occupant. |
| `BACKEND READY` + a page shows `PLATFORM ENDPOINT FAILED` | the process is healthy; the endpoint is at fault. `./start.sh logs backend`. |
| `BACKEND READY` + live data | nothing to do. |

**Seeding data for console validation** — use Agent 2's deterministic tool, not a
hand-made fixture:

```bash
PYTHONPATH=backend .venv/bin/python tools/e2e_seed.py --reset --json
# determinism check (the `database` path is the only machine-dependent field)
PYTHONPATH=backend .venv/bin/python tools/e2e_seed.py --db /tmp/a.db --reset --json > run1.json
PYTHONPATH=backend .venv/bin/python tools/e2e_seed.py --db /tmp/b.db --reset --json > run2.json
diff run1.json run2.json     # only `database` may differ
```

It seeds only through `/api/v1/*`, never direct SQL. 16 of 18 surfaces populate
from it; `behaviour_patterns` is known-empty and `behaviour/profile` returns 500 —
both are Agent 3's, and neither blocks console validation because the console now
reports them as a named state rather than a spinner.

**Port conflicts** are diagnosed, never silently ignored: `start` aborts naming
the occupying PID. `./start.sh status` prints the raw listener, and `./start.sh
stop` will report an unowned ClariFin-shaped listener but **will not kill it**.
Verify ownership before removing it by hand.

**Known unrelated:** 4 pre-existing Earnd app failures are branch detections that
need `docker-compose down` to free ports. Not investigated.

---

## 11. Not completed

- **Backend cold-start cost is unchanged** (13.8–118.6 s). Those are backend
  changes in files this agent does not own; §7 gives the exact diffs. Hiding
  them behind a longer frontend timeout was explicitly out of bounds.
- **`asyncio.to_thread` offload** — recommended, **NOT MEASURED** for safety on
  this host (§7.4).
- **Global deadline for non-platform financial API paths** — **NOT MEASURED**;
  kept unbounded on purpose and pinned by a test so it stays visibly open (§5.1).
- **CI wiring** for `scripts/test-platform-readiness.sh` — `.github/**` belongs to
  Agent 2; must be added there or the test will not run in CI.
- **The three pre-existing Playwright console specs were not extended** to assert
  the new states. Their selectors still resolve (verified), so nothing is broken,
  but they only exercise `unavailable`. Extending them needs
  `frontend/tests/e2e/**`, outside this agent's scope.
- **No full mutation campaign run** (out of scope by instruction).