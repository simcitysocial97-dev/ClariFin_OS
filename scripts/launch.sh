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

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

show_help() {
    cat << 'EOF'
ClariFin OS Launcher

Usage:
    ./scripts/launch.sh <command>

Commands:
    start         One-click: backend (dev/reload) + frontend (production serve)
    backend       Start the FastAPI backend server (http://localhost:8000)
    frontend      Start the Next.js frontend in dev mode (http://localhost:3000)
    serve         Serve the built frontend (http://localhost:3000)
    verify        Run the canonical verification suite
    health        Check platform health via API
    platform      Open the Platform Console in browser
    help          Show this help message

Examples:
    ./scripts/launch.sh start
    ./scripts/launch.sh backend
    ./scripts/launch.sh frontend
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

start_backend() {
    echo "Starting ClariFin OS Backend..."
    if [ ! -d ".venv" ]; then
        echo "Python venv not found. Run: bash scripts/bootstrap.sh"
        exit 1
    fi
    cd backend
    # Canonical invocation: -m uvicorn puts cwd on sys.path[0] so `src.api`
    # resolves without PYTHONPATH. The .venv python is authoritative here.
    "$REPO_ROOT/.venv/bin/python" -m uvicorn src.api:app \
        --host 0.0.0.0 --port 8000 --reload
}

start_frontend() {
    echo "Starting ClariFin OS Frontend (dev mode)..."
    cd frontend
    npm run dev
}

serve_frontend() {
    echo "Serving ClariFin OS Frontend (production build)..."
    if [ ! -d "frontend/out" ]; then
        echo "Frontend not built. Run: cd frontend && npm run build"
        exit 1
    fi
    npx serve@latest frontend/out -p 3000 -s
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
        # Start backend in background (hot reload).
        start_backend &
        BACKEND_PID=$!
        # Wait for backend readiness at :8000.
        echo "Waiting for backend to be ready..."
        for i in {1..30}; do
            if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
                echo "Backend is ready!"
                break
            fi
            sleep 1
            if [ "$i" -eq 30 ]; then
                echo "Warning: Backend may not be ready yet"
            fi
        done
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
        # Serve frontend (foreground); wait for backend in background.
        ( serve_frontend ) &
        FRONTEND_PID=$!
        wait "$BACKEND_PID" "$FRONTEND_PID"
        ;;
    backend)
        start_backend
        ;;
    frontend)
        start_frontend
        ;;
    serve)
        serve_frontend
        ;;
    verify)
        shift
        if [ -z "${1:-}" ]; then
            run_verify
        else
            "$REPO_ROOT/.venv/bin/python" -m runtime.verify "$@"
        fi
        ;;
    health)
        check_health
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
