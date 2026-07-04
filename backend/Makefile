# ClariFin Backend Makefile
# Provides convenient shortcuts for common development tasks

PYTHON := ./venv/bin/python
PIP := ./venv/bin/pip

.PHONY: venv validate run test clean help lock docker-build docker-test docker-run docker-compose-up docker-compose-down doctor

# Default target
help:
	@echo "ClariFin Backend - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make venv      - Create virtual environment and install dependencies"
	@echo "  make validate  - Run pipeline validation checks"
	@echo "  make run       - Start the FastAPI development server"
	@echo "  make test      - Run pytest test suite"
	@echo "  make clean     - Remove virtual environment"
	@echo ""
	@echo "Dependency Management:"
	@echo "  make lock      - Regenerate requirements.txt from requirements.in"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build      - Build Docker image"
	@echo "  make docker-run        - Run Docker container"
	@echo "  make docker-test       - Run tests inside Docker container"
	@echo "  make docker-compose-up - Start with docker-compose"
	@echo "  make docker-compose-down - Stop docker-compose"
	@echo ""
	@echo "Environment:"
	@echo "  make doctor    - Check environment health"
	@echo ""
	@echo "Prerequisites: Python 3.10+, ghostscript, opencv, Docker (optional)"

# Create virtual environment and install dependencies
venv:
	python3 -m venv venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo ""
	@echo "✅ Virtual environment created successfully!"
	@echo "   Run 'make validate' to check the installation"

# Run pipeline validation
validate:
	$(PYTHON) -m src.validate_pipeline

# Start development server
run:
	$(PYTHON) -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	$(PYTHON) -m pytest tests/ -v

# Clean up virtual environment
clean:
	rm -rf venv/
	@echo "✅ Virtual environment removed"

# Regenerate locked requirements.txt from requirements.in
lock:
	$(PIP) install pip-tools
	$(PYTHON) -m piptools compile --output-file=requirements.txt requirements.in
	@echo "✅ requirements.txt regenerated from requirements.in"

# Docker commands
docker-build:
	docker build -t clarifin-backend:latest .

docker-run:
	docker run -p 8000:8000 -v $(PWD)/data:/app/data --env-file .env clarifin-backend:latest

docker-test:
	docker run --rm -v $(PWD)/data:/app/data --env-file .env clarifin-backend:latest python -m pytest tests/ -v

docker-compose-up:
	cp -n .env.example .env 2>/dev/null || true
	docker-compose up --build -d

docker-compose-down:
	docker-compose down

# Environment validation
doctor:
	$(PYTHON) scripts/doctor.py

# ──────────────────────────────────────────────
# Database Maintenance
# ──────────────────────────────────────────────

db-status:
	$(PYTHON) -m src.maintenance status

db-vacuum:
	$(PYTHON) -m src.maintenance vacuum

db-backup:
	$(PYTHON) -m src.maintenance backup

db-export:
	$(PYTHON) -m src.maintenance export-json

db-check:
	$(PYTHON) -m src.maintenance check-orphans

db-full-maintenance: db-backup db-vacuum db-check db-status
	@echo "✅ Full maintenance complete"
