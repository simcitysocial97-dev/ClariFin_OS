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
BACKEND_PORT=8000
FRONTEND_PORT=3000

# B3: Termination timeouts (seconds)
GRACEFUL_TIMEOUT=5
FORCE_TIMEOUT=2

show_help() {
    cat << 'EOF'
ClariFin OS Launcher

Usage:
    ./scripts/launch.sh <command>

Commands:
    start         One-click: backend (dev/reload) + frontend (production serve)
    stop          Deterministically terminate owned backend + frontend processes
    restart       Stop then start (deterministic lifecycle reset)
    status        Report actual process ownership/state for each component
    health        Check runtime health via process + HTTP probes
    logs          Show recently captured runtime output (backend/frontend)
                   Usage: ./scripts/launch.sh logs [backend|frontend]
    verify        Run the canonical verification suite
    platform      Open the Platform Console in browser
    help          Show this help message

Examples:
    ./scripts/launch.sh start
    ./scripts/launch.sh status
    ./scripts/launch.sh health
    ./scripts/launch.sh restart
    ./scripts/launch.sh logs backend
    ./scripts/launch.sh stop
    ./scripts/launch.sh verify quick

Verification Commands:
    verify check     Primary verification entrypoint
    verify doctor    Framework health check
    verify status    Current verification status
    verify env-check Canonical environment check
    verify backend   Backend verification profile
    verify frontend  Frontend verification profile
    verify quick     Quick quality gate
    verify mutation  Mutation testing (authoritative or --smoke)

EOF
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
        frontend)
            ps -g "$leader_pid" -o pid= 2>/dev/null | while read -r member; do
                [ -z "$member" ] && continue
                kill -0 "$member" 2>/dev/null || continue
                local args
                args=$(ps -o args= -p "$member" 2>/dev/null || echo "")
                if echo "$args" | grep -qE "next-server|next start"; then
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
            frontend)
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
            frontend)
                echo "$d_cmdline" | grep -qE "next-server|next start" && return 0
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
        local cleaned=false
        case "$component" in
            backend)
                local orphan_procs
                orphan_procs=$(pgrep -f "uvicorn.*src\.api:app.*--port.*${BACKEND_PORT}" 2>/dev/null | grep -v "^${pid}$" || true)
                if [ -n "$orphan_procs" ]; then
                    echo "  $component: cleaning orphan processes: $orphan_procs"
                    echo "$orphan_procs" | while read -r opid; do
                        kill -TERM "$opid" 2>/dev/null || true
                    done
                    sleep 1
                    echo "$orphan_procs" | while read -r opid; do
                        kill -0 "$opid" 2>/dev/null && kill -KILL "$opid" 2>/dev/null || true
                    done
                    cleaned=true
                fi
                ;;
            frontend)
                local orphan_procs
                orphan_procs=$(pgrep -f "next-server|next start" 2>/dev/null | grep -v "^${pid}$" || true)
                if [ -n "$orphan_procs" ]; then
                    echo "  $component: cleaning orphan processes: $orphan_procs"
                    echo "$orphan_procs" | while read -r opid; do
                        kill -TERM "$opid" 2>/dev/null || true
                    done
                    sleep 1
                    echo "$orphan_procs" | while read -r opid; do
                        kill -0 "$opid" 2>/dev/null && kill -KILL "$opid" 2>/dev/null || true
                    done
                    cleaned=true
                fi
                ;;
        esac

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

_detect_orphans() {
    local orphans=()

    # Backend orphans: uvicorn src.api:app on :8000 not represented by valid PID
    local recorded_backend
    recorded_backend=$(_read_pid backend)
    local backend_procs
    backend_procs=$(pgrep -af "uvicorn.*src\.api:app.*--port.*8000" 2>/dev/null | grep -v "pgrep" || true)
    if [ -n "$backend_procs" ]; then
        while IFS= read -r line; do
            local pid
            pid=$(echo "$line" | awk '{print $1}')
            if [ -n "$recorded_backend" ] && [ "$pid" = "$recorded_backend" ]; then
                continue
            fi
            orphans+=("backend: PID $pid — $line")
        done <<< "$backend_procs"
    fi

    # Frontend orphans: next-server / next start on :3000 not represented by valid PID
    local recorded_frontend
    recorded_frontend=$(_read_pid frontend)
    local frontend_procs
    frontend_procs=$(pgrep -af "next-server|next start" 2>/dev/null | grep -v "pgrep" || true)
    if [ -n "$frontend_procs" ]; then
        while IFS= read -r line; do
            local pid
            pid=$(echo "$line" | awk '{print $1}')
            if [ -n "$recorded_frontend" ] && [ "$pid" = "$recorded_frontend" ]; then
                continue
            fi
            orphans+=("frontend: PID $pid — $line")
        done <<< "$frontend_procs"
    fi

    if [ ${#orphans[@]} -gt 0 ]; then
        echo "Orphan ClariFin_OS processes detected:"
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
    for component in backend frontend; do
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

_stop() {
    echo "═══════════════════════════════════════════════════════════"
    echo "  ClariFin OS — Stopping"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    _ensure_state_dir

    local had_backend=false
    local had_frontend=false
    [ -n "$(_read_pid backend)" ] && had_backend=true
    [ -n "$(_read_pid frontend)" ] && had_frontend=true

    if [ "$had_backend" = false ] && [ "$had_frontend" = false ]; then
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
        # Kill any orphan uvicorn or next-server processes not covered by PID files
        local orphans_killed=false
        local bp_orphan
        bp_orphan=$(pgrep -f "uvicorn.*src\.api:app.*--port.*${BACKEND_PORT}" 2>/dev/null | grep -v "^${pid}$" || true)
        if [ -n "$bp_orphan" ]; then
            echo "  Killing backend orphans: $bp_orphan"
            echo "$bp_orphan" | while read -r op; do kill -TERM "$op" 2>/dev/null || true; done
            sleep 1
            echo "$bp_orphan" | while read -r op; do kill -0 "$op" 2>/dev/null && kill -KILL "$op" 2>/dev/null || true; done
            orphans_killed=true
        fi
        local fp_orphan
        fp_orphan=$(pgrep -f "next-server|next start" 2>/dev/null | grep -v "^${pid}$" || true)
        if [ -n "$fp_orphan" ]; then
            echo "  Killing frontend orphans: $fp_orphan"
            echo "$fp_orphan" | while read -r op; do kill -TERM "$op" 2>/dev/null || true; done
            sleep 1
            echo "$fp_orphan" | while read -r op; do kill -0 "$op" 2>/dev/null && kill -KILL "$op" 2>/dev/null || true; done
            orphans_killed=true
        fi
        [ "$orphans_killed" = true ] && sleep "$FORCE_TIMEOUT"

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
        bp_remaining=$(pgrep -f "uvicorn.*src\.api:app.*--port.*${BACKEND_PORT}" 2>/dev/null || true)
        if [ -n "$bp_remaining" ]; then
            echo "  Force-killing backend orphans: $bp_remaining"
            echo "$bp_remaining" | while read -r op; do kill -KILL "$op" 2>/dev/null || true; done
        fi
        local fp_remaining
        fp_remaining=$(pgrep -f "next-server|next start" 2>/dev/null || true)
        if [ -n "$fp_remaining" ]; then
            echo "  Force-killing frontend orphans: $fp_remaining"
            echo "$fp_remaining" | while read -r op; do kill -KILL "$op" 2>/dev/null || true; done
        fi
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
    local backend_ready=false
    for i in {1..30}; do
        if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
            echo "Backend is ready!"
            backend_ready=true
            break
        fi
        sleep 1
    done

    if [ "$backend_ready" = false ]; then
        echo "ERROR: Backend not reachable after 30s. Last captured log lines:"
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
    local frontend_ready=false
    for i in {1..30}; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ | grep -qE '^[23]'; then
            echo "Frontend is ready!"
            frontend_ready=true
            break
        fi
        sleep 1
    done

    if [ "$frontend_ready" = false ]; then
        echo "ERROR: Frontend not reachable after 30s. Last captured log lines:"
        tail -20 "$LAUNCHER_LOGS_DIR/frontend.log" 2>/dev/null || echo "  (no log captured)"
        echo "Frontend failed to start. Cleaning up owned processes..."
        _terminate_component frontend
        _terminate_component backend
        return 1
    fi

    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo -e "  ClariFin OS restarted successfully!"
    echo ""
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
    echo "═══════════════════════════════════════════════════════════"

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
    code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
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
    code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ready 2>/dev/null || echo "000")
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
    code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ 2>/dev/null || echo "000")
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
    bp_result=$(_health_check_backend_process)
    echo "  Process        $bp_result"
    if echo "$bp_result" | grep -q "^FAIL"; then overall_pass=false; fi

    # Backend /health
    local bh_result
    bh_result=$(_health_check_backend_http)
    echo "  /health        $bh_result"
    if echo "$bh_result" | grep -q "^FAIL"; then overall_pass=false; fi

    # Backend /ready
    local br_result
    br_result=$(_health_check_backend_ready)
    echo "  /ready         $br_result"
    if echo "$br_result" | grep -q "^FAIL"; then overall_pass=false; fi

    echo ""

    # Frontend process
    echo "Frontend:"
    local fp_result
    fp_result=$(_health_check_frontend_process)
    echo "  Process        $fp_result"
    if echo "$fp_result" | grep -q "^FAIL"; then overall_pass=false; fi

    # Frontend HTTP
    local fh_result
    fh_result=$(_health_check_frontend_http)
    echo "  HTTP (:3000)   $fh_result"
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
        --host 0.0.0.0 --port 8000 --reload \
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
    # B3: setsid for process-group ownership.
    # B5: redirect stdout+stderr to persistent log file.
    _ensure_log_dir || return 1
    _ensure_component_log frontend || return 1
    _rotate_log frontend
    setsid npm start >> "$LAUNCHER_LOGS_DIR/frontend.log" 2>&1 &
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

check_health() {
    echo "Checking platform health..."
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "Backend not running. Start with: ./scripts/launch.sh backend"
        exit 1
    fi
    echo ""
    echo "Application Health:"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
    echo ""
    echo "Platform Health:"
    curl -s http://localhost:8000/platform/v1/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/platform/v1/health
}

check_platform() {
    echo "Opening Platform Console..."
    if command -v xdg-open > /dev/null 2>&1; then
        xdg-open http://localhost:8000/platform 2>/dev/null || echo "Open: http://localhost:8000/platform"
    elif command -v open > /dev/null 2>&1; then
        open http://localhost:8000/platform 2>/dev/null || echo "Open: http://localhost:8000/platform"
    else
        echo "Open in browser: http://localhost:8000/platform"
    fi
}

COMMAND="${1:-help}"

case "$COMMAND" in
    start)
        echo "═══════════════════════════════════════════════════════════"
        echo "  ClariFin OS — Starting (backend dev + frontend serve)"
        echo "═══════════════════════════════════════════════════════════"
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

        # Wait for backend readiness
        echo "Waiting for backend to be ready..."
        backend_ready=false
        for i in {1..30}; do
            if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
                echo "Backend is ready!"
                backend_ready=true
                break
            fi
            sleep 1
        done

        if [ "$backend_ready" = false ]; then
            echo "ERROR: Backend not reachable after 30s. Last captured log lines:"
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
        frontend_ready=false
        for i in {1..30}; do
            if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ | grep -qE '^[23]'; then
                echo "Frontend is ready!"
                frontend_ready=true
                break
            fi
            sleep 1
        done

        if [ "$frontend_ready" = false ]; then
            echo "ERROR: Frontend not reachable after 30s. Last captured log lines:"
            tail -20 "$LAUNCHER_LOGS_DIR/frontend.log" 2>/dev/null || echo "  (no log captured)"
            echo "Frontend failed to start. Cleaning up owned processes..."
            _terminate_component frontend
            _terminate_component backend
            exit 1
        fi

        echo ""
        echo "═══════════════════════════════════════════════════════════"
        echo -e "  ClariFin OS is running!"
        echo ""
        echo "  Frontend:  http://localhost:3000"
        echo "  Backend:   http://localhost:8000"
        echo "  API Docs:  http://localhost:8000/docs"
        echo ""
        echo "Press Ctrl+C to stop"
        echo "═══════════════════════════════════════════════════════════"
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
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
