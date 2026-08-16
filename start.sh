#!/bin/bash

# ClariFin OS - Personal Finance MVP v1.0.0
# One-Click Launch Script for Unix/Linux/Mac
# ==========================================

set -e

echo "═══════════════════════════════════════════════════════════"
echo "  ClariFin OS - Personal Finance MVP v1.0.0"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo "Please install Node.js 18 or higher"
    exit 1
fi

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down ClariFin OS...${NC}"
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}Goodbye!${NC}"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup INT TERM EXIT

echo -e "${YELLOW}Starting Backend Server...${NC}"
cd backend

# M10: single repository Python environment at ../.venv (no per-backend venv).
VENV_DIR="../.venv"
if [ ! -d "$VENV_DIR/bin" ]; then
    echo "Creating repository Python virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate repository virtual environment
source "$VENV_DIR/bin/activate"

# Install dependencies if needed
if [ ! -f "$VENV_DIR/.installed-editable" ] || [ ../pyproject.toml -nt "$VENV_DIR/.installed-editable" ]; then
    echo "Installing Python dependencies from root pyproject.toml (single authority)..."
    pip install -q -e ".[all]"
    touch "$VENV_DIR/.installed-editable"
fi

# Start backend in background
echo -e "${GREEN}Backend starting on http://localhost:8000${NC}"
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo -e "${GREEN}Backend is ready!${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}Warning: Backend may not be ready yet${NC}"
    fi
done

echo ""
echo -e "${YELLOW}Starting Frontend...${NC}"
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ] || [ package.json -nt "node_modules/.package-lock.json" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Build frontend for production
echo "Building frontend..."
npm run build

# Start frontend in background
echo -e "${GREEN}Frontend starting on http://localhost:3000${NC}"
npx serve@latest out -p 3000 -s &
FRONTEND_PID=$!
cd ..

echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "${GREEN}ClariFin OS is running!${NC}"
echo ""
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo "═══════════════════════════════════════════════════════════"

# Wait for processes
wait
