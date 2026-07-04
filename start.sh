#!/bin/bash

# ClariFin OS - Development Start Script
# Starts backend and frontend dev servers concurrently
# ==========================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# PID files for process management
BACKEND_PID_FILE="/tmp/clarifin-backend.pid"
FRONTEND_PID_FILE="/tmp/clarifin-frontend.pid"

# Store PIDs
BACKEND_PID=""
FRONTEND_PID=""

# Clear screen for clean output
clear 2>/dev/null || true

echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  ClariFin OS - Development Server${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}⚡ Shutting down ClariFin OS...${NC}"
    
    # Kill backend if running
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "${BLUE}  → Stopping backend (PID: $BACKEND_PID)${NC}"
        kill "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
    fi
    
    # Kill frontend if running
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo -e "${BLUE}  → Stopping frontend (PID: $FRONTEND_PID)${NC}"
        kill "$FRONTEND_PID" 2>/dev/null || true
        wait "$FRONTEND_PID" 2>/dev/null || true
    fi
    
    # Remove PID files
    rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"
    
    echo -e "${GREEN}✅ Services stopped. Goodbye!${NC}"
    exit 0
}

# Set trap to cleanup on exit signals
trap cleanup INT TERM EXIT

# Check if backend venv exists
echo -e "${BLUE}▶ Checking prerequisites...${NC}"
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}⚠ Warning: backend/venv not found${NC}"
    echo -e "   Run: ${BOLD}cd backend && make venv${NC}"
    echo ""
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠ Warning: frontend/node_modules not found${NC}"
    echo -e "   Run: ${BOLD}cd frontend && npm ci${NC}"
    echo ""
fi

# Start Backend
echo -e "${BLUE}▶ Starting Backend Server...${NC}"
cd backend

# Check if we can use make run or fall back to uvicorn directly
if [ -f "Makefile" ] && grep -q "^run:" Makefile 2>/dev/null; then
    # Use make run but capture the PID
    make run &
    BACKEND_PID=$!
else
    # Fallback to direct uvicorn
    if [ -f "venv/bin/python" ]; then
        ./venv/bin/python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000 &
    else
        python3 -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000 &
    fi
    BACKEND_PID=$!
fi

echo $BACKEND_PID > "$BACKEND_PID_FILE"
cd ..

echo -e "${GREEN}  ✓ Backend starting on port 8000 (PID: $BACKEND_PID)${NC}"

# Wait a moment for backend to initialize
sleep 2

# Start Frontend
echo -e "${BLUE}▶ Starting Frontend Server...${NC}"
cd frontend

# Start Next.js dev server
if [ -f "../backend/venv/bin/npm" ]; then
    # Use npm from PATH
    npm run dev &
else
    npm run dev &
fi
FRONTEND_PID=$!

echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
cd ..

echo -e "${GREEN}  ✓ Frontend starting on port 3000 (PID: $FRONTEND_PID)${NC}"
echo ""

# Wait for services to be ready
echo -e "${BLUE}▶ Waiting for services to be ready...${NC}"
sleep 3

# Print access URLs
echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ ClariFin OS is running!${NC}"
echo ""
echo -e "  ${BOLD}Frontend:${NC} ${BLUE}http://localhost:3000${NC}"
echo -e "  ${BOLD}Backend:${NC}  ${BLUE}http://localhost:8000${NC}"
echo -e "  ${BOLD}Docs:${NC}     ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo -e "  ${YELLOW}Press Ctrl+C to stop${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Stream logs from both processes
# Use tail -f on /dev/null to keep script running while waiting for processes
wait
