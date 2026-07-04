# Backend Stabilization Facts

> Source of truth for backend commands, database structure, and development workflows.
> Last updated: 2026-01-03

## Commands (from Makefile)

### Development
| Command | Description |
|---------|-------------|
| `make venv` | Create virtual environment and install dependencies |
| `make run` | Start FastAPI development server (`./venv/bin/python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000`) |
| `make test` | Run pytest test suite (`./venv/bin/python -m pytest tests/ -v`) |
| `make validate` | Run pipeline validation checks (`./venv/bin/python -m src.validate_pipeline`) |
| `make clean` | Remove virtual environment |
| `make doctor` | Check environment health (`./venv/bin/python scripts/doctor.py`) |

### Dependency Management
| Command | Description |
|---------|-------------|
| `make lock` | Regenerate requirements.txt from requirements.in |

### Docker
| Command | Description |
|---------|-------------|
| `make docker-build` | Build Docker image |
| `make docker-run` | Run Docker container |
| `make docker-test` | Run tests inside Docker container |
| `make docker-compose-up` | Start with docker-compose |
| `make docker-compose-down` | Stop docker-compose |

### Database Maintenance
| Command | Description |
|---------|-------------|
| `make db-status` | Database status (`./venv/bin/python -m src.maintenance status`) |
| `make db-vacuum` | Vacuum database (`./venv/bin/python -m src.maintenance vacuum`) |
| `make db-backup` | Backup database (`./venv/bin/python -m src.maintenance backup`) |
| `make db-export` | Export to JSON (`./venv/bin/python -m src.maintenance export-json`) |
| `make db-check` | Check orphans (`./venv/bin/python -m src.maintenance check-orphans`) |
| `make db-full-maintenance` | Run full maintenance (backup + vacuum + check + status) |

## Database Paths and Data Directories

### Primary Database
- **Path**: `data/finance.db` (relative to CWD when FinanceDB is instantiated)
- **Class**: `FinanceDB` in `src/db.py`
- **Default instantiation**: `FinanceDB(db_path="data/finance.db")`

### Data Directories
| Directory | Purpose |
|-----------|---------|
| `data/backups/` | Database backups |
| `data/logs/` | Application logs |
| `data/uploads/` | Uploaded PDF/CSV files |

### Configuration
- Database path can be overridden via `db_path` parameter to `FinanceDB`
- Uses SQLite with WAL mode (`PRAGMA journal_mode=WAL`)
- Foreign keys enabled (`PRAGMA foreign_keys=ON`)
- Busy timeout: 5000ms (`PRAGMA busy_timeout=5000`)

## Schema Creation and Migrations

### Where CREATE TABLE Statements Live
All DDL (Data Definition Language) statements are defined as module-level constants in `src/db.py`:

```python
# Core tables
_DDL_STATEMENTS      # CREATE TABLE statements
_DDL_TRANSACTIONS    # CREATE TABLE transactions
_DDL_INDEXES         # CREATE INDEX statements

# Feature tables
_DDL_MEMBERS         # CREATE TABLE members
_DDL_IMPORT_MAPPINGS # CREATE TABLE import_mappings
_DDL_RECONCILIATIONS # CREATE TABLE reconciliations
_DDL_ACCOUNTS        # CREATE TABLE accounts
_DDL_CARDS           # CREATE TABLE cards
_DDL_INCOME_SOURCES  # CREATE TABLE income_sources
_DDL_LOANS           # CREATE TABLE loans
_DDL_LOAN_PAYMENTS   # CREATE TABLE loan_payments
_DDL_INVESTMENTS     # CREATE TABLE investments
_DDL_MONTHLY_SNAPSHOTS       # CREATE TABLE monthly_snapshots
_DDL_RECURRING_TRANSACTIONS  # CREATE TABLE recurring_transactions

# Triggers
_DDL_ACCOUNTS_TRIGGER            # UPDATE timestamp trigger
_DDL_CARDS_TRIGGER               # UPDATE timestamp trigger
_DDL_INCOME_SOURCES_TRIGGER      # UPDATE timestamp trigger
_DDL_LOANS_TRIGGER               # UPDATE timestamp trigger
_DDL_RECURRING_TRANSACTIONS_TRIGGER  # UPDATE timestamp trigger
```

### How to Add New Tables
1. Define a new `_DDL_*` constant in `src/db.py` with the CREATE TABLE statement
2. Add execution in `_create_tables()` method:
   ```python
   conn.execute(_DDL_NEW_TABLE)
   ```

### Migration Pattern
Migrations use `ALTER TABLE ADD COLUMN` with try/except:

```python
_migration_columns = [
    ("table_name", "column_name", "COLUMN_TYPE"),
]
for table, col, col_type in _migration_columns:
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
    except sqlite3.OperationalError:
        pass  # Column already exists
```

### Immutability Triggers
Transactions are protected by triggers:
```sql
CREATE TRIGGER prevent_transaction_update BEFORE UPDATE ON transactions
BEGIN SELECT RAISE(ABORT, 'Transactions are immutable. Cannot update.'); END;

CREATE TRIGGER prevent_transaction_delete BEFORE DELETE ON transactions
BEGIN SELECT RAISE(ABORT, 'Transactions are immutable. Cannot delete.'); END;
```

## Routers and Their Prefixes

All 17 routers are defined in `src/routers/` and registered in `src/api.py`.

| Router File | Import Name | Route Prefix (in code) |
|-------------|-------------|------------------------|
| `transactions.py` | `transactions` | `/api/transactions` |
| `upload.py` | `upload` | `/api/upload` |
| `categories.py` | `categories` | `/api/categories` |
| `accounts.py` | `accounts` | `/api/accounts` |
| `dashboard.py` | `dashboard` | `/api/dashboard/*` |
| `reconciliation.py` | `reconciliation` | `/api/reconciliation/*` |
| `behavior.py` | `behavior` | `/api/behavior` |
| `audit.py` | `audit` | `/api/audit/*` |
| `cards.py` | `cards` | `/api/cards` |
| `income_sources.py` | `income_sources` | `/api/income-sources` |
| `loans.py` | `loans` | `/api/loans/*` |
| `investments.py` | `investments` | `/api/investments` |
| `recurring.py` | `recurring` | `/api/recurring` |
| `snapshots.py` | `snapshots` | `/api/snapshots` |
| `projections.py` | `projections` | `/api/projections` |
| `export.py` | `export` | `/api/export/*` |

### Router Registration Pattern
```python
# In src/api.py
from src.routers import (
    transactions, upload, categories, accounts,
    dashboard, reconciliation, behavior, audit, cards,
    income_sources, loans, investments, recurring,
    snapshots, projections, export,
)

app.include_router(transactions.router)
app.include_router(upload.router)
# ... etc
```

### Route Definition Pattern
Routes use explicit full paths (not router prefixes):
```python
# In src/routers/transactions.py
@router.get("/api/transactions")
def get_transactions(...):
    ...
```

## Startup and Lifespan

### Lifespan Context Manager
Located in `src/api.py`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    log.info("ClariFin backend starting up")
    validator = StartupValidator(db_path=DB_PATH, upload_dir=UPLOAD_DIR)
    validator.run_all_checks()
    
    yield
    
    # Shutdown
    close_db()
    log.info("ClariFin backend shutting down")
```

### App Configuration
```python
app = FastAPI(
    title="Personal Finance API",
    description="REST API for personal finance tracker",
    version="1.0.0",
    lifespan=lifespan,
)
```

## Engines

All engines are in `src/engines/`:

| Engine | Purpose |
|--------|---------|
| `balance_engine.py` | Running balance calculations |
| `behavior_engine.py` | Behavioral analysis and scoring |
| `cashflow_engine.py` | Cash flow projections |
| `insight_generator.py` | Financial insights generation |
| `ledger_audit_engine.py` | Ledger auditing |
| `loan_engine.py` | Loan calculations and amortization |
| `networth_engine.py` | Net worth tracking |
| `nudge_engine.py` | User nudges/notifications |
| `projection_engine.py` | Financial projections |
| `reconciliation_engine.py` | Cross-account transfer matching |
| `recurring_engine.py` | Recurring transaction detection |
| `snapshot_engine.py` | Monthly snapshot generation |
| `validation_engine.py` | Statement validation (NEW) |

## PDF Extraction (B5: Extractor Interface)

The backend supports pluggable PDF extraction via the `CLARIFIN_EXTRACTOR` environment variable.

### Configuration

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `CLARIFIN_EXTRACTOR` | `legacy` \| `docling` | `legacy` | Selects the PDF extraction engine |

### Extractor Types

**Legacy Extractor** (`CLARIFIN_EXTRACTOR=legacy`):
- Uses Camelot + pdfplumber for table extraction
- Production-proven, works with all supported banks
- No additional dependencies required
- Located in `src/extraction/legacy_extractor.py`

**Docling Extractor** (`CLARIFIN_EXTRACTOR=docling`):
- Uses AI-powered Docling library for document understanding
- Requires: `pip install 'docling>=2.0.0'`
- Optional dependency - app works without it
- Located in `src/extraction/docling_extractor.py`

### Usage Examples

```bash
# Use legacy extractor (default)
./venv/bin/python -m uvicorn src.api:app

# Use docling extractor
CLARIFIN_EXTRACTOR=docling ./venv/bin/python -m uvicorn src.api:app

# Programmatic access
from src.extraction.factory import get_extractor, get_extractor_type

extractor = get_extractor()  # Returns configured extractor
result = extractor.extract("/path/to/statement.pdf")
```

### Error Handling

- If `CLARIFIN_EXTRACTOR=docling` but docling is not installed:
  - Clear error message: "Docling is not installed. Install with: pip install 'docling>=2.0.0'"
  - Statement is staged with `FAILED` status
  - HTTP 500 response with error details

- If extraction fails (PDF format issues):
  - Statement is staged with `NEEDS_REVIEW` status
  - Error message stored in statement_imports.error
  - HTTP 422 response

### Factory API

```python
from src.extraction.factory import (
    get_extractor,        # Get configured extractor instance
    get_extractor_type,   # Get current extractor type string
    is_extractor_available,  # Check if extractor can be used
    list_available_extractors  # List all extractors and status
)
```

## Key Design Patterns

1. **Immutable Ledger**: Transactions never updated/deleted (triggers enforce)
2. **Integer Paise**: All money stored as INTEGER paise (1 rupee = 100 paise)
3. **Deterministic Computation**: Same inputs → same outputs (no randomness)
4. **Hash Deduplication**: SHA256 signatures prevent duplicate transactions
5. **FinanceDB Abstraction**: All DB access through FinanceDB class
6. **Pluggable Extraction**: Extractor interface allows swapping PDF engines without changing router code
