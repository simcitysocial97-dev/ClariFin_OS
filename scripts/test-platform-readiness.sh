#!/usr/bin/env bash
# =============================================================================
# scripts/test-platform-readiness.sh — M11 regression
# =============================================================================
#
# WHAT THIS PINS
# --------------
# `scripts/launch.sh platform-status` and the `Platform API` block in
# `scripts/launch.sh health` must classify the console's data path into four
# states, and must not collapse them. The launcher is an operator's first
# instrument: if it says "BACKEND UNAVAILABLE" about a backend that is 40 s into
# importing its module graph, it invites a restart that throws away the warm-up.
#
# The classifier is `curl`'s own exit code, which is why this needs real
# servers rather than a mocked function:
#
#     exit  7  -> connection refused  -> BACKEND UNAVAILABLE
#     exit 28  -> operation timed out -> PLATFORM STARTING
#     HTTP 200  ->                     -> PLATFORM READY
#     HTTP 5xx  ->                     -> PLATFORM ENDPOINT FAILED
#
# The three server modes are tiny local TCP servers written to $TMPDIR, so the
# test has no dependency on the backend, on a built frontend, or on any port
# being free in advance (it picks a free one itself).
#
# Usage:
#   bash scripts/test-platform-readiness.sh
#
# Exit 0 only if every case passes.
# =============================================================================
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAUNCHER="$ROOT_DIR/scripts/launch.sh"
PY="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$PY" ]; then
    echo "ERROR: canonical interpreter missing at $PY" >&2
    echo "       Run: bash scripts/bootstrap.sh" >&2
    exit 1
fi

TMPDIR_TEST="$(mktemp -d)"
PID_FILE="$TMPDIR_TEST/pids"
: >"$PID_FILE"
FAILURES=0

# The launcher's own transient state directory. Section 8 writes a pid record
# here so `stop` takes the "there are owned components" path and therefore
# actually reaches the orphan sweep; without a record `stop` returns early with
# "No owned processes recorded" and the ownership check would never run. The
# directory is gitignored and the record is removed by the cleanup trap.
LAUNCHER_STATE_DIR="$ROOT_DIR/runtime/generated/launcher/state"

# Track a pid for teardown.
#
# Deliberately a FILE and not a shell array: `start_server` is invoked inside
# `$( ... )` for its port number, so an array updated in the callee would live in
# the command-substitution subshell and be discarded. An array-based version of
# this test leaked every fixture server (verified: 9 orphans after one run).
track_pid() {
    printf '%s\n' "$1" >>"$PID_FILE"
}

cleanup() {
    local pid
    if [ -f "$PID_FILE" ]; then
        while read -r pid; do
            [ -n "$pid" ] || continue
            kill -9 "$pid" 2>/dev/null || true
        done <"$PID_FILE"
    fi
    # Never leave a fabricated pid record behind: a later real `stop` must not
    # try to terminate a pid this test invented.
    rm -f "$LAUNCHER_STATE_DIR/console.pid" 2>/dev/null || true
    rm -rf "$TMPDIR_TEST"
}
trap cleanup EXIT

# A TCP server that behaves in exactly one of the three ways the classifier
# distinguishes. Uses the canonical interpreter so the test cannot be run under
# an unmanaged Python.
#
# The body is passed via `-c` with a `uvicorn src.api:app ...` argv tail. That is
# not cosmetic: the launcher's ownership predicate greps a listener's command
# line for `uvicorn.*src\.api:app`, so a fixture that does not look like a
# ClariFin backend would silently skip the branch under test and the case would
# pass for the wrong reason. This reproduces the real orphan's `ps -o args=`
# shape exactly.
SERVER_BODY='
import socket, sys, threading, time

# `python -c CODE uvicorn src.api:app <mode> <port>` puts "-c" at argv[0], so the
# literal argv tail occupies indices 1..4.
mode, port = sys.argv[3], int(sys.argv[4])
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", port))
srv.listen(64)


def handle(conn):
    if mode == "silent":
        conn.recv(65535)
        while True:
            time.sleep(3600)
    try:
        conn.recv(65535)
        body = b"{\"kind\":\"platform.health_snapshot\",\"data\":{}}"
        reason = b"OK" if mode == "ready" else b"Internal Server Error"
        conn.sendall(
            b"HTTP/1.1 " + (b"200 " if mode == "ready" else b"500 ") + reason
            + b"\r\nContent-Type: application/json\r\nContent-Length: "
            + str(len(body)).encode()
            + b"\r\nConnection: close\r\n\r\n" + body
        )
    except Exception:
        pass


while True:
    try:
        c, _ = srv.accept()
    except OSError:
        break
    threading.Thread(target=handle, args=(c,), daemon=True).start()
'

# Find a free TCP port without racing another process for it.
free_port() {
    "$PY" - <<'PYEOF'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PYEOF
}

# Every PID listening on a TCP port. Used to prove `stop` did NOT kill an
# unowned listener, which is a property of the *absence* of a kill and so cannot
# be asserted from the launcher's own output alone.
server_pids_on() {
    ss -tlnp 2>/dev/null | grep -E ":$1 " | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u
}

start_server() {
    local mode="$1" port pid
    port="$(free_port)"
    # `uvicorn src.api:app` in argv => the fixture matches the launcher's
    # component signature (see SERVER_BODY).
    "$PY" -c "$SERVER_BODY" uvicorn "src.api:app" "$mode" "$port" >/dev/null 2>&1 &
    pid=$!
    track_pid "$pid"
    # Wait for the listener to actually accept, so the test never races itself.
    local _
    for _ in $(seq 1 50); do
        if "$PY" -c "
import socket,sys
s=socket.socket()
s.settimeout(0.2)
sys.exit(0 if s.connect_ex(('127.0.0.1',$port))==0 else 1)
" 2>/dev/null; then
            echo "$port"
            return 0
        fi
        sleep 0.1
    done
    echo "ERROR: test server ($mode) did not start on $port" >&2
    return 1
}

# Claim a component as launcher-owned by recording a live, test-owned process in
# the launcher's own state directory. Prints the pid.
claim_owned_component() {
    local component="$1" pid
    setsid sleep 300 >/dev/null 2>&1 &
    pid=$!
    track_pid "$pid"
    mkdir -p "$LAUNCHER_STATE_DIR"
    printf '%s' "$pid" >"$LAUNCHER_STATE_DIR/${component}.pid"
    printf '%s' "$pid"
}

# expect_case <name> <port> <probe-timeout> <expected-state> <expected-exit>
expect_case() {
    local name="$1" port="$2" probe_timeout="$3" want_state="$4" want_exit="$5"
    local out rc got_state
    out="$(
        CLARIFIN_BACKEND_PORT="$port" \
        CLARIFIN_FRONTEND_PORT=0 \
        bash "$LAUNCHER" platform-status "$probe_timeout" 2>&1
    )"
    rc=$?
    got_state="$(printf '%s\n' "$out" | sed -n 's/^  State *//p' | head -1)"

    if [ "$got_state" = "$want_state" ] && [ "$rc" = "$want_exit" ]; then
        printf '  PASS  %-22s state=%-24s exit=%s\n' "$name" "$got_state" "$rc"
        return 0
    fi
    printf '  FAIL  %-22s state=%-24s (want %-24s) exit=%s (want %s)\n' \
        "$name" "${got_state:-<none>}" "$want_state" "$rc" "$want_exit"
    printf '%s\n' "$out" | sed 's/^/        | /'
    FAILURES=$((FAILURES + 1))
    return 1
}

echo "=== M11 — launcher platform readiness classification ==="
echo "launcher: $LAUNCHER"
echo ""

# 1. Nothing listening at all.
DEAD_PORT="$(free_port)"
expect_case "no-listener" "$DEAD_PORT" 3 "BACKEND UNAVAILABLE" 1

# 2. Connection accepted, no response inside the bound => STARTING, not a failure.
#    This is the case the whole milestone exists for: the previous launcher could
#    not express it and reported the same thing as a dead port.
PORT="$(start_server silent)" || exit 1
expect_case "accepted-silent" "$PORT" 3 "PLATFORM STARTING" 1

# 3. The application answers with an error => the process is fine, the endpoint
#    is not. Must NOT be reported as a cold start.
PORT="$(start_server error)" || exit 1
expect_case "http-500" "$PORT" 5 "PLATFORM ENDPOINT FAILED" 1

# 4. The application answers 200.
PORT="$(start_server ready)" || exit 1
expect_case "http-200" "$PORT" 5 "PLATFORM READY" 0

# 5. `health` must report the platform section without folding a cold platform
#    read into the overall verdict: a starting platform is not an unhealthy
#    financial application.
PORT="$(start_server silent)" || exit 1
HEALTH_OUT="$(
    CLARIFIN_BACKEND_PORT="$PORT" CLARIFIN_FRONTEND_PORT=0 \
    bash "$LAUNCHER" health 2>&1
)"
if printf '%s\n' "$HEALTH_OUT" | grep -q "STARTING (no response within"; then
    printf '  PASS  %-22s %s\n' "health-platform" "reports STARTING"
else
    printf '  FAIL  %-22s health did not report platform STARTING\n' "health-platform"
    printf '%s\n' "$HEALTH_OUT" | sed 's/^/        | /'
    FAILURES=$((FAILURES + 1))
fi
if printf '%s\n' "$HEALTH_OUT" | grep -q "platform-status"; then
    printf '  PASS  %-22s %s\n' "health-pointer" "points at platform-status"
else
    printf '  FAIL  %-22s health does not point at platform-status\n' "health-pointer"
    FAILURES=$((FAILURES + 1))
fi

# 6. The banner must be non-gating: a cold platform read must not be presented
#    as something the operator must wait through before using the console.
if grep -q 'PLATFORM_PROBE_TIMEOUT="${CLARIFIN_PLATFORM_PROBE_TIMEOUT:-25}"' "$LAUNCHER"; then
    printf '  PASS  %-22s %s\n' "probe-bounded" "default 25 s bound"
else
    printf '  FAIL  %-22s platform probe is not bounded\n' "probe-bounded"
    FAILURES=$((FAILURES + 1))
fi

# 7. `health` itself must terminate against a backend that accepts connections
#    and never answers. `curl` has no default timeout, so an unbounded probe here
#    makes `./start.sh health` hang forever in exactly the cold-start window the
#    console is meant to survive. This case is a hang, not an assertion on text.
PORT="$(start_server silent)" || exit 1
HEALTH_STARTED_AT=$(date +%s)
timeout 90 bash -c "CLARIFIN_BACKEND_PORT='$PORT' CLARIFIN_FRONTEND_PORT=0 \
    bash '$LAUNCHER' health >/dev/null 2>&1"
HEALTH_RC=$?
HEALTH_TOOK=$(( $(date +%s) - HEALTH_STARTED_AT ))
if [ "$HEALTH_RC" = "124" ]; then
    printf '  FAIL  %-22s health HUNG against an accepted-but-silent backend (killed at 90 s)\n' "health-bounded"
    FAILURES=$((FAILURES + 1))
elif [ "$HEALTH_TOOK" -gt 60 ]; then
    printf '  FAIL  %-22s health took %ss against a silent backend (bound is 5 s/probe)\n' "health-bounded" "$HEALTH_TOOK"
    FAILURES=$((FAILURES + 1))
else
    printf '  PASS  %-22s terminated in %ss\n' "health-bounded" "$HEALTH_TOOK"
fi

# 8. SHUTDOWN SAFETY: `stop` must not kill a process it did not start.
#
#    Defect reproduced on this host before the fix: a 5h45m-old
#    `uvicorn src.api:app --port 8000` from a previous session, re-parented to
#    init, with no pid record, was destroyed by `./scripts/launch.sh stop`
#    ("Killing backend orphan on port 8000: 1704145") purely because its command
#    line matched. A command-line signature is not ownership.
#
#    Reproduced here deterministically: a listener with a ClariFin-shaped command
#    line on the backend port, no pid record. `stop` must report it and leave it
#    running. The server mode is `ready` so it survives long enough to be probed.
PORT="$(start_server ready)" || exit 1
UNOWNED_PIDS="$(server_pids_on "$PORT")"
if [ -z "$UNOWNED_PIDS" ]; then
    printf '  FAIL  %-22s could not identify the unowned listener pid\n' "stop-ownership"
    FAILURES=$((FAILURES + 1))
else
    # Record an owned component so `stop` reaches the sweep instead of returning
    # early with "No owned processes recorded".
    claim_owned_component console >/dev/null
    STOP_OUT="$(
        CLARIFIN_BACKEND_PORT="$PORT" CLARIFIN_FRONTEND_PORT=0 \
        bash "$LAUNCHER" stop 2>&1
    )"
    if printf '%s\n' "$STOP_OUT" | grep -q "LEAVING UNOWNED backend-shaped listener"; then
        printf '  PASS  %-22s %s\n' "stop-ownership" "reports the unowned listener"
    else
        printf '  FAIL  %-22s stop did not report the unowned listener\n' "stop-ownership"
        printf '%s\n' "$STOP_OUT" | sed 's/^/        | /'
        FAILURES=$((FAILURES + 1))
    fi
    STILL_ALIVE=0
    for upid in $UNOWNED_PIDS; do
        kill -0 "$upid" 2>/dev/null && STILL_ALIVE=1
    done
    if [ "$STILL_ALIVE" = "1" ]; then
        printf '  PASS  %-22s %s\n' "stop-no-kill" "unowned listener survived stop"
    else
        printf '  FAIL  %-22s stop KILLED a process it did not spawn (pids: %s)\n' "stop-no-kill" "$UNOWNED_PIDS"
        FAILURES=$((FAILURES + 1))
    fi
fi

# 9. `status` must report the Platform API verdict and a console-only run, not
#    only "Overall: STOPPED". Reported here because both were added after
#    measurement showed `status` could not answer the question an operator has
#    during a cold start.
PORT="$(start_server silent)" || exit 1
STATUS_OUT="$(
    CLARIFIN_BACKEND_PORT="$PORT" CLARIFIN_FRONTEND_PORT=0 \
    timeout 120 bash "$LAUNCHER" status 2>&1
)"
if printf '%s\n' "$STATUS_OUT" | grep -q "Platform API (:"; then
    printf '  PASS  %-22s %s\n' "status-platform" "reports the platform verdict"
else
    printf '  FAIL  %-22s status omits the Platform API verdict\n' "status-platform"
    FAILURES=$((FAILURES + 1))
fi
if printf '%s\n' "$STATUS_OUT" | grep -qE "State: +STARTING"; then
    printf '  PASS  %-22s %s\n' "status-starting" "surfaces BACKEND STARTING"
else
    printf '  FAIL  %-22s status did not surface STARTING\n' "status-starting"
    printf '%s\n' "$STATUS_OUT" | sed 's/^/        | /'
    FAILURES=$((FAILURES + 1))
fi

echo ""
if [ "$FAILURES" -eq 0 ]; then
    echo "RESULT: PASS (all launcher platform-readiness cases)"
    exit 0
fi
echo "RESULT: FAIL ($FAILURES case(s))"
exit 1
