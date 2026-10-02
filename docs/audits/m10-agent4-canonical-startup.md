# M10 Agent 4 — Canonical Startup, Shutdown, and Clean-Start Validation

**Baseline:** `main @ bfcf336b5b7f46e759c7486f3eb02d0f8d92e14b`

This document is the operator contract. It names exactly **one** canonical
startup and one canonical shutdown, and it contains the real output of a
cold-start run performed in this worktree.

---

## 1. Canonical startup

```
./start.sh
```

Windows (WSL2):

```
start.bat
```

Both are thin wrappers. The single implementation is `scripts/launch.sh`, so
Unix and Windows share one code path, one environment contract, and one set of
URLs. There is no second launcher.

`npm start` at the repository root is an equivalent alias.

### The sequence `./start.sh` performs

```
validate environment -> start backend -> start frontend
-> wait for real readiness -> print URLs
```

1. **Validate environment** (`validate_environment full`) — *before any process
   is spawned*, so a broken environment cannot leave an orphaned backend.
2. **Port preflight** — refuses to start if 8000/3000 are occupied.
3. **Orphan detection** — reports untracked ClariFin processes *on this
   launcher's own ports*; never signals them automatically at this stage.
4. **Start backend** — `.venv/bin/python -m uvicorn src.api:app` in its own
   process group via `setsid`; PID recorded.
5. **Wait for backend readiness** — polls `GET /ready` until `200`.
6. **Start frontend** — `npm start` (Next.js production server) in its own
   process group; PID recorded.
7. **Wait for frontend readiness** — polls `GET /` until 2xx/3xx.
8. **Print URLs** — application, Platform Console, backend, API docs, health.
9. **Hold the foreground** — `Ctrl+C` triggers a full graceful teardown.

### URLs after startup

| Surface | URL |
| --- | --- |
| Application | `http://localhost:3000` (redirects to `/dashboard`) |
| **Platform Console** | **`http://localhost:3000/platform/`** |
| Backend API | `http://localhost:8000` |
| API docs | `http://localhost:8000/docs` |
| Health | `http://localhost:8000/health` |
| Readiness | `http://localhost:8000/ready` |
| Console data API | `http://localhost:8000/platform/v1` |

> The Platform Console is a **frontend** route. It is *not* served on port 8000.
> The trailing slash is significant (`next.config.ts` sets `trailingSlash: true`);
> `/platform` answers `308`, `/platform/` answers `200`.

## 2. Independent Platform Console entry point

```
./scripts/launch.sh console
```

A diagnostic entry point that starts **only the frontend** — no backend, and no
Python environment at all. It is deliberately independent so the console remains
usable when the financial application cannot start.

- Requires only Node 24 + `frontend/node_modules`.
- Validates its own (narrower) environment; the `.venv` is not consulted.
- Serves `http://localhost:3000/platform/`.
- Panels that need live data render an explicit unavailable state
  (`frontend/app/platform/page.tsx:241-248` — "the platform API is
  unreachable"), so a frontend-only run degrades predictably rather than hanging.
- Participates in the same ownership/teardown contract, so
  `./scripts/launch.sh stop` shuts it down too.

`./scripts/launch.sh platform` opens an **already running** console in a browser
and fails with an actionable message instead of opening a dead URL.

## 3. Canonical shutdown

```
./scripts/launch.sh stop
```

What it guarantees:

- Terminates every process the launcher spawned, by recorded PID **and process
  group**, so child processes are included.
- Uses `SIGTERM` first, waits up to 5s, escalates to `SIGKILL` after 2s.
- Refuses to kill a live PID it cannot prove it owns (ownership is validated by
  PGID *and* command line), preserving unowned processes.
- Sweeps orphans **only on this launcher's own ports**, re-validating each PID
  before signalling, so an unrelated service is never terminated.
- Verifies the ports were actually released and reports any that were not.
- **Idempotent**: safe to run when nothing is running; exits `0`.

## 4. Environment prerequisites

Validate at any time without starting anything:

```
./scripts/launch.sh check-env
```

| Requirement | How it is satisfied |
| --- | --- |
| Python ≥ 3.12 in the repository-root `.venv` | `bash scripts/bootstrap.sh` |
| `uvicorn`, `fastapi` importable from that `.venv` | `bash scripts/bootstrap.sh` |
| stdlib `platform` not shadowed by `runtime/platform` | Guaranteed by module execution from the repo root (`AGENTS.md`) |
| Node.js 24 on `PATH` | Install Node 24, then `bash scripts/bootstrap.sh` |
| npm 11.19.0 | Pinned by `frontend/package.json` `packageManager` |
| `frontend/node_modules` | `bash scripts/bootstrap.sh` (runs `npm ci`) |
| `frontend/dist` (production serve path) | `cd frontend && npm run build` |

One command satisfies everything except the production build:

```
bash scripts/bootstrap.sh
```

### Port overrides

Defaults are the canonical 8000/3000. To run a second instance alongside:

```
CLARIFIN_BACKEND_PORT=8010 CLARIFIN_FRONTEND_PORT=3010 ./start.sh
```

Defaults are unchanged when unset.

---

## 5. Clean-start validation transcript

Performed in this worktree from a cold state. **Ports 8010/3010 were used
instead of the canonical 8000/3000 because a concurrent M10 participant
(Agent 3, worktree `m10-agent3-console-frontend-5a07b998d81d2c05`) held
8000/3000 for the duration.** That peer's processes were treated as untouchable;
this run additionally proves the teardown safety fix. Canonical ports remain
the documented default.

### 5.1 Cold state confirmed

```
$ ss -tlnp | grep -E ':(8010|3010) '
8010/3010 FREE

$ ls runtime/generated/launcher
ls: cannot access 'runtime/generated/launcher': No such file or directory
```

### 5.2 Canonical startup

```
$ CLARIFIN_BACKEND_PORT=8010 CLARIFIN_FRONTEND_PORT=3010 ./start.sh
═══════════════════════════════════════════════════════════
  ClariFin OS — Starting (backend dev + frontend serve)
═══════════════════════════════════════════════════════════

───────────────────────────────────────────────────────────
  Validating environment (full)
───────────────────────────────────────────────────────────
Python (canonical .venv):
  OK       canonical interpreter .../m10-agent4-startup-ops-2bcf73e9b6f38c26/.venv/bin/python (Python 3.12.3)
  OK       backend dependencies resolvable (uvicorn, fastapi)
  OK       stdlib platform not shadowed by runtime/platform

Node / frontend:
  OK       v24.20.0
  OK       frontend/node_modules present

Frontend build:
  OK       frontend/dist present (production build available)

  Environment OK.

Preflight checks...
  Ports 8010 and 3010 available.

Starting ClariFin OS Backend...
  Backend started (PID=1265187, PGID=1265187)
Waiting for backend to be ready...
Backend is ready (GET /ready -> 200) after 55s.

Serving ClariFin OS Frontend (production build)...
  Frontend started (PID=1266390, PGID=1266390)
Waiting for frontend to be ready...
Frontend is ready (GET / -> 307) after 26s.

═══════════════════════════════════════════════════════════
  ClariFin OS is running.

  Application        http://localhost:3010
  Platform Console   http://localhost:3010/platform/
  Backend API        http://localhost:8010
  API Docs           http://localhost:8010/docs
  Health / Readiness http://localhost:8010/health  http://localhost:8010/ready

  Stop: ./scripts/launch.sh stop    (or Ctrl+C in this terminal)
═══════════════════════════════════════════════════════════
```

### 5.3 Reachability proved

```
$ curl -s -o /dev/null -w "HTTP %{http_code} -> %{redirect_url}\n" http://localhost:3010/
HTTP 307 -> http://localhost:3010/dashboard

$ curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:3010/platform/
HTTP 200
$ curl -s http://localhost:3010/platform | grep -oE "<title>[^<]*</title>"
<title>Platform Console — ClariFin OS</title>

$ curl -s http://localhost:8010/health
{"status":"healthy","version":"1.0.0","message":"ClariFin_OS is running"}

$ curl -s http://localhost:8010/ready
{"status":"ready","checks":{"database":true,"upload_dir":true,"data_dir":true},"message":"All systems operational"}
HTTP 200

$ curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8010/platform/v1/health
HTTP 200
```

Proof the pre-existing defect D1 was real (backend has no `/platform`):

```
$ curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8010/platform
HTTP 404
$ curl -s http://localhost:8010/platform
{"detail":"Not Found"}
```

### 5.4 Status and health

```
$ ./start.sh status
Backend (:8010)
  State:      RUNNING
  PID:        1265187
  PGID:       1265187
  Command:    .../python -m uvicorn src.api:app --host 0.0.0.0 --port 8010 --reload
  Port:       8010 — occupied by owned process

Frontend (:3010)
  State:      RUNNING
  PID:        1266390
  PGID:       1266390
  Command:    npm start -p 3010
  Port:       3010 — occupied by owned process

  Overall:    Application RUNNING
STATUS_EXIT=0

$ ./start.sh health
Backend:
  Process        PASS (PID=1265187)
  /health        PASS (HTTP 200)
  /ready         PASS (HTTP 200)
Frontend:
  Process        PASS (PID=1266390)
  HTTP (:3010)   PASS (HTTP 307)
  Overall        HEALTHY
HEALTH_EXIT=0
```

### 5.5 Canonical shutdown — and proof the peer's servers survived

```
$ ./start.sh stop
  backend: terminating PID 1265187 (PGID=1265187)...
  backend: exited gracefully (1s)
  frontend: terminating PID 1266390 (PGID=1266390)...
  frontend: exited gracefully (1s)

Ports released: 8010 (backend), 3010 (frontend)
  ClariFin OS stopped.
STOP_EXIT=0
```

Verification:

```
$ ss -tlnp | grep -E ':(8010|3010) '
OK: 8010 and 3010 free

$ ps -o pid,args -p 1265187,1266390,1266410
    PID COMMAND                      <- launcher leader + npm + next-server child: all gone

$ ps -o pid,args -p 1269970,1275764   <- the OTHER agent's servers
1269970 .../python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
1275764 next-server (v16.3.6)

$ ss -tlnp | grep -E ':(8000|3000) '
LISTEN 0 2048 0.0.0.0:8000 0.0.0.0:* users:(("python",pid=1269970,fd=6))
LISTEN 0  511 0.0.0.0:3000 0.0.0.0:* users:(("next-server (v1",pid=1275764,fd=21))
```

**No orphaned processes remained, and the concurrent participant's servers were
untouched.** This is the concrete proof of defect D5's fix: under the previous
machine-wide `pgrep -f "next-server|next start"` sweep, `stop` would have killed
PID 1275764.

### 5.6 Idempotency

```
$ ./start.sh stop
No owned processes recorded.
  ClariFin OS is not running (or already stopped).
EXIT=0

$ ./start.sh stop        # third consecutive invocation
No owned processes recorded.
  ClariFin OS is not running (or already stopped).
EXIT=0
```

### 5.7 Platform Console independence

```
$ ./start.sh console
  ClariFin OS — Platform Console (independent)

  Validating environment (console)
  OK       v24.20.0
  OK       frontend/node_modules present

  Environment OK (console requires no Python environment).

Starting frontend (console mode, Next.js dev server)...
  Console frontend started (PID=1278237, PGID=1278237)

Platform Console is ready (GET /platform -> 200) after 31s.

  Platform Console is running (frontend only).
  Console:    http://localhost:3010/platform/
  Platform API: http://localhost:8010/platform/v1/health  (requires the backend)
```

Independence proof — the backend was genuinely absent:

```
$ curl -s -o /dev/null -w "GET /platform/ -> HTTP %{http_code}\n" http://localhost:3010/platform/
GET /platform/ -> HTTP 200

$ ss -tlnp | grep -E ':8010 '
OK: nothing listening on 8010 - console is independent

$ ls runtime/generated/launcher/state/
console.pid          <- no backend.pid; no Python process was started
```

```
$ ./start.sh stop
  console: terminating PID 1278237 (PGID=1278237)...
  console: exited gracefully (1s)
Ports released: 8010 (backend), 3010 (frontend)
STOP_EXIT=0
```

## 6. Validation coverage and limits

Proven: environment validation, backend readiness gating on `/ready`, frontend
readiness gating, Platform Console reachable with the backend absent, URL
printout, graceful teardown, idempotent shutdown, no orphaned processes, and
isolation from a concurrent participant's servers.

**Not runtime-verified on this host:** the Windows `start.bat` path (defect D3),
which needs a Windows+WSL2 host. It was fixed by construction: `wslpath` output
is joined with a forward slash instead of the Windows backslash the original
appended. This limitation is recorded rather than papered over.