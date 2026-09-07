#!/bin/bash
# ClariFin OS Launcher (Cross-platform)
# Simple operational entry points for ClariFin OS

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
    backend       Start the FastAPI backend server (http://localhost:8000)
    frontend      Start the Next.js frontend in dev mode (http://localhost:3000)
    serve         Serve the built frontend (http://localhost:3000)
    verify        Run the canonical verification suite
    health        Check platform health via API
    platform      Open the Platform Console in browser
    help          Show this help message

Examples:
    ./scripts/launch.sh backend
    ./scripts/launch.sh frontend
    ./scripts/launch.sh verify
    ./scripts/launch.sh health

Verification Commands:
    verify check     Primary verification entrypoint
    verify doctor    Framework health check
    verify status    Current verification status
    verify env-check Canonical environment check
    verify backend   Backend verification profile
    verify frontend  Frontend verification profile
    verify quick     Quick quality gate

EOF
}

start_backend() {
    echo "Starting ClariFin OS Backend..."
    if [ ! -d ".venv" ]; then
        echo "Python venv not found. Run: bash scripts/bootstrap.sh"
        exit 1
    fi
    source .venv/bin/activate
    cd backend
    PYTHONPATH=. ../.venv/bin/uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
}

start_frontend() {
    echo "Starting ClariFin OS Frontend (dev mode)..."
    cd frontend
    npm run dev
}

serve_frontend() {
    echo "Serving ClariFin OS Frontend (production build)..."
    if [ ! -d "frontend/out" ]; then
        echo "Frontend not built. Run: npm run build in frontend directory"
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
    source .venv/bin/activate
    .venv/bin/python runtime/verify.py check
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
        if [ -z "$1" ]; then
            run_verify
        else
            source .venv/bin/activate
            .venv/bin/python runtime/verify.py "$@"
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
