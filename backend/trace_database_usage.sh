#!/usr/bin/env bash

echo "========================================="
echo "Searching FinanceDB instantiations"
echo "========================================="

grep -RIn \
  --exclude-dir=venv \
  --exclude-dir=.git \
  --exclude-dir=__pycache__ \
  "FinanceDB(" .

echo
echo "========================================="
echo "Searching sqlite3 connections"
echo "========================================="

grep -RIn \
  --exclude-dir=venv \
  --exclude-dir=.git \
  --exclude-dir=__pycache__ \
  "sqlite3.connect" .

echo
echo "========================================="
echo "Searching database path references"
echo "========================================="

grep -RIn \
  --exclude-dir=venv \
  --exclude-dir=.git \
  --exclude-dir=__pycache__ \
  "finance.db\|FINANCE_DB_PATH\|database_path\|db_path" .

echo
echo "========================================="
echo "Searching FastAPI dependency providers"
echo "========================================="

grep -RIn \
  --exclude-dir=venv \
  --exclude-dir=.git \
  --exclude-dir=__pycache__ \
  "Depends\|dependency_overrides\|get_db\|get_finance" src tests

echo
echo "========================================="
echo "Searching app creation"
echo "========================================="

grep -RIn \
  --exclude-dir=venv \
  --exclude-dir=.git \
  --exclude-dir=__pycache__ \
  "FastAPI(" src

echo
echo "Done."
