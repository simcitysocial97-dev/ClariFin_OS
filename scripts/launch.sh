#!/bin/bash
# ClariFin OS Launcher (Cross-platform)
# Simple operational entry points for ClariFin OS
#
# Canonical execution contract (M9-C57): all Python runtime commands are invoked
# through the repository-managed .venv and as modules (`python -m runtime.verify`),
# not as bare files. No ambient PATH, no PYTHONPATH hacking.
#
# Local backend development uses `uvicorn` via `-m uvicorn` from the backend
# directory; sys.path[0] = cwd covers `src.*` imports, so no PYTHONPATH is needed.
#
# Process ownership (O-1-B3): each component runs in its own process group
# (via setsid). PID files under runtime/generated/launcher/state/ record
# ownership. `stop` validates before killing, uses graceful+forced teardown,
# and verifies ports released.
#
# Persistent logging (O-1-B5): backend/frontend stdout+stderr are captured to
# runtime/generated/launcher/logs/{backend,frontend}.log (append; size-based
# rotation at 5 MiB, max 3 historical files). Unavailable/unwritable log
# targets abort startup with an explicit diagnostic — a failure to establish
# capture must never produce a false "running" banner.

set -e

# Resolve script location robustly (works for both `bash scripts/launch.sh` and `./scripts/launch.sh`)
if [[ "${BASH_SOURCE[0]}" == "*" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

# B3: Launcher runtime state directory (gitignored, not tracked)
LAUNCHER_STATE_DIR="$REPO_ROOT/runtime/generated/launcher/state"

# B5: Launcher persistent log directory (gitignored, not tracked)
LAUNCHER_LOGS_DIR="$REPO_ROOT/runtime/generated/launcher/logs"

# B5: Log rotation policy — max 3 rotated files per component, 5 MiB threshold
LOG_MAX_ROTATIONS=3
LOG_ROTATE_THRESHOLD_BYTES=$((5 * 1024 * 1024))  # 5 MiB

# B3: Application ports
#
# The canonical ports are 8000/3000. The environment overrides exist so a
# developer (or a parallel validation run) can start a second instance without
# colliding with the canonical one; unset, the canonical ports are used.
BACKEND_PORT="${CLARIFIN_BACKEND_PORT:-8000}"
FRONTEND_PORT="${CLARIFIN_FRONTEND_PORT:-3000}"

# B3: Termination timeouts (seconds)
GRACEFUL_TIMEOUT=5
FORCE_TIMEOUT=2

# B3: Readiness timeouts (seconds)
BACKEND_READY_TIMEOUT=60
FRONTEND_READY_TIMEOUT=90

# Canonical URLs. The Platform Console is a Next.js route served by the
# frontend on FRONTEND_PORT — it is NOT a backend route. The backend only
# exposes the console's JSON API under /platform/v1.
PLATFORM_CONSOLE_URL="http://localhost:${FRONTEND_PORT}/platform/"
PLATFORM_API_URL="http://localhost:${BACKEND_PORT}/platform/v1/health"
FRONTEND_URL="http://localhost:${FRONTEND_PORT}"
BACKEND_URL="http://localhost:${BACKEND_PORT}"

show_help() {
    cat << 'EOF'
ClariFin OS Launcher

This script is the CANONICAL operational entry point for ClariFin OS.
`./start.sh` (Unix/macOS) and `start.bat` (Windows via WSL2) are thin
cross-platform wrappers that delegate here. Nothing else is official.

Canonical startup:
    ./start.sh                      # or: ./scripts/launch.sh start

    validate environment -> start backend -> start frontend
    -> wait for real readiness -> print URLs

Two independent entry points:

    ./start.sh                      Full application
                                    Backend :8000 + Frontend :3000
                                    Application      http://localhost:3000
                                    Platform Console http://localhost:3000/platform/

    ./scripts/launch.sh console     Platform Console ONLY (diagnostic)
                                    Frontend :3000, no backend, no Python
                                    required. Panels needing live data show
                                    an explicit unavailable state.

Canonical shutdown:
    ./scripts/launch.sh stop        Idempotent; safe when nothing is running.
                                    Tears down every process the launcher
                                    spawned and verifies ports are released.

Usage:
    ./scripts/launch.sh <command>

Commands:
    start         Full application: backend (dev/reload) + frontend (prod serve)
    console       Platform Console only, independent of the financial backend
    stop          Deterministically terminate every launcher-owned process
    restart       Stop then start (deterministic lifecycle reset)
    status        Report actual process ownership/state for each component
    health        Check runtime health via process + HTTP probes
    check-env     Validate the environment without starting anything
    logs          Show recently captured runtime output (backend/frontend/console)
                   Usage: ./scripts/launch.sh logs [backend|frontend|console]
    verify        Run the canonical verification suite
    platform      Open the Platform Console in the browser
    help          Show this help message

Examples:
    ./start.sh
    ./scripts/launch.sh start
    ./scripts/launch.sh console
    ./scripts/launch.sh status
    ./scripts/launch.sh health
    ./scripts/launch.sh stop
    ./scripts/launch.sh logs backend
    ./scripts/launch.sh check-env

Verification Commands:
    verify check     Primary verification entrypoint
    verify doctor    Framework health check
    verify status    Current verification status
    verify env-check Canonical environment check
    verify backend   Backend verification profile
    verify frontend  Frontend verification profile
    verify quick     Quick quality gate
    verify mutation  Mutation testing (authoritative or --smoke)

Prerequisites (validate with `./scripts/launch.sh check-env`):
    - Python >= 3.12 in the repository-root .venv
    - Node.js 24 + npm 11.19.0 (frontend/package.json engines/packageManager)
    - frontend/node_modules installed
    - frontend/dist built (production serve path only)
    All of the above are established by: bash scripts/bootstrap.sh

Port overrides (defaults are the canonical ports shown above):
    CLARIFIN_BACKEND_PORT=8010 CLARIFIN_FRONTEND_PORT=3010 ./start.sh
    Use only to run a second instance alongside the canonical one.

EOF
}

# --- Environment validation (AGENTS.md canonical .venv contract) ---
#
# Every start path validates the environment BEFORE spawning any service, so a
# broken environment produces one actionable diagnostic instead of a half-started
# application with an orphaned backend. Checks are additive: all failures are
# reported together, then the command exits non-zero.

VENV_DIR="$REPO_ROOT/.venv"
VENV_PY="$VENV_DIR/bin/python"

_validate_python_env() {
    local problems=0

    if [ ! -e "$VENV_DIR" ]; then
        echo "  MISSING  $VENV_DIR"
        echo "           The repository-root virtualenv does not exist."
        echo "           Fix: bash scripts/bootstrap.sh"
        problems=$((problems + 1))
        return $problems
    fi

    if [ ! -x "$VENV_PY" ]; then
        echo "  BROKEN   $VENV_PY is not executable."
        echo "           The virtualenv exists but has no usable interpreter."
        echo "           Fix: bash scripts/bootstrap.sh   (recreates .venv)"
        problems=$((problems + 1))
        return $problems
    fi

    local py_version
    py_version=$("$VENV_PY" --version 2>&1 | awk '{print $2}')
    echo "  OK       canonical interpreter $VENV_PY (Python $py_version)"

    # Confirm the interpreter is a real venv rooted at the repository, not a
    # stray symlink into some other checkout's environment.
    local venv_prefix
    venv_prefix=$("$VENV_PY" -c 'import sys; print(sys.prefix)' 2>/dev/null || echo "")
    if [ -z "$venv_prefix" ]; then
        echo "  BROKEN   cannot resolve sys.prefix from $VENV_PY"
        problems=$((problems + 1))
    fi

    # Backend import smoke test: uvicorn must be resolvable as a MODULE from the
    # canonical interpreter. This is the exact form the backend is launched with
    # (`python -m uvicorn`), so a failure here predicts the backend failing.
    local missing
    missing=$("$VENV_PY" -c '
import importlib.util, sys
missing = [m for m in ("uvicorn", "fastapi") if importlib.util.find_spec(m) is None]
print(",".join(missing))
' 2>/dev/null || echo "__probe_failed__")

    if [ "$missing" = "__probe_failed__" ]; then
        echo "  BROKEN   could not probe imports from $VENV_PY"
        echo "           Fix: bash scripts/bootstrap.sh"
        problems=$((problems + 1))
    elif [ -n "$missing" ]; then
        echo "  MISSING  backend dependencies not installed: $missing"
        echo "           Fix: bash scripts/bootstrap.sh"
        problems=$((problems + 1))
    else
        echo "  OK       backend dependencies resolvable (uvicorn, fastapi)"
    fi

    # Canonical module execution must not shadow the stdlib `platform` module
    # with runtime/platform (documented AGENTS.md invariant). Verify rather than
    # assume, because breaking it produces baffling downstream failures.
    local shadowed
    shadowed=$("$VENV_PY" -c '
import platform
p = getattr(platform, "__file__", "") or ""
print("SHADOWED" if "/runtime/platform" in p else "OK")
' 2>/dev/null || echo "SHADOWED")
    if [ "$shadowed" = "SHADOWED" ]; then
        echo "  UNSAFE   stdlib platform resolves to runtime/platform"
        echo "           Python commands must run as modules from the repo root"
        echo "           (python -m runtime.verify), never as bare script paths."
        problems=$((problems + 1))
    else
        echo "  OK       stdlib platform not shadowed by runtime/platform"
    fi

    return $problems
}

_validate_node_env() {
    local problems=0

    if ! command -v node >/dev/null 2>&1; then
        echo "  MISSING  node not found on PATH"
        echo "           Node.js 24 is required (see frontend/package.json engines)."
        echo "           Fix: install Node 24, then re-run bash scripts/bootstrap.sh"
        problems=$((problems + 1))
        return $problems
    fi

    local node_version
    node_version=$(node --version 2>/dev/null || echo "v0.0.0")
    # Mirror the contract enforced by scripts/bootstrap.sh and frontend engines.
    if ! echo "$node_version" | grep -qE '^v24\.'; then
        echo "  BROKEN   Node $node_version found; Node 24 is required."
        echo "           Fix: install Node 24, then re-run bash scripts/bootstrap.sh"
        problems=$((problems + 1))
        return $problems
    fi
    echo "  OK       $node_version"

    if ! command -v npm >/dev/null 2>&1; then
        echo "  MISSING  npm not found on PATH"
        problems=$((problems + 1))
        return $problems
    fi

    if [ ! -d "$REPO_ROOT/frontend/node_modules" ]; then
        echo "  MISSING  frontend/node_modules is absent"
        echo "           Fix: bash scripts/bootstrap.sh   (runs npm ci)"
        problems=$((problems + 1))
    else
        echo "  OK       frontend/node_modules present"
    fi

    return $problems
}

# Validate that a production build exists for the production-serve path.
# Kept separate from _validate_node_env so `console` (frontend-only diagnostic)
# can skip it when the developer intends Next.js dev mode instead.
_validate_frontend_build() {
    if [ ! -d "$REPO_ROOT/frontend/dist" ]; then
        echo "  MISSING  frontend/dist is absent"
        echo "           next.config.ts sets distDir='dist', so `npm run build`"
        echo "           writes the production build to frontend/dist."
        echo "           Fix: (cd frontend && npm run build)"
        return 1
    fi
    echo "  OK       frontend/dist present (production build available)"
    return 0
}

# $1 = label for the banner, $2 = "full" | "console"
validate_environment() {
    local mode="${2:-full}"
    echo "───────────────────────────────────────────────────────────"
    echo "  Validating environment ($mode)"
    echo "───────────────────────────────────────────────────────────"

    local problems=0

    echo "Python (canonical .venv):"
    local py_problems
    # _validate_* return the problem count, so capture it before it is lost.
    py_problems=0
    _validate_python_env || py_problems=$?
    problems=$((problems + py_problems))

    echo ""
    echo "Node / frontend:"
    local node_problems=0
    _validate_node_env || node_problems=$?
    problems=$((problems + node_problems))

    if [ "$mode" = "full" ]; then
        echo ""
        echo "Frontend build:"
        _validate_frontend_build || problems=$((problems + 1))
    fi

    echo ""
    if [ "$problems" -ne 0 ]; then
        echo "───────────────────────────────────────────────────────────"
        echo "  ENVIRONMENT NOT READY — $problems problem(s) above."
        echo "  Fix the reported items and retry. No services were started."
        echo "───────────────────────────────────────────────────────────"
        return 1
    fi

    echo "  Environment OK."
    return 0
}

# --- B5: Persistent log management ---

_ensure_log_dir() {
    if ! mkdir -p "$LAUNCHER_LOGS_DIR" 2>/dev/null; then
        echo "ERROR: cannot create log directory: $LAUNCHER_LOGS_DIR (check permissions)." >&2
        return 1
    fi
    # Verify the directory is actually writable (mkdir -p on an existing dir
    # silently succeeds even when it is not).
    local probe="$LAUNCHER_LOGS_DIR/.write_probe"
    if ! touch "$probe" 2>/dev/null; then
        echo "ERROR: log directory is not writable: $LAUNCHER_LOGS_DIR (check permissions)." >&2
        rm -f "$probe" 2>/dev/null
        return 1
    fi
    rm -f "$probe"
    return 0
}

# Rotate a component's log file if it exceeds the retention threshold.
# Policy: current.log → current.log.1 → current.log.2 → current.log.3 (oldest discarded)
# Only rotates when file size exceeds LOG_ROTATE_THRESHOLD_BYTES.
_rotate_log() {
    local component=$1
    local log_file="$LAUNCHER_LOGS_DIR/${component}.log"

    [ -f "$log_file" ] || return 0

    local size
    size=$(stat -c%s "$log_file" 2>/dev/null || echo 0)
    if [ "$size" -ge "$LOG_ROTATE_THRESHOLD_BYTES" ]; then
        local i=$LOG_MAX_ROTATIONS
        while [ "$i" -gt 1 ]; do
            local prev=$((i - 1))
            [ -f "${log_file}.${prev}" ] && mv "${log_file}.${prev}" "${log_file}.${i}"
            i=$((i - 1))
        done
        mv "$log_file" "${log_file}.1"
        touch "$log_file"
        echo "  $component: log rotated (${size} bytes → .1, fresh log created)"
    fi
}

# B5: Fail fast if the component's log file cannot be opened for append.
# Uses the same open mode as the launch redirect (>> file 2>&1), so this check
# cannot pass while the actual capture would fail. Per O-1-B5 failure
# semantics, an unavailable log target must fail startup explicitly and
# diagnostically — never allow a false "running" banner.
_ensure_component_log() {
    local component=$1
    local log_file="$LAUNCHER_LOGS_DIR/${component}.log"
    if ! printf '' 2>/dev/null >> "$log_file"; then
        echo "ERROR: cannot write log file: $log_file (check permissions/ownership)." >&2
        echo "       Aborting $component start: persistent log capture is mandatory." >&2
        return 1
    fi
    return 0
}

# --- B3: PID / process-group management ---

_ensure_state_dir() {
    mkdir -p "$LAUNCHER_STATE_DIR"
}

_write_pid() {
    local component=$1
    local pid=$2
    echo "$pid" > "$LAUNCHER_STATE_DIR/${component}.pid"
}

_read_pid() {
    local component=$1
    local pidfile="$LAUNCHER_STATE_DIR/${component}.pid"
    if [ -f "$pidfile" ]; then
        cat "$pidfile"
    fi
}

_remove_pid() {
    local component=$1
    rm -f "$LAUNCHER_STATE_DIR/${component}.pid"
}

# Discover the actual serving process within a recorded PID's session group.
# Some applications (npm, uvicorn --reload) fork children that outlive the session leader.
# Returns the PID of the deepest descendant still running the expected command, or empty.
_discover_serving_pid() {
    local component=$1
    local leader_pid=$2

    # If leader is alive, return it
    if kill -0 "$leader_pid" 2>/dev/null; then
        echo "$leader_pid"
        return
    fi

    # Leader dead — find descendants in the same session that match the component pattern
    case "$component" in
        backend)
            # Find all PIDs in the session, then check which ones are still uvicorn workers
            ps -g "$leader_pid" -o pid= 2>/dev/null | while read -r member; do
                [ -z "$member" ] && continue
                kill -0 "$member" 2>/dev/null || continue
                local args
                args=$(ps -o args= -p "$member" 2>/dev/null || echo "")
                if echo "$args" | grep -q "uvicorn.*src\.api:app"; then
                    echo "$member"
                    return
                fi
            done
            ;;
        frontend|console)
            ps -g "$leader_pid" -o pid= 2>/dev/null | while read -r member; do
                [ -z "$member" ] && continue
                kill -0 "$member" 2>/dev/null || continue
                local args
                args=$(ps -o args= -p "$member" 2>/dev/null || echo "")
                if echo "$args" | grep -qE "next-server|next start|next dev"; then
                    echo "$member"
                    return
                fi
            done
            ;;
    esac
}

# Validate that a stored PID is still alive AND still belongs to our process group.
# Also checks for descendant processes when the leader has exited.
# Returns 0 if valid, 1 if stale/reused.
_validate_owned_process() {
    local component=$1
    local stored_pid=$2

    # Case A: Direct validation — PID alive, PGID matches, cmdline matches
    if kill -0 "$stored_pid" 2>/dev/null; then
        local current_pgid
        current_pgid=$(ps -o pgid= -p "$stored_pid" 2>/dev/null | xargs)
        if [ -z "$current_pgid" ] || [ "$current_pgid" != "$stored_pid" ]; then
            return 1
        fi
        local cmdline
        cmdline=$(ps -o args= -p "$stored_pid" 2>/dev/null || echo "")
        case "$component" in
            backend)
                echo "$cmdline" | grep -q "uvicorn.*src\.api:app" || return 1
                ;;
            frontend|console)
                echo "$cmdline" | grep -qE "npm|next" || return 1
                ;;
        esac
        return 0
    fi

    # Case B: Leader dead — check for surviving descendants in the same session
    local serving_pid
    serving_pid=$(_discover_serving_pid "$component" "$stored_pid")
    if [ -n "$serving_pid" ]; then
        # Descendant found — validate it
        local d_pgid
        d_pgid=$(ps -o pgid= -p "$serving_pid" 2>/dev/null | xargs)
        # Descendant should share the same PGID as the original session leader
        if [ -n "$d_pgid" ] && [ "$d_pgid" = "$stored_pid" ]; then
            return 0
        fi
        # Even if PGID drifted, if it's still in the same session and matches the command, accept it
        local d_cmdline
        d_cmdline=$(ps -o args= -p "$serving_pid" 2>/dev/null || echo "")
        case "$component" in
            backend)
                echo "$d_cmdline" | grep -q "uvicorn.*src\.api:app" && return 0
                ;;
            frontend|console)
                echo "$d_cmdline" | grep -qE "next-server|next start|next dev" && return 0
                ;;
        esac
    fi

    return 1
}

# Gracefully terminate one owned component. Handles all PID cases (A/B/C).
# Also handles the case where the recorded PID has died but child processes
# in the same process group are still running.
_terminate_component() {
    local component=$1
    local pid
    pid=$(_read_pid "$component")

    if [ -z "$pid" ]; then
        echo "  $component: no PID record found"
        return 0
    fi

    if _validate_owned_process "$component" "$pid"; then
        echo "  $component: terminating PID $pid (PGID=$pid)..."
        # Send SIGTERM to the entire process group
        kill -TERM -- -"$pid" 2>/dev/null || true

        # Wait for graceful exit (bounded)
        local elapsed=0
        while [ "$elapsed" -lt "$GRACEFUL_TIMEOUT" ]; do
            if ! kill -0 "$pid" 2>/dev/null; then
                echo "  $component: exited gracefully (${elapsed}s)"
                _remove_pid "$component"
                return 0
            fi
            sleep 1
            elapsed=$((elapsed + 1))
        done

        # Force kill if still alive
        if kill -0 "$pid" 2>/dev/null; then
            echo "  $component: force-killing (exceeded ${GRACEFUL_TIMEOUT}s graceful timeout)..."
            kill -KILL -- -"$pid" 2>/dev/null || true
            sleep "$FORCE_TIMEOUT"
            _remove_pid "$component"
            return 0
        fi

        echo "  $component: terminated"
        _remove_pid "$component"
        return 0
    else
        # Recorded PID is stale or unowned.
        # SAFE POLICY: never terminate a live unrelated process.
        if kill -0 "$pid" 2>/dev/null; then
            # PID alive but ownership validation failed (PGID or cmdline mismatch).
            # This is UNOWNED — preserve the process, only remove the PID file.
            echo "  $component: unowned PID $pid preserved (ownership mismatch)"
            _remove_pid "$component"
            return 0
        fi

        # PID is dead — check for orphan descendants still occupying the port.
        # Candidates are restricted to listeners on this launcher's port and
        # re-validated per PID, so an unrelated server is never signalled.
        local cleaned=false
        local comp_port
        case "$component" in
            backend)  comp_port="$BACKEND_PORT" ;;
            *)        comp_port="$FRONTEND_PORT" ;;
        esac

        local orphan_procs=""
        local opid
        for opid in $(_port_listener_pids "$comp_port"); do
            [ "$opid" = "$pid" ] && continue
            if _port_listener_is_ours "$component" "$opid"; then
                orphan_procs="$orphan_procs $opid"
            fi
        done

        if [ -n "$orphan_procs" ]; then
            echo "  $component: cleaning orphan processes on port $comp_port:$orphan_procs"
            for opid in $orphan_procs; do
                kill -TERM "$opid" 2>/dev/null || true
            done
            sleep 1
            for opid in $orphan_procs; do
                kill -0 "$opid" 2>/dev/null && kill -KILL "$opid" 2>/dev/null || true
            done
            cleaned=true
        fi

        if [ "$cleaned" = true ]; then
            echo "  $component: PID $pid cleared (orphans cleaned)"
        else
            echo "  $component: stale PID $pid cleared"
        fi
        _remove_pid "$component"
        return 0
    fi
}

# --- B3: Port preflight ---

# Returns 0 when FRONTEND_PORT is free. The console command uses this on its own
# so an already-running frontend is detected without demanding the backend port.
_preflight_frontend_port() {
    ss -tlnp 2>/dev/null | grep -E ":${FRONTEND_PORT} " >/dev/null 2>&1 && return 1
    return 0
}

_preflight_ports() {
    local has_conflict=false

    local backend_owner
    backend_owner=$(ss -tlnp 2>/dev/null | grep -E ":${BACKEND_PORT} " || true)
    if [ -n "$backend_owner" ]; then
        echo "  Backend port $BACKEND_PORT occupied: $backend_owner"
        has_conflict=true
    fi

    local frontend_owner
    frontend_owner=$(ss -tlnp 2>/dev/null | grep -E ":${FRONTEND_PORT} " || true)
    if [ -n "$frontend_owner" ]; then
        echo "  Frontend port $FRONTEND_PORT occupied: $frontend_owner"
        has_conflict=true
    fi

    if [ "$has_conflict" = true ]; then
        return 1
    fi
    return 0
}

# --- B3: Orphan detection ---

# Return the PIDs currently LISTENING on the given port.
#
# Deliberately port-scoped rather than command-line-scoped. The previous
# implementation swept processes with `pgrep -f "next-server|next start"`, which
# matches every Next.js server on the machine regardless of port — so `stop`
# could terminate a developer's unrelated project. Restricting candidates to
# the ports this launcher instance owns makes teardown incapable of reaching
# another process. Ownership is still confirmed per-PID before any signal.
_port_listener_pids() {
    local port="$1"
    ss -tlnp 2>/dev/null \
        | grep -E ":${port}[[:space:]]" \
        | grep -oE 'pid=[0-9]+' \
        | cut -d= -f2 \
        | sort -u
}

# True when the PID is a plausible ClariFin component for this launcher:
# it must both answer on the expected port and look like the expected command.
_port_listener_is_ours() {
    local component="$1"
    local pid="$2"
    local args
    args=$(ps -o args= -p "$pid" 2>/dev/null || echo "")
    [ -n "$args" ] || return 1
    case "$component" in
        backend)
            echo "$args" | grep -q "uvicorn.*src\.api:app"
            ;;
        frontend|console)
            echo "$args" | grep -qE "next-server|next start|next dev"
            ;;
        *)
            return 1
            ;;
    esac
}

_detect_orphans() {
    local orphans=()

    local component port recorded pid
    for component in backend frontend console; do
        case "$component" in
            backend)  port="$BACKEND_PORT" ;;
            *)        port="$FRONTEND_PORT" ;;
        esac

        recorded=$(_read_pid "$component")
        for pid in $(_port_listener_pids "$port"); do
            if [ -n "$recorded" ] && [ "$pid" = "$recorded" ]; then
                continue
            fi
            if _port_listener_is_ours "$component" "$pid"; then
                orphans+=("$component: PID $pid on port $port not tracked by this launcher")
            fi
        done
    done

    if [ ${#orphans[@]} -gt 0 ]; then
        echo "Orphan ClariFin_OS processes detected on this launcher's ports:"
        for o in "${orphans[@]}"; do
            echo "  $o"
        done
        echo "  Run './scripts/launch.sh stop' to clean up."
        return 1
    fi

    return 0
}

# --- B3: Stale-state cleanup ---

_clean_stale_state() {
    for component in backend frontend console; do
        local pid
        pid=$(_read_pid "$component")
        if [ -n "$pid" ]; then
            if ! kill -0 "$pid" 2>/dev/null; then
                echo "  Cleaning stale PID for $component: $pid (process gone)"
                _remove_pid "$component"
            else
                local current_pgid
                current_pgid=$(ps -o pgid= -p "$pid" 2>/dev/null | xargs)
                if [ -n "$current_pgid" ] && [ "$current_pgid" != "$pid" ]; then
                    echo "  Cleaning stale PID for $component: $pid (PGID mismatch: $current_pgid)"
                    _remove_pid "$component"
                fi
            fi
        fi
    done
}

# --- B3: Stop command ---

# Single source of truth for the post-start banner, so `start` and `restart`
# cannot drift and disagree about which URLs are live.
_print_running_banner() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  ClariFin OS is running."
    echo ""
    echo "  Application        $FRONTEND_URL"
    echo "  Platform Console   $PLATFORM_CONSOLE_URL"
    echo "  Backend API        $BACKEND_URL"
    echo "  API Docs           $BACKEND_URL/docs"
    echo "  Health / Readiness $BACKEND_URL/health  $BACKEND_URL/ready"
    echo ""
    echo "  Stop: ./scripts/launch.sh stop    (or Ctrl+C in this terminal)"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
}

_stop() {
    echo "═══════════════════════════════════════════════════════════"
    echo "  ClariFin OS — Stopping"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    _ensure_state_dir

    # Console is an independently-started surface that may be running alone, so
    # it participates in the same ownership/teardown contract as the app pair.
    local had_backend=false
    local had_frontend=false
    local had_console=false
    [ -n "$(_read_pid backend)" ] && had_backend=true
    [ -n "$(_read_pid frontend)" ] && had_frontend=true
    [ -n "$(_read_pid console)" ] && had_console=true

    if [ "$had_backend" = false ] && [ "$had_frontend" = false ] && [ "$had_console" = false ]; then
        echo "No owned processes recorded."
        # Quarantine any stray stale files
        rm -f "$LAUNCHER_STATE_DIR"/*.pid 2>/dev/null || true
        echo ""
        echo "═══════════════════════════════════════════════════════════"
        echo "  ClariFin OS is not running (or already stopped)."
        echo "═══════════════════════════════════════════════════════════"
        return 0
    fi

    echo "Terminating owned processes..."
    echo ""

    # Console first: it is a diagnostic surface independent of the financial app.
    if [ "$had_console" = true ]; then
        _terminate_component console
    fi

    # Terminate backend first (frontend depends on it)
    if [ "$had_backend" = true ]; then
        _terminate_component backend
    fi

    # Then frontend
    if [ "$had_frontend" = true ]; then
        _terminate_component frontend
    fi

    echo ""

    # Verify ports released; attempt orphan cleanup if needed
    local backend_free=true
    local frontend_free=true
    ss -tlnp 2>/dev/null | grep -qE ":${BACKEND_PORT} " && backend_free=false
    ss -tlnp 2>/dev/null | grep -qE ":${FRONTEND_PORT} " && frontend_free=false

    if [ "$backend_free" = false ] || [ "$frontend_free" = false ]; then
        echo "Some ports still occupied. Attempting orphan cleanup..."
        # Port-scoped and re-validated per PID: only listeners on this
        # launcher's own ports that also match the expected component command
        # are signalled. An unrelated service on another port is never touched.
        local orphans_killed=false
        local comp port op
        for comp in backend frontend console; do
            case "$comp" in
                backend)  port="$BACKEND_PORT" ;;
                *)        port="$FRONTEND_PORT" ;;
            esac
            [ "$port" = "$BACKEND_PORT" ] && [ "$backend_free" = true ] && continue
            [ "$port" = "$FRONTEND_PORT" ] && [ "$frontend_free" = true ] && continue
            for op in $(_port_listener_pids "$port"); do
                _port_listener_is_ours "$comp" "$op" || continue
                echo "  Killing $comp orphan on port $port: $op"
                kill -TERM "$op" 2>/dev/null || true
            done
            orphans_killed=true
        done
        [ "$orphans_killed" = true ] && sleep "$FORCE_TIMEOUT"
        for op in $(_port_listener_pids "$BACKEND_PORT"); do
            _port_listener_is_ours backend "$op" || continue
            kill -0 "$op" 2>/dev/null && kill -KILL "$op" 2>/dev/null || true
        done
        for op in $(_port_listener_pids "$FRONTEND_PORT"); do
            _port_listener_is_ours frontend "$op" || continue
            kill -0 "$op" 2>/dev/null && kill -KILL "$op" 2>/dev/null || true
        done

        # Re-check
        ss -tlnp 2>/dev/null | grep -qE ":${BACKEND_PORT} " && backend_free=false
        ss -tlnp 2>/dev/null | grep -qE ":${FRONTEND_PORT} " && frontend_free=false
    fi

    if [ "$backend_free" = true ] && [ "$frontend_free" = true ]; then
        echo "Ports released: $BACKEND_PORT (backend), $FRONTEND_PORT (frontend)"
    else
        echo "WARNING: Ports may still be in use:"
        [ "$backend_free" = false ] && echo "  $BACKEND_PORT (backend) still occupied"
        [ "$frontend_free" = false ] && echo "  $FRONTEND_PORT (frontend) still occupied"
    fi

    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  ClariFin OS stopped."
    echo "═══════════════════════════════════════════════════════════"
}

# --- B4: Status command ---

# Determine the state of a single component.
# Outputs: RUNNING | STOPPED | STALE | UNOWNED | UNKNOWN
_get_component_state() {
    local component=$1
    local pid
    pid=$(_read_pid "$component")

    if [ -z "$pid" ]; then
        echo "STOPPED"
        return
    fi

    # Check if the recorded PID or any descendant is still alive and owned
    if _validate_owned_process "$component" "$pid"; then
        # Find the actual serving PID for display
        local serving_pid
        serving_pid=$(_discover_serving_pid "$component" "$pid")
        if [ -n "$serving_pid" ] && [ "$serving_pid" != "$pid" ]; then
            # Show the actual serving PID but report RUNNING
            echo "RUNNING"
        else
            echo "RUNNING"
        fi
        return
    fi

    # Not validated — determine why
    if kill -0 "$pid" 2>/dev/null; then
        # PID alive but ownership failed
        echo "UNOWNED"
    else
        # PID dead, no surviving descendants
        echo "STALE"
    fi
}

# Check if a port is occupied by the expected owned process (by PID or PGID).
_port_occupied_by_owner() {
    local component=$1
    local port=$2
    local pid
    pid=$(_read_pid "$component")

    if [ -z "$pid" ]; then
        return 1
    fi

    # Check if the PID's process group is listening on the port
    local owner
    owner=$(ss -tlnp 2>/dev/null | grep -E ":${port} " || true)
    if [ -z "$owner" ]; then
        return 1
    fi

    # Direct PID match
    if echo "$owner" | grep -q "pid=$pid"; then
        return 0
    fi

    # PGID match: use `ps -g` (session/group leader) to find all members
    # Note: `ps -G` (numeric PGID) is unreliable on some systems; use -g with leader PID.
    local members
    members=$(ps -g "$pid" -o pid= 2>/dev/null | xargs || echo "")
    for member_pid in $members; do
        if echo "$owner" | grep -q "pid=$member_pid"; then
            return 0
        fi
    done

    return 1
}

cmd_status() {
    _ensure_state_dir

    local backend_state frontend_state
    backend_state=$(_get_component_state backend)
    frontend_state=$(_get_component_state frontend)

    echo "═══════════════════════════════════════════════════════════"
    echo "  ClariFin OS — Lifecycle Status"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    # Backend status
    echo "Backend (:$BACKEND_PORT)"
    local b_pid b_pgid b_cmd b_serving
    b_pid=$(_read_pid backend)
    b_serving=$(_discover_serving_pid backend "$b_pid")
    local b_display_pid="${b_serving:-${b_pid:-n/a}}"
    b_pgid=$([ -n "$b_display_pid" ] && ps -o pgid= -p "$b_display_pid" 2>/dev/null | xargs || echo "")
    b_cmd=$([ -n "$b_display_pid" ] && ps -o args= -p "$b_display_pid" 2>/dev/null || echo "")
    echo "  State:      $backend_state"
    echo "  PID:        ${b_display_pid:-n/a}"
    echo "  PGID:       ${b_pgid:-n/a}"
    echo "  Command:    ${b_cmd:-n/a}"
    if [ "$backend_state" = "RUNNING" ]; then
        if _port_occupied_by_owner backend "$BACKEND_PORT"; then
            echo "  Port:       $BACKEND_PORT — occupied by owned process"
        else
            echo "  Port:       $BACKEND_PORT — occupied (unverified owner)"
        fi
    else
        local b_port_state
        b_port_state=$(ss -tlnp 2>/dev/null | grep -E ":${BACKEND_PORT} " || echo "free")
        echo "  Port:       $BACKEND_PORT — $b_port_state"
    fi
    echo ""

    # Frontend status
    echo "Frontend (:$FRONTEND_PORT)"
    local f_pid f_pgid f_cmd f_serving
    f_pid=$(_read_pid frontend)
    f_serving=$(_discover_serving_pid frontend "$f_pid")
    local f_display_pid="${f_serving:-${f_pid:-n/a}}"
    f_pgid=$([ -n "$f_display_pid" ] && ps -o pgid= -p "$f_display_pid" 2>/dev/null | xargs || echo "")
    f_cmd=$([ -n "$f_display_pid" ] && ps -o args= -p "$f_display_pid" 2>/dev/null || echo "")
    echo "  State:      $frontend_state"
    echo "  PID:        ${f_display_pid:-n/a}"
    echo "  PGID:       ${f_pgid:-n/a}"
    echo "  Command:    ${f_cmd:-n/a}"
    if [ "$frontend_state" = "RUNNING" ]; then
        if _port_occupied_by_owner frontend "$FRONTEND_PORT"; then
            echo "  Port:       $FRONTEND_PORT — occupied by owned process"
        else
            echo "  Port:       $FRONTEND_PORT — occupied (unverified owner)"
        fi
    else
        local f_port_state
        f_port_state=$(ss -tlnp 2>/dev/null | grep -E ":${FRONTEND_PORT} " || echo "free")
        echo "  Port:       $FRONTEND_PORT — $f_port_state"
    fi
    echo ""

    # Summary
    echo "───────────────────────────────────────────────────────────"
    local all_running=true
    [ "$backend_state" != "RUNNING" ] && all_running=false
    [ "$frontend_state" != "RUNNING" ] && all_running=false

    if [ "$all_running" = true ]; then
        echo "  Overall:    Application RUNNING"
    elif [ "$backend_state" = "RUNNING" ] || [ "$frontend_state" = "RUNNING" ]; then
        echo "  Overall:    PARTIAL (backend=$backend_state, frontend=$frontend_state)"
    else
        echo "  Overall:    STOPPED"
    fi
    echo "═══════════════════════════════════════════════════════════"

    if [ "$all_running" = true ]; then
        return 0
    elif [ "$backend_state" = "STALE" ] || [ "$frontend_state" = "STALE" ] || \
         [ "$backend_state" = "UNOWNED" ] || [ "$frontend_state" = "UNOWNED" ]; then
        return 1
    else
        return 2
    fi
}

# --- B4: Restart command ---

cmd_restart() {
    echo "═══════════════════════════════════════════════════════════"
    echo "  ClariFin OS — Restart"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    # Step 1: Deterministic stop
    _stop
    echo ""

    # Step 2: Verify stopped / ports released
    echo "Verifying clean state..."
    _ensure_state_dir

    local still_running=false
    for component in backend frontend; do
        local pid
        pid=$(_read_pid "$component")
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "  WARNING: $component PID $pid still alive after stop"
            still_running=true
        fi
    done

    local ports_free=true
    ss -tlnp 2>/dev/null | grep -qE ":${BACKEND_PORT} " && ports_free=false
    ss -tlnp 2>/dev/null | grep -qE ":${FRONTEND_PORT} " && ports_free=false

    if [ "$still_running" = true ] || [ "$ports_free" = false ]; then
        echo "  Attempting orphan cleanup..."
        # Force-kill any remaining uvicorn or next-server processes
        local bp_remaining
        # Port-scoped and re-validated per PID (see _port_listener_pids): a
        # machine-wide command-line match could kill another project's server.
        bp_remaining=$(_port_listener_pids "$BACKEND_PORT")
        for op in $bp_remaining; do
            _port_listener_is_ours backend "$op" || continue
            echo "  Force-killing backend orphan on port $BACKEND_PORT: $op"
            kill -KILL "$op" 2>/dev/null || true
        done
        local fp_remaining
        fp_remaining=$(_port_listener_pids "$FRONTEND_PORT")
        for op in $fp_remaining; do
            _port_listener_is_ours frontend "$op" || continue
            echo "  Force-killing frontend orphan on port $FRONTEND_PORT: $op"
            kill -KILL "$op" 2>/dev/null || true
        done
        sleep "$FORCE_TIMEOUT"

        # Re-check
        still_running=false
        for component in backend frontend; do
            local pid
            pid=$(_read_pid "$component")
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                still_running=true
            fi
        done
        ports_free=true
        ss -tlnp 2>/dev/null | grep -qE ":${BACKEND_PORT} " && ports_free=false
        ss -tlnp 2>/dev/null | grep -qE ":${FRONTEND_PORT} " && ports_free=false

        if [ "$still_running" = true ] || [ "$ports_free" = false ]; then
            echo ""
            echo "Restart aborted: could not achieve clean state after orphan cleanup."
            echo "Run './scripts/launch.sh stop' manually before retrying."
            return 1
        fi
        echo "  Orphan cleanup successful."
    else
        echo "  Clean state verified."
    fi
    echo ""

    # Step 3: Canonical start
    echo "Starting ClariFin OS..."
    echo ""

    # Port preflight
    echo "Preflight checks..."
    if ! _preflight_ports; then
        echo ""
        echo "Aborting restart: port conflict(s) detected."
        return 1
    fi
    echo "  Ports $BACKEND_PORT and $FRONTEND_PORT available."
    echo ""

    # Stale cleanup
    _clean_stale_state
    echo ""

    # Start backend
    start_backend || {
        echo "Backend failed to start."
        return 1
    }
    BACKEND_PID=$(_read_pid backend)

    echo "Waiting for backend to be ready..."
    if ! _wait_for_backend_ready; then
        echo "Last captured log lines:"
        tail -20 "$LAUNCHER_LOGS_DIR/backend.log" 2>/dev/null || echo "  (no log captured)"
        echo "Backend failed to start. Cleaning up..."
        _terminate_component backend
        return 1
    fi
    echo ""

    # Start frontend
    serve_frontend || {
        echo "Frontend failed to start. Cleaning up owned processes..."
        _terminate_component backend
        return 1
    }
    FRONTEND_PID=$(_read_pid frontend)

    echo "Waiting for frontend to be ready..."
    if ! _wait_for_frontend_ready; then
        echo "Last captured log lines:"
        tail -20 "$LAUNCHER_LOGS_DIR/frontend.log" 2>/dev/null || echo "  (no log captured)"
        echo "Frontend failed to start. Cleaning up owned processes..."
        _terminate_component frontend
        _terminate_component backend
        return 1
    fi

    echo ""
    echo "  ClariFin OS restarted successfully."
    echo ""
    _print_running_banner

    return 0
}

# --- B4: Health command ---

_health_check_backend_process() {
    local pid
    pid=$(_read_pid backend)
    if [ -z "$pid" ]; then
        echo "FAIL (no PID record)"
        return 1
    fi
    local serving_pid
    serving_pid=$(_discover_serving_pid backend "$pid")
    local display_pid="${serving_pid:-$pid}"
    if _validate_owned_process backend "$pid"; then
        echo "PASS (PID=$display_pid)"
        return 0
    else
        echo "FAIL (PID=$display_pid not owned)"
        return 1
    fi
}

_health_check_backend_http() {
    local code
    code=$(_http_code "$BACKEND_URL/health")
    if [ "$code" = "200" ]; then
        echo "PASS (HTTP $code)"
        return 0
    else
        echo "FAIL (HTTP $code)"
        return 1
    fi
}

_health_check_backend_ready() {
    local code
    code=$(_http_code "$BACKEND_URL/ready")
    if [ "$code" = "200" ]; then
        echo "PASS (HTTP $code)"
        return 0
    elif [ "$code" = "503" ]; then
        echo "FAIL (HTTP $code — not ready)"
        return 1
    else
        echo "FAIL (HTTP $code)"
        return 1
    fi
}

_health_check_frontend_process() {
    local pid
    pid=$(_read_pid frontend)
    if [ -z "$pid" ]; then
        echo "FAIL (no PID record)"
        return 1
    fi
    local serving_pid
    serving_pid=$(_discover_serving_pid frontend "$pid")
    local display_pid="${serving_pid:-$pid}"
    if _validate_owned_process frontend "$pid"; then
        echo "PASS (PID=$display_pid)"
        return 0
    else
        echo "FAIL (PID=$display_pid not owned)"
        return 1
    fi
}

_health_check_frontend_http() {
    local code
    code=$(_http_code "$FRONTEND_URL/")
    if echo "$code" | grep -qE '^[23]'; then
        echo "PASS (HTTP $code)"
        return 0
    else
        echo "FAIL (HTTP $code)"
        return 1
    fi
}

cmd_health() {
    _ensure_state_dir

    echo "═══════════════════════════════════════════════════════════"
    echo "  ClariFin OS — Health Check"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    local overall_pass=true

    # Backend process
    echo "Backend:"
    local bp_result
    bp_result=$(_health_check_backend_process) || true
    echo "  Process        $bp_result"
    if echo "$bp_result" | grep -q "^FAIL"; then overall_pass=false; fi

    # Backend /health
    local bh_result
    bh_result=$(_health_check_backend_http) || true
    echo "  /health        $bh_result"
    if echo "$bh_result" | grep -q "^FAIL"; then overall_pass=false; fi

    # Backend /ready
    local br_result
    br_result=$(_health_check_backend_ready) || true
    echo "  /ready         $br_result"
    if echo "$br_result" | grep -q "^FAIL"; then overall_pass=false; fi

    echo ""

    # Frontend process
    echo "Frontend:"
    local fp_result
    fp_result=$(_health_check_frontend_process) || true
    echo "  Process        $fp_result"
    if echo "$fp_result" | grep -q "^FAIL"; then overall_pass=false; fi

    # Frontend HTTP
    local fh_result
    fh_result=$(_health_check_frontend_http) || true
    echo "  HTTP (:${FRONTEND_PORT})   $fh_result"
    if echo "$fh_result" | grep -q "^FAIL"; then overall_pass=false; fi

    echo ""
    echo "───────────────────────────────────────────────────────────"

    if [ "$overall_pass" = true ]; then
        echo "  Overall        HEALTHY"
    else
        echo "  Overall        UNHEALTHY"
    fi
    echo "═══════════════════════════════════════════════════════════"

    if [ "$overall_pass" = true ]; then
        return 0
    else
        return 1
    fi
}

# --- B4: Logs command ---

cmd_logs() {
    local component="${2:-}"
    _ensure_log_dir

    echo "═══════════════════════════════════════════════════════════"
    echo "  ClariFin OS — Logs"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    if [ -z "$component" ]; then
        # Show all available logs (bounded tail)
        local found=false
        for f in "$LAUNCHER_LOGS_DIR"/*.log; do
            [ -f "$f" ] || continue
            found=true
            local bname
            bname=$(basename "$f")
            echo "— $bname —"
            tail -50 "$f" 2>/dev/null || echo "  (empty)"
            echo ""
        done
        if [ "$found" = false ]; then
            echo "No log files found in $LAUNCHER_LOGS_DIR."
            echo "Start the application to begin capturing output."
        fi
    elif [ "$component" = "backend" ] || [ "$component" = "frontend" ]; then
        local log_file="$LAUNCHER_LOGS_DIR/${component}.log"
        if [ -f "$log_file" ]; then
            echo "— ${component}.log —"
            tail -100 "$log_file"
        else
            echo "No log file found for $component at $log_file."
            echo "Start the application to begin capturing output."
        fi
    else
        echo "Unknown component: $component"
        echo "Usage: ./scripts/launch.sh logs [backend|frontend]"
        return 1
    fi

    echo ""
    echo "═══════════════════════════════════════════════════════════"
    return 0
}

# --- Readiness gating ---
#
# Print the HTTP status code for a URL, or "000" when the connection fails.
#
# curl already writes "000" to stdout when it cannot connect, but it does so
# while also exiting non-zero. A `|| echo "000"` fallback therefore appended a
# SECOND "000" and reports surfaced as "HTTP 000000". This helper keeps a single
# authoritative value and always exits 0 so callers can use it in `$( )`.
_http_code() {
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" "$1" 2>/dev/null) || true
    [ -n "$code" ] || code="000"
    printf '%s' "$code"
}

# Readiness is proven by polling a real endpoint until it answers, never by
# sleeping a fixed interval. /ready is the backend's canonical readiness probe
# (backend/src/health.py:38): it verifies database connectivity and required
# directories and answers 503 until they are satisfied. The previous /docs probe
# answered 200 from a static Swagger page and therefore proved only that the
# socket was open, not that the application was usable.

_wait_for_backend_ready() {
    local elapsed=0
    local code="000"
    while [ "$elapsed" -lt "$BACKEND_READY_TIMEOUT" ]; do
        code=$(_http_code "$BACKEND_URL/ready")
        if [ "$code" = "200" ]; then
            echo "Backend is ready (GET /ready -> 200) after ${elapsed}s."
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    echo "Backend did not become ready within ${BACKEND_READY_TIMEOUT}s (last /ready -> $code)."
    return 1
}

_wait_for_frontend_ready() {
    local elapsed=0
    local code="000"
    while [ "$elapsed" -lt "$FRONTEND_READY_TIMEOUT" ]; do
        code=$(_http_code "$FRONTEND_URL/")
        case "$code" in
            2*|3*)
                echo "Frontend is ready (GET / -> $code) after ${elapsed}s."
                return 0
                ;;
        esac
        sleep 1
        elapsed=$((elapsed + 1))
    done
    echo "Frontend did not become ready within ${FRONTEND_READY_TIMEOUT}s (last / -> $code)."
    return 1
}

# The Platform Console is a Next.js route, so its readiness is the frontend's
# readiness. The route itself must answer, not just the port.
_wait_for_console_ready() {
    local elapsed=0
    local code="000"
    while [ "$elapsed" -lt "$FRONTEND_READY_TIMEOUT" ]; do
        code=$(_http_code "$PLATFORM_CONSOLE_URL")
        case "$code" in
            2*|3*)
                echo "Platform Console is ready (GET /platform -> $code) after ${elapsed}s."
                return 0
                ;;
        esac
        sleep 1
        elapsed=$((elapsed + 1))
    done
    echo "Platform Console did not become ready within ${FRONTEND_READY_TIMEOUT}s (last /platform -> $code)."
    return 1
}

# --- Component starters (B3: setsid + PID recording) ---

start_backend() {
    echo "Starting ClariFin OS Backend..."
    if [ ! -d ".venv" ]; then
        echo "Python venv not found. Run: bash scripts/bootstrap.sh"
        return 1
    fi
    _ensure_log_dir || return 1
    _ensure_component_log backend || return 1
    _rotate_log backend
    cd backend
    # Canonical invocation: -m uvicorn puts cwd on sys.path[0] so `src.api`
    # resolves without PYTHONPATH. The .venv python is authoritative here.
    # B3: setsid creates a new session/process group for deterministic teardown.
    # B5: redirect stdout+stderr to persistent log file.
    setsid "$REPO_ROOT/.venv/bin/python" -m uvicorn src.api:app \
        --host 0.0.0.0 --port "$BACKEND_PORT" --reload \
        >> "$LAUNCHER_LOGS_DIR/backend.log" 2>&1 &
    local pid=$!
    _write_pid backend "$pid"
    echo "  Backend started (PID=$pid, PGID=$pid)"
    echo "  Log: $LAUNCHER_LOGS_DIR/backend.log"
    return 0
}

start_frontend() {
    echo "Starting ClariFin OS Frontend (dev mode)..."
    cd frontend
    # B3: setsid for process-group ownership.
    # B5: redirect stdout/stderr to persistent log file.
    _ensure_log_dir || return 1
    _ensure_component_log frontend || return 1
    _rotate_log frontend
    setsid npm run dev >> "$LAUNCHER_LOGS_DIR/frontend.log" 2>&1 &
    local pid=$!
    _write_pid frontend "$pid"
    echo "  Frontend started (PID=$pid, PGID=$pid)"
    echo "  Log: $LAUNCHER_LOGS_DIR/frontend.log"
}

serve_frontend() {
    echo "Serving ClariFin OS Frontend (production build)..."
    if [ ! -d "$REPO_ROOT/frontend/dist" ]; then
        echo "Frontend not built. Run: cd frontend && npm run build"
        return 1
    fi
    cd "$REPO_ROOT"
    cd frontend
# B2 (confirmed): npm start = next start, serves frontend/dist on :3000.
    # The port is passed explicitly so CLARIFIN_FRONTEND_PORT is honoured and
    # the launcher owns the port it advertises rather than relying on a default
    # that may already be taken.
    # B3: setsid for process-group ownership.
    # B5: redirect stdout/stderr to persistent log file.
    _ensure_log_dir || return 1
    _ensure_component_log frontend || return 1
    _rotate_log frontend
    setsid npm start -- -p "$FRONTEND_PORT" >> "$LAUNCHER_LOGS_DIR/frontend.log" 2>&1 &
    local pid=$!
    _write_pid frontend "$pid"
    echo "  Frontend started (PID=$pid, PGID=$pid)"
    echo "  Log: $LAUNCHER_LOGS_DIR/frontend.log"
    return 0
}

run_verify() {
    echo "Running verification..."
    if [ ! -d ".venv" ]; then
        echo "Python venv not found. Run: bash scripts/bootstrap.sh"
        exit 1
    fi
    # Canonical module invocation from the repository root.
    "$REPO_ROOT/.venv/bin/python" -m runtime.verify check "$@"
}

check_platform() {
    echo "Opening Platform Console..."
    _require_console_running
    _open_browser "$PLATFORM_CONSOLE_URL"
}

# The console is served by the Next.js frontend on FRONTEND_PORT. The backend
# exposes only its JSON API at /platform/v1. Fail loudly rather than opening a
# URL that cannot answer.
_require_console_running() {
    local code
    code=$(_http_code "$PLATFORM_CONSOLE_URL")
    case "$code" in
        2*|3*)
            return 0
            ;;
    esac
    echo "ERROR: Platform Console is not reachable (HTTP $code) at $PLATFORM_CONSOLE_URL"
    echo ""
    echo "The console is a frontend route and needs the Next.js server running."
    echo "  Start the console on its own:  ./scripts/launch.sh console"
    echo "  Or start the whole application: ./start.sh"
    return 1
}

_open_browser() {
    local url="$1"
    if command -v xdg-open > /dev/null 2>&1; then
        xdg-open "$url" 2>/dev/null || echo "Open: $url"
    elif command -v open > /dev/null 2>&1; then
        open "$url" 2>/dev/null || echo "Open: $url"
    else
        echo "Open in browser: $url"
    fi
}

# Independent Platform Console entry point: starts ONLY the frontend, with no
# backend. This is a diagnostic surface — it must stay usable when the financial
# application cannot start. The console renders an explicit unavailable state
# when the platform API is unreachable, so a frontend-only run degrades
# predictably instead of hanging on a missing backend.
cmd_console() {
    echo "═══════════════════════════════════════════════════════════"
    echo "  ClariFin OS — Platform Console (independent)"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    # Frontend-only validation: no backend, so no .venv/uvicorn requirement.
    echo "───────────────────────────────────────────────────────────"
    echo "  Validating environment (console)"
    echo "───────────────────────────────────────────────────────────"
    local problems=0
    local node_problems=0
    _validate_node_env || node_problems=$?
    problems=$((problems + node_problems))
    echo ""
    if [ "$problems" -ne 0 ]; then
        echo "  ENVIRONMENT NOT READY — $problems problem(s) above."
        echo "  No services were started."
        return 1
    fi
    echo "  Environment OK (console requires no Python environment)."
    echo ""

    _ensure_state_dir

    # Port already serving means the console is up (or another app owns it).
    # _preflight_frontend_port returns 0 when the port is FREE, so the
    # "already served" branch is the inverted test.
    if ! _preflight_frontend_port; then
        local existing_owner
        existing_owner=$(ss -tlnp 2>/dev/null | grep -E ":${FRONTEND_PORT} " || true)
        echo ""
        echo "Frontend port $FRONTEND_PORT is already served:"
        echo "  $existing_owner"
        if _port_listener_is_ours frontend "$(echo "$existing_owner" | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)"; then
            echo ""
            echo "Platform Console may already be running:"
            echo "  $PLATFORM_CONSOLE_URL"
            echo ""
            _open_browser "$PLATFORM_CONSOLE_URL"
            return 0
        fi
        echo ""
        echo "This port is held by a process that is not a ClariFin frontend."
        echo "Stop it, or start the console on another port:"
        echo "  CLARIFIN_FRONTEND_PORT=3010 ./scripts/launch.sh console"
        return 1
    fi

    _ensure_log_dir || return 1
    _ensure_component_log console || return 1
    _rotate_log console

    echo "Starting frontend (console mode, Next.js dev server)..."
    cd "$REPO_ROOT/frontend"
    setsid npm run dev -- -p "$FRONTEND_PORT" >> "$LAUNCHER_LOGS_DIR/console.log" 2>&1 &
    local pid=$!
    _write_pid console "$pid"
    echo "  Console frontend started (PID=$pid, PGID=$pid)"
    echo "  Log: $LAUNCHER_LOGS_DIR/console.log"
    echo ""

    _wait_for_console_ready || {
        echo "ERROR: Platform Console did not become ready within ${FRONTEND_READY_TIMEOUT}s."
        tail -20 "$LAUNCHER_LOGS_DIR/console.log" 2>/dev/null || echo "  (no log captured)"
        _terminate_component console
        return 1
    }

    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  Platform Console is running (frontend only)."
    echo ""
    echo "  Console:    $PLATFORM_CONSOLE_URL"
    echo "  Platform API: $PLATFORM_API_URL  (requires the backend)"
    echo ""
    echo "  The console runs without the financial backend. Panels that need"
    echo "  live data report an explicit unavailable state until the backend"
    echo "  is started with ./start.sh."
    echo ""
    echo "  Stop with:  ./scripts/launch.sh stop"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    _open_browser "$PLATFORM_CONSOLE_URL"

    # Stay in the foreground so Ctrl+C tears the console down cleanly.
    trap '_terminate_component console; exit 0' INT TERM
    wait "$pid"
}

COMMAND="${1:-help}"

case "$COMMAND" in
    start)
        echo "═══════════════════════════════════════════════════════════"
        echo "  ClariFin OS — Starting (backend dev + frontend serve)"
        echo "═══════════════════════════════════════════════════════════"
        echo ""

        # Environment first: never spawn a service we cannot satisfy, so a bad
        # environment can never leave an orphaned backend behind.
        validate_environment full || exit 1
        echo ""

        _ensure_state_dir

        # B3: Port preflight
        echo "Preflight checks..."
        if ! _preflight_ports; then
            echo ""
            echo "Aborting start: port conflict(s) detected. Resolve before retrying."
            exit 1
        fi
        echo "  Ports $BACKEND_PORT and $FRONTEND_PORT available."
        echo ""

        # B3: Detect orphans
        _detect_orphans || true
        echo ""

        # B3: Clean stale state
        _clean_stale_state
        echo ""

        # Start backend
        start_backend || {
            echo "Backend failed to start."
            exit 1
        }
        BACKEND_PID=$(_read_pid backend)

        # Wait for backend readiness against the canonical /ready probe
        echo "Waiting for backend to be ready..."
        if ! _wait_for_backend_ready; then
            echo "Last captured log lines:"
            tail -20 "$LAUNCHER_LOGS_DIR/backend.log" 2>/dev/null || echo "  (no log captured)"
            echo "Backend failed to start. Cleaning up..."
            _terminate_component backend
            exit 1
        fi
        echo ""

        # Start frontend
        serve_frontend || {
            echo "Frontend failed to start. Cleaning up owned processes..."
            _terminate_component backend
            exit 1
        }
        FRONTEND_PID=$(_read_pid frontend)

        # Wait for frontend readiness
        echo "Waiting for frontend to be ready..."
        if ! _wait_for_frontend_ready; then
            echo "Last captured log lines:"
            tail -20 "$LAUNCHER_LOGS_DIR/frontend.log" 2>/dev/null || echo "  (no log captured)"
            echo "Frontend failed to start. Cleaning up owned processes..."
            _terminate_component frontend
            _terminate_component backend
            exit 1
        fi

        _print_running_banner
        echo "Press Ctrl+C to stop"
        echo ""

        # B3: Trap for graceful shutdown on Ctrl+C
        trap '_stop; exit 0' INT TERM

        wait "$BACKEND_PID" "$FRONTEND_PID"
        ;;
    stop)
        _stop
        ;;
    restart)
        cmd_restart
        ;;
    status)
        cmd_status
        ;;
    health)
        cmd_health
        ;;
    console)
        cmd_console
        ;;
    logs)
        cmd_logs "$@"
        ;;
    backend)
        start_backend
        wait
        ;;
    frontend)
        start_frontend
        wait
        ;;
    serve)
        serve_frontend
        wait
        ;;
    verify)
        shift
        if [ -z "${1:-}" ]; then
            run_verify
        else
            "$REPO_ROOT/.venv/bin/python" -m runtime.verify "$@"
        fi
        ;;
    platform)
        check_platform
        ;;
    check-env)
        validate_environment full
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
