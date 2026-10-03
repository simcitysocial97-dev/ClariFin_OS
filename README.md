# ClariFin OS

Personal finance platform — FastAPI backend (`src.api:app`) and a Next.js
frontend.

## Canonical startup

There is exactly **one** way to start ClariFin OS.

```bash
./start.sh
```

On Windows (via WSL2):

```
start.bat
```

Both delegate to `scripts/launch.sh`, the single canonical launcher. `npm start`
at the repository root is an equivalent alias. No other startup method is
official.

`./start.sh` validates the environment, starts the backend, starts the
frontend, **waits for real readiness** (polling `GET /ready` and `GET /`, not
sleeping), and prints the URLs.

| Surface | URL |
| --- | --- |
| Application | http://localhost:3000 (redirects to `/dashboard`) |
| **Platform Console** | **http://localhost:3000/platform/** |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Health / readiness | http://localhost:8000/health · http://localhost:8000/ready |

The Platform Console is a **frontend** route, not a backend route — it is not on
port 8000. The trailing slash matters (`/platform` returns `308`).

## Platform Console — independent entry point

```bash
./scripts/launch.sh console
```

Starts **only the frontend**: no backend, no Python environment. This is a
diagnostic surface, deliberately independent of the financial application so it
stays usable when the app cannot start. Panels needing live data show an explicit
unavailable state until the backend is running.

To open an already-running console in a browser instead:
`./scripts/launch.sh platform`.

## Canonical shutdown

```bash
./scripts/launch.sh stop
```

Terminates every process the launcher spawned (by PID **and** process group, so
children are included), escalates `SIGTERM` → `SIGKILL` if needed, verifies the
ports were released, and refuses to kill any process it cannot prove it owns.
**Idempotent** — safe to run when nothing is running; exits `0`.

Pressing `Ctrl+C` in the startup terminal performs the same teardown.

## Prerequisites

| Requirement | Satisfied by |
| --- | --- |
| Python ≥ 3.12 in the repository-root `.venv` | `bash scripts/bootstrap.sh` |
| Backend deps (`uvicorn`, `fastapi`) | `bash scripts/bootstrap.sh` |
| Node.js 24 + npm 11.19.0 | `bash scripts/bootstrap.sh` (checks version) |
| `frontend/node_modules` | `bash scripts/bootstrap.sh` (runs `npm ci`) |
| `frontend/dist` production build | `cd frontend && npm run build` |

```bash
bash scripts/bootstrap.sh      # create/repair .venv, install all deps
```

Check the environment without starting anything:

```bash
./scripts/launch.sh check-env
```

> **The repository-root `.venv` is the only sanctioned Python environment**
> (`AGENTS.md`). Never create or use `backend/venv` or `backend/.venv`. Always
> invoke Python as a module from the repository root
> (`.venv/bin/python -m runtime.verify ...`), never as a bare script path.

## Other commands

```bash
./scripts/launch.sh status        # process ownership and port state
./scripts/launch.sh health        # process + HTTP health probes
./scripts/launch.sh restart       # deterministic stop then start
./scripts/launch.sh logs [backend|frontend|console]
./scripts/launch.sh help          # full command list
```

Logs are captured under `runtime/generated/launcher/logs/`. PID ownership state
lives under `runtime/generated/launcher/state/`.

## Running a second instance

Defaults are the canonical ports 8000/3000. To avoid a collision:

```bash
CLARIFIN_BACKEND_PORT=8010 CLARIFIN_FRONTEND_PORT=3010 ./start.sh
```

## Verification

```bash
.venv/bin/python -m runtime.verify check     # primary verification
.venv/bin/python -m runtime.verify env-check # environment fingerprint
bash scripts/env-doctor.sh                   # environment diagnostic
```

## Further reading

- [`docs/audits/m10-agent4-canonical-startup.md`](docs/audits/m10-agent4-canonical-startup.md)
  — the operator contract and the real clean-start validation transcript.
- [`docs/audits/m10-agent4-startup-inventory.md`](docs/audits/m10-agent4-startup-inventory.md)
  — every entry point, classified with evidence.
- [`docs/audits/m10-agent4-cleanup-ledger.md`](docs/audits/m10-agent4-cleanup-ledger.md)
  — what was removed, what was kept, and why.
- [`AGENTS.md`](AGENTS.md) — binding canonical-environment rules.