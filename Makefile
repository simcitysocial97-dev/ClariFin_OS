# ClariFin OS - Root Makefile
# Provides convenient shortcuts for common development tasks

.PHONY: help start stop run setup-frontend build-frontend typecheck

# Default target
help:
	@echo "ClariFin OS - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make start          - Start backend and frontend dev servers"
	@echo "  make stop           - Stop running dev servers"
	@echo "  make run            - Alias for 'make start'"
	@echo ""
	@echo "Frontend:"
	@echo "  make setup-frontend - Install frontend dependencies"
	@echo "  make build-frontend - Build frontend for production"
	@echo "  make typecheck      - Run TypeScript type checking"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - Python 3.10+ with backend/venv"
	@echo "  - Node.js 20+ with frontend/node_modules"

# Start both backend and frontend dev servers
start:
	./start.sh

# Stop running dev servers (uses PID files)
stop:
	@echo "Stopping ClariFin OS services..."
	@if [ -f /tmp/clarifin-backend.pid ]; then \
		kill $$(cat /tmp/clarifin-backend.pid) 2>/dev/null || true; \
		rm -f /tmp/clarifin-backend.pid; \
		echo "  ✓ Backend stopped"; \
	fi
	@if [ -f /tmp/clarifin-frontend.pid ]; then \
		kill $$(cat /tmp/clarifin-frontend.pid) 2>/dev/null || true; \
		rm -f /tmp/clarifin-frontend.pid; \
		echo "  ✓ Frontend stopped"; \
	fi
	@echo "✅ All services stopped"

# Alias for start
run: start

# Frontend targets
setup-frontend:
	cd frontend && npm ci

build-frontend:
	cd frontend && npm run build

typecheck:
	cd frontend && npm run typecheck 2>/dev/null || npx tsc --noEmit
	@echo "✅ Typecheck complete"
