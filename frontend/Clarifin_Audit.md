# CLARIFIN_OS - COMPLETE TECHNICAL AUDIT REPORT

---

# 1️⃣ PROJECT STRUCTURE

## Full Folder Tree (4 Levels Deep)

```
ClariFin_OS/
├── .env.example
├── README.md
├── start.sh                    # Unix launch script
├── start.bat                   # Windows launch script
├── backend/
│   ├── src/
│   │   ├── api.py              # FastAPI application (1800+ lines)
│   │   ├── db.py               # SQLite database layer (1200+ lines)
│   │   ├── main.py             # CLI entry for table extraction
│   │   ├── categorizer.py      # Transaction categorization
│   │   ├── csv_importer.py     # CSV/Excel import
│   │   ├── column_mapper.py    # Column mapping for imports
│   │   ├── statement_extractor.py
│   │   ├── metadata_extractor.py
│   │   ├── transaction_parser.py
│   │   ├── table_extractor.py
│   │   ├── validator.py
│   │   ├── ingest.py
│   │   ├── engines/
│   │   │   ├── __init__.py
│   │   │   ├── balance_engine.py       # Deterministic balance calc
│   │   │   ├── behavior_engine.py      # Behavioral analysis
│   │   │   ├── insight_generator.py    # Insight generation
│   │   │   ├── ledger_audit_engine.py  # Ledger integrity checks
│   │   │   ├── nudge_engine.py         # Financial nudges
│   │   │   └── reconciliation_engine.py # Cross-account matching
│   │   ├── extraction/
│   │   │   ├── __init__.py
│   │   │   ├── camelot_extractor.py
│   │   │   └── hybrid_extractor.py
│   │   ├── parsers/            # Bank-specific parsers
│   │   └── structural/
│   │       └── layout_analyzer.py
│   ├── data/
│   │   ├── finance.db          # SQLite database
│   │   └── uploads/            # PDF statement uploads
│   └── tests/
│       ├── test_audit_minimal.py
│       ├── test_behavior_engine.py
│       ├── test_determinism.py
│       ├── test_reconciliation.py
│       └── test_reconciliation_determinism.py
├── frontend/
│   ├── app/                    # Next.js App Router
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   ├── transactions/
│   │   ├── analytics/
│   │   ├── cards/
│   │   ├── categories/
│   │   ├── import/
│   │   ├── settings/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                 # shadcn/ui components
│   │   ├── dashboard/
│   │   ├── layout/
│   │   ├── transactions/
│   │   ├── cards/
│   │   ├── import/
│   │   ├── error-boundary.tsx
│   │   ├── theme-provider.tsx
│   │   └── theme-toggle.tsx
│   ├── lib/
│   │   ├── api/
│   │   │   └── client.ts       # Typed API client (400+ lines)
│   │   ├── hooks/
│   │   ├── parser/
│   │   ├── store/
│   │   ├── format.ts
│   │   └── utils.ts
│   ├── types/
│   │   ├── transaction.ts
│   │   ├── api.ts
│   │   └── card.ts
│   ├── tests/
│   │   ├── specs/              # Playwright test specs
│   │   ├── fixtures/
│   │   ├── utils/
│   │   └── global-setup.ts
│   └── public/
├── memory-bank/                # Project documentation
│   ├── projectbrief.md
│   ├── techContext.md
│   ├── activeContext.md
│   └── progress.md
└── servers/                    # MCP servers
    └── src/
        ├── filesystem/         # File operations
        ├── memory/             # Knowledge graph
        ├── sequentialthinking/ # Chain-of-thought
        └── everything/
```

## Configuration Files

### Frontend: `next.config.ts`
```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  distDir: 'out',
  images: { unoptimized: true },
  trailingSlash: true,
};

export default nextConfig;
```

### Frontend: `tsconfig.json`
- Target: ES2017
- Strict mode: ENABLED
- JSX: react-jsx
- Module resolution: bundler
- Path alias: `@/*` → `./*`

### Frontend: `playwright.config.ts`
- Test directory: `./tests/specs`
- Parallel execution: ENABLED
- Retry on CI: 2 attempts
- Browsers: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari, Tablet
- Global timeout: 30s per test
- Web server: `npm start` on port 3000

### Backend: `requirements.txt`
```
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
camelot-py[cv]>=1.0.0
pdfplumber>=0.11.9
opencv-python-headless>=4.8.0
ghostscript>=0.7
pandas>=2.0.0
numpy>=1.24.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx
python-multipart>=0.0.6
aiofiles>=23.0.0
```

### Backend: `pyrightconfig.json`
- Type checking mode: strict
- Python version: 3.10+

## Entry Points

| Component | Entry Point | Execution Command |
|-----------|-------------|-------------------|
| Frontend Dev | `frontend/app/page.tsx` | `npm run dev` (port 3000) |
| Frontend Build | `next.config.ts` | `npm run build` → `out/` |
| Backend API | `backend/src/api.py:app` | `uvicorn src.api:app --port 8000` |
| Backend CLI | `backend/src/main.py` | `python src/main.py` |
| Unix Launcher | `start.sh` | `./start.sh` (orchestrates both) |
| Windows Launcher | `start.bat` | `start.bat` |

## Environment Variables

```bash
# .env.example
NEXT_PUBLIC_API_URL=http://localhost:8000    # Frontend → Backend
DATABASE_PATH=./data/finance.db              # Optional override
FRONTEND_PORT=3000
BACKEND_PORT=8000
```

## Package Managers

- **Frontend**: npm (package-lock.json present)
- **Backend**: pip (requirements.txt)
- **MCP Servers**: npm workspaces

## Full Dependency List

### Production Dependencies (Frontend)
| Package | Version |
|---------|---------|
| next | 16.1.6 |
| react | 19.2.3 |
| react-dom | 19.2.3 |
| typescript | ^5 |
| tailwindcss | ^4 |
| @tailwindcss/postcss | ^4 |
| pdfjs-dist | ^5.4.624 |
| zustand | ^5.0.11 |
| recharts | ^3.7.0 |
| chart.js | ^4.5.1 |
| react-chartjs-2 | ^5.3.1 |
| react-dropzone | ^14.4.0 |
| date-fns | ^4.1.0 |
| lucide-react | ^0.563.0 |
| next-themes | ^0.4.6 |
| radix-ui | ^1.4.3 |

### Production Dependencies (Backend)
| Package | Version |
|---------|---------|
| fastapi | >=0.100.0 |
| uvicorn | >=0.23.0 |
| camelot-py | >=1.0.0 |
| pdfplumber | >=0.11.9 |
| opencv-python-headless | >=4.8.0 |
| ghostscript | >=0.7 |
| pandas | >=2.0.0 |
| numpy | >=1.24.0 |
| python-multipart | >=0.0.6 |
| aiofiles | >=23.0.0 |

## Build System

| Component | Build Tool | Output |
|-----------|------------|--------|
| Frontend | Next.js 16 + Turbopack | `frontend/out/` (static export) |
| Backend | None (interpreted) | N/A |
| Tests | Playwright | HTML + JSON reports |

## Runtime Environment

- **Node.js**: 18+ (frontend)
- **Python**: 3.10+ (backend)
- **SQLite**: 3.x (bundled)
- **OS**: Linux 6.17 (production), cross-platform dev

## Deployment Architecture

NOT IMPLEMENTED - Local development only. No containerization, no CI/CD, no production deployment configuration.

---

# 2️⃣ SYSTEM ARCHITECTURE

## Architectural Style: **MODULAR MONOLITH**

- Single backend process (FastAPI)
- Single frontend process (Next.js)
- Deterministic computation engines
- Immutable ledger design
- No microservices
- No event bus

## High-Level Component Map

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Browser   │  │  Next.js    │  │    React Components     │ │
│  │   (User)    │  │   (SSR/SSG) │  │  (Dashboard, Charts)    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────┬───────────────────────────────┘
                                  │ HTTP/REST
┌─────────────────────────────────▼───────────────────────────────┐
│                      API LAYER (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Router → Middleware → Controller → Pydantic Validation     ││
│  │  CORS enabled: localhost:3000, localhost:3001               ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────┬───────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│                   SERVICE LAYER (Engines)                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│
│  │BalanceEngine │ │BehaviorEngine│ │   ReconciliationEngine   ││
│  │              │ │              │ │                          ││
│  │• compute_    │ │• 5 behavioral│ │ • find_potential_matches ││
│  │  running_    │ │  indices     │ │ • confidence scoring     ││
│  │  balance     │ │• health score│ │ • deterministic matching ││
│  └──────────────┘ └──────────────┘ └──────────────────────────┘│
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│
│  │LedgerAudit   │ │InsightGen    │ │     NudgeEngine          ││
│  │  Engine      │ │              │ │                          ││
│  │• hash verify │ │• evidence-   │ │ • priority-sorted nudges ││
│  │• integrity   │ │  based       │ │ • habit suggestions      ││
│  └──────────────┘ └──────────────┘ └──────────────────────────┘│
└─────────────────────────────────┬───────────────────────────────┘
                                  │ SQL (sqlite3)
┌─────────────────────────────────▼───────────────────────────────┐
│                      DATA LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  SQLite Database (backend/data/finance.db)                   ││
│  │  • WAL mode enabled                                          ││
│  │  • Foreign keys enforced                                     ││
│  │  • Immutable transaction triggers                            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Core Modules and Responsibilities

| Module | Responsibility | Key Files |
|--------|----------------|-----------|
| **API Layer** | HTTP routing, validation, CORS | `api.py` |
| **Database Layer** | SQL operations, migrations | `db.py` |
| **PDF Pipeline** | Extract, parse, categorize | `statement_extractor.py`, `table_extractor.py` |
| **Balance Engine** | Deterministic balance computation | `balance_engine.py` |
| **Behavior Engine** | Behavioral analysis (5 indices) | `behavior_engine.py` |
| **Reconciliation** | Cross-account transfer matching | `reconciliation_engine.py` |
| **Audit Engine** | Ledger integrity verification | `ledger_audit_engine.py` |
| **Frontend API** | Typed HTTP client | `client.ts` |
| **State Management** | UI state (Zustand) | `store/` |

## Data Flow Between Modules

```
PDF Upload
    ↓
StatementExtractor (table extraction)
    ↓
TransactionParser (row parsing)
    ↓
Categorizer (keyword matching)
    ↓
FinanceDB.insert_transactions() (with hash_signature)
    ↓
BalanceEngine.compute_running_balance() (replay)
    ↓
BehaviorEngine.compute_behavior_profile() (analysis)
    ↓
Frontend via REST API
```

## Communication Patterns

| Pattern | Usage |
|---------|-------|
| **Synchronous HTTP** | Frontend ↔ Backend (REST) |
| **Synchronous SQL** | Backend ↔ SQLite |
| **No Async Queues** | All processing is inline |
| **No Pub-Sub** | No event bus |
| **No WebSockets** | Polling not implemented |

## Initialization Sequence

```
1. start.sh
   ├── Activate Python venv
   ├── pip install -r requirements.txt
   ├── uvicorn src.api:app (port 8000)
   ├── npm install
   ├── npm run build
   └── npx serve out -p 3000

2. Backend First Request
   └── FinanceDB._create_tables()
       ├── CREATE TABLE IF NOT EXISTS statements
       ├── CREATE TABLE IF NOT EXISTS transactions
       ├── CREATE TABLE IF NOT EXISTS reconciliations
       ├── CREATE TABLE IF NOT EXISTS accounts
       ├── CREATE TABLE IF NOT EXISTS cards
       └── Run migrations (ALTER TABLE for new columns)

3. Frontend Load
   └── React hydration
       ├── Fetch /api/overview
       ├── Fetch /api/behavior/summary
       └── Render dashboard
```

## Shutdown Sequence

NOT IMPLEMENTED - Processes killed via SIGTERM. No graceful shutdown hooks.

## Dependency Graph

```
api.py
├── db.py (direct import)
├── engines/balance_engine.py
├── engines/behavior_engine.py
├── engines/reconciliation_engine.py
├── engines/ledger_audit_engine.py
├── categorizer.py
├── statement_extractor.py
└── metadata_extractor.py

db.py
└── sqlite3 (stdlib)

engines/*.py
└── db.py (via function parameters)

frontend/lib/api/client.ts
└── fetch() (native)
```

## Execution Pipeline (Real Names)

```
HTTP Request (POST /api/upload)
    ↓
CORS Middleware (fastapi.middleware.cors)
    ↓
api.upload_statement() (api.py:950-1100)
    ↓
StatementExtractor.extract() (statement_extractor.py)
    ↓
TableExtractor.find_transaction_tables() (table_extractor.py)
    ↓
TransactionParser.parse_dataframe() (transaction_parser.py)
    ↓
Categorizer.categorize() (categorizer.py)
    ↓
FinanceDB.insert_transactions() (db.py:400-500)
    ↓
FinanceDB.update_statement_metadata() (db.py:800-850)
    ↓
JSON Response → Frontend
```

---

# 3️⃣ REQUEST / EXECUTION PIPELINE

## Single Request Lifecycle: `GET /api/overview`

```
Incoming HTTP GET /api/overview
    ↓
[STAGE 1: CORS Middleware]
    File: fastapi/middleware/cors.py (built-in)
    ↓
[STAGE 2: Route Resolution]
    File: backend/src/api.py
    Function: get_overview() (lines ~300-450)
    ↓
[STAGE 3: Database Connection]
    File: backend/src/api.py
    Function: get_db() → FinanceDB(db_path)
    ↓
[STAGE 4: Data Retrieval]
    File: backend/src/db.py
    Function: get_all_transactions_with_bank({})
    SQL: SELECT ... FROM transactions t JOIN statements s
    ↓
[STAGE 5: Data Enrichment]
    File: backend/src/api.py
    Function: enrich_transaction() (lines ~180-220)
    Function: compute_is_large() (lines ~240-260)
    Function: compute_behavioral_insights() (lines ~300-400)
    ↓
[STAGE 6: Response Formatting]
    File: backend/src/api.py
    Pydantic: Implicit dict serialization
    ↓
[STAGE 7: HTTP Response]
    Content-Type: application/json
    Status: 200 OK
```

## Input Validation Layer

| Endpoint | Validation | File |
|----------|------------|------|
| POST /api/upload | File extension check (.pdf) | `api.py:upload_statement()` |
| POST /api/accounts | Pydantic AccountCreate model | `api.py:AccountCreate` |
| PUT /api/accounts/{id} | Pydantic AccountUpdate model | `api.py:AccountUpdate` |
| Query params | Query() validators | `api.py:get_transactions()` |

## Error Handling Layer

```python
# Pattern in api.py
try:
    result = operation()
    return result
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

**NO GLOBAL ERROR HANDLER** - Each endpoint wraps in try/except individually.

## Middleware Layers

```
Request
    ↓
CORSMiddleware (allow_origins: ["http://localhost:3000", "http://localhost:3001"])
    ↓
Router
    ↓
Endpoint Handler
```

**NO AUTHENTICATION MIDDLEWARE** - Open API, no auth.

---

# 4️⃣ CORE BUSINESS LOGIC

## Main Algorithms

### Algorithm 1: Deterministic Balance Replay

**File**: `backend/src/engines/balance_engine.py`

```python
def compute_running_balance(db_path, account_id, starting_balance_paise=0):
    # Step 1: Query transactions ordered by date_iso ASC, id ASC
    rows = SELECT id, date_iso, debit, credit, description, account_id
           FROM transactions
           WHERE account_id = ?
           ORDER BY date_iso ASC, id ASC
    
    # Step 2: Replay sequentially
    balance = starting_balance_paise
    results = []
    for row in rows:
        balance += row['credit'] - row['debit']
        results.append({
            'transaction_id': row['id'],
            'balance_paise': balance,
            ...
        })
    
    return results
```

**Time Complexity**: O(n) where n = transaction count
**Space Complexity**: O(n) for results storage

### Algorithm 2: Behavioral Index Calculation

**File**: `backend/src/engines/behavior_engine.py`

```python
def compute_behavior_profile(db_path):
    # Step 1: Get 90 days of transactions
    transactions = _get_transactions_90_days(db_path)
    
    # Step 2: Calculate 5 behavioral indices
    loss_aversion = _compute_loss_aversion_index(transactions)
    impulsivity = _compute_impulsivity_score(transactions)
    habit_stability = _compute_habit_stability_score(transactions)
    financial_stress = _compute_financial_stress_index(transactions)
    savings_discipline = _compute_savings_discipline_score(transactions)
    
    # Step 3: Weighted composite health score
    health_score = (
        0.20 * savings_discipline["score"] +
        0.18 * habit_stability["score"] +
        0.18 * (1 - impulsivity["score"]) +
        0.18 * (1 - financial_stress["score"]) +
        0.13 * (1 - loss_aversion["score"]) +
        0.13 * buffer_score
    ) * 100
    
    return health_score
```

### Algorithm 3: Reconciliation Matching

**File**: `backend/src/engines/reconciliation_engine.py`

```python
def find_potential_matches(db_path, max_date_window_days=3):
    # Step 1: Get all transactions with debit/credit
    transactions = SELECT id, date_iso, debit, credit, account_id
                   FROM transactions
                   WHERE (debit > 0 OR credit > 0)
                   ORDER BY (debit + credit) ASC, date_iso ASC, id ASC
    
    # Step 2: Compare all pairs (O(n²))
    matches = []
    for i, txn_a in enumerate(transactions):
        for txn_b in transactions[i+1:]:
            # Check: opposite amounts, different accounts, date within window
            if _check_match(txn_a, txn_b):
                confidence = _calculate_confidence(date_diff, amount_exact, desc_similarity)
                matches.append({...})
    
    return matches
```

**Time Complexity**: O(n²) - quadratic on transaction count
**Bottleneck**: Nested loop for cross-account matching

### Algorithm 4: Hash Signature Generation

**File**: `backend/src/db.py` (line ~450)

```python
# Hash formula for immutability
hash_input = f"{account_id}|{date_iso}|{description}|{debit_paise}|{credit_paise}"
hash_signature = hashlib.sha256(hash_input.encode()).hexdigest().lower()

# Used for duplicate detection
UNIQUE INDEX on hash_signature
```

## Core Data Transformations

| Transformation | Source | Target | Logic |
|----------------|--------|--------|-------|
| Amount parsing | String ("₹1,234.56") | Float (1234.56) | Regex + float() |
| Paise conversion | Float (1234.56) | Integer (123456) | int(round(amount * 100)) |
| Date normalization | Various formats | ISO 8601 (YYYY-MM-DD) | Multi-format parser |
| Category assignment | Description string | Category enum | Keyword matching |
| Balance computation | Transaction list | Running balances | Sequential replay |

## Decision Trees

### Categorizer Decision Tree

```
Description (lower case)
    ↓
Contains "swiggy|zomato|restaurant"?
    ↓ YES → Category: "Food & Dining"
    ↓ NO
Contains "amazon|flipkart|shopping"?
    ↓ YES → Category: "Shopping"
    ↓ NO
Contains "uber|ola|petrol|diesel"?
    ↓ YES → Category: "Transport"
    ↓ NO
...
    ↓ DEFAULT → Category: "Uncategorized"
```

**File**: `backend/src/categorizer.py`

## State Transitions

### Transaction State (Immutable)

```
[IMPORTED] → (no state changes allowed)

Ledger Immutability Guarantees:
- INSERT OR IGNORE only
- No UPDATE operations (trigger blocks)
- No DELETE operations (trigger blocks)
- Corrections via compensating transactions
```

### Reconciliation State

```
CREATED (status='pending')
    ↓ confirm_reconciliation()
CONFIRMED (status='confirmed')

CREATED (status='pending')
    ↓ reject_reconciliation()
REJECTED (status='rejected')
```

## Rule Engines

### Behavioral Index Rules

**File**: `backend/src/engines/behavior_engine.py`

| Index | Rule | Weight |
|-------|------|--------|
| Loss Aversion | Post-income velocity > 1.5 = high | 0.13 |
| Impulsivity | Micro-txn ratio > 0.8 = high | 0.18 |
| Habit Stability | Category CV < 0.5 = stable | 0.18 |
| Financial Stress | EOM depletion ratio > 0.5 = high | 0.18 |
| Savings Discipline | Savings rate > 0.2 = good | 0.20 |

### Confidence Calculation Rules

**File**: `backend/src/engines/reconciliation_engine.py`

| Factor | Condition | Weight |
|--------|-----------|--------|
| Same date | date_diff == 0 | +0.4 |
| Within 1 day | date_diff == 1 | +0.3 |
| Exact amount | amount_exact | +0.4 |
| Description match | similarity > 0.7 | +0.2 |
| **CAP** | max | 1.0 |

## Task Orchestration

NOT IMPLEMENTED - No background job system. All processing is synchronous:
- PDF processing blocks HTTP response
- Large files may cause timeouts
- No Celery/RQ/Redis

## Scheduling Mechanisms

NOT IMPLEMENTED - No cron, no schedulers, no periodic tasks.

---

# 5️⃣ TOOLING / INTEGRATIONS

## External Integrations

### 1. SQLite Database

| Attribute | Value |
|-----------|-------|
| **File** | `backend/src/db.py` |
| **Input** | SQL queries, parameters |
| **Output** | Row dictionaries |
| **Sync/Async** | Synchronous (blocking) |
| **Retry** | None |
| **Timeout** | None (OS default) |
| **Error Handling** | Exception propagation |
| **Side Effects** | Persistent storage |
| **Connection Pooling** | No (new connection per request) |

### 2. PDF Processing (camelot-py)

| Attribute | Value |
|-----------|-------|
| **File** | `backend/src/extraction/camelot_extractor.py` |
| **Input** | PDF file path |
| **Output** | pandas DataFrame (table data) |
| **Sync/Async** | Synchronous |
| **Retry** | None |
| **Timeout** | None |
| **Error Handling** | Try/except with fallback |
| **Side Effects** | None (read-only) |
| **External Dependencies** | Ghostscript, OpenCV |

### 3. PDF Processing (pdfplumber)

| Attribute | Value |
|-----------|-------|
| **File** | `backend/src/statement_extractor.py` |
| **Input** | PDF file path |
| **Output** | Extracted text, tables |
| **Sync/Async** | Synchronous |
| **Retry** | None |
| **Timeout** | None |
| **Error Handling** | Exception propagation |
| **Side Effects** | None (read-only) |

### 4. HTTP Client (Frontend)

| Attribute | Value |
|-----------|-------|
| **File** | `frontend/lib/api/client.ts` |
| **Input** | Endpoint, params, body |
| **Output** | Typed response objects |
| **Sync/Async** | Asynchronous (Promise-based) |
| **Retry** | None |
| **Timeout** | None (browser default) |
| **Error Handling** | throw Error with status code |
| **Side Effects** | Network requests |

### 5. Playwright E2E Testing

| Attribute | Value |
|-----------|-------|
| **File** | `frontend/playwright.config.ts` |
| **Input** | Test specs |
| **Output** | Test results, screenshots, videos |
| **Sync/Async** | Asynchronous |
| **Retry** | 2 retries on CI |
| **Timeout** | 30s per test |
| **Browsers** | Chromium, Firefox, WebKit, Mobile |
| **Side Effects** | Browser automation |

## Internal Tools

### Hash Generator

| Attribute | Value |
|-----------|-------|
| **File** | `backend/src/db.py` |
| **Input** | account_id, date_iso, description, debit, credit |
| **Output** | SHA256 hex string |
| **Algorithm** | SHA256(account_id\|date_iso\|description\|debit\|credit) |

### Column Mapper

| Attribute | Value |
|-----------|-------|
| **File** | `backend/src/column_mapper.py` |
| **Input** | List of column names from CSV/Excel |
| **Output** | Mapping to standard fields (date, description, amount, type) |
| **Logic** | Fuzzy string matching on column names |

## Dynamic Loading

NOT IMPLEMENTED - No plugin system, no dynamic imports, no service registry.

## Dependency Injection

NOT IMPLEMENTED - Direct instantiation pattern:
```python
def get_db():
    return FinanceDB(db_path=DB_PATH)  # Direct instantiation
```

---

# 6️⃣ DATA LAYER

## Database: SQLite 3.x

### Schema Design

#### Table: `statements`
```sql
CREATE TABLE statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank TEXT NOT NULL,
    card_last4 TEXT,
    statement_period_from TEXT,
    statement_period_to TEXT,
    file_name TEXT NOT NULL,
    imported_at TEXT DEFAULT (datetime('now')),
    total_amount_due REAL,
    minimum_amount_due REAL,
    payment_due_date TEXT,
    credit_limit REAL,
    opening_balance REAL,
    bill_cycle_start TEXT,
    bill_cycle_end TEXT,
    validation_status TEXT DEFAULT 'pending',
    validation_difference REAL,
    UNIQUE(bank, file_name)
);
```

#### Table: `transactions` (Immutable Ledger)
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id INTEGER NOT NULL REFERENCES statements(id),
    sequence_num INTEGER NOT NULL DEFAULT 0,
    date TEXT NOT NULL,
    description TEXT,
    amount REAL NOT NULL,
    type TEXT CHECK(type IN ('debit', 'credit', '')),
    category TEXT DEFAULT 'Uncategorized',
    subcategory TEXT,
    member TEXT DEFAULT 'Self',
    source TEXT DEFAULT 'pdf',
    -- Phase 2A: Financial determinism
    debit INTEGER DEFAULT 0,
    credit INTEGER DEFAULT 0,
    amount_paise INTEGER DEFAULT 0,
    date_iso TEXT,
    hash_signature TEXT UNIQUE,
    account_id TEXT,
    FOREIGN KEY(statement_id) REFERENCES statements(id)
);
```

#### Table: `reconciliations`
```sql
CREATE TABLE reconciliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    debit_txn_id INTEGER NOT NULL,
    credit_txn_id INTEGER NOT NULL,
    debit_account_id TEXT NOT NULL,
    credit_account_id TEXT NOT NULL,
    amount REAL NOT NULL,
    date_diff_days INTEGER DEFAULT 0,
    match_confidence REAL DEFAULT 0.0,
    match_type TEXT NOT NULL,  -- 'exact', 'window', 'fuzzy', 'manual'
    status TEXT DEFAULT 'pending',
    deterministic_key TEXT UNIQUE,
    created_at TEXT DEFAULT (datetime('now')),
    confirmed_at TEXT
);
```

#### Table: `accounts`
```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    bank_name TEXT DEFAULT '',
    account_type TEXT CHECK(account_type IN ('savings', 'current', 'credit_card', 'fd', 'wallet', 'loan')),
    account_number_masked TEXT DEFAULT 'XXXX',
    balance_paise INTEGER DEFAULT 0,
    credit_limit_paise INTEGER DEFAULT 0,
    currency TEXT DEFAULT 'INR',
    color TEXT DEFAULT '#6366F1',
    icon TEXT DEFAULT 'building',
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
```

### ORM or Query Builder

**NOT IMPLEMENTED** - Raw SQL only via `sqlite3` module:
```python
conn.execute("SELECT * FROM transactions WHERE id = ?", (id,))
```

### Migrations System

**NOT IMPLEMENTED** - Ad-hoc migrations in `db.py:_create_tables()`:
```python
# Try to add column, ignore if exists
try:
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
except Exception:
    pass  # column already exists
```

### Indexing Strategy

```sql
-- Primary indexes
CREATE INDEX idx_txn_date ON transactions(date);
CREATE INDEX idx_txn_category ON transactions(category);
CREATE INDEX idx_txn_statement ON transactions(statement_id);
CREATE INDEX idx_txn_type ON transactions(type);

-- Phase 2A indexes
CREATE INDEX idx_txn_date_iso ON transactions(date_iso);
CREATE UNIQUE INDEX idx_transaction_hash ON transactions(hash_signature);
CREATE INDEX idx_account_date_iso ON transactions(account_id, date_iso, id);
```

### Caching Layer

NOT IMPLEMENTED - No Redis, no in-memory cache, no query caching.

### Cache Invalidation Logic

NOT IMPLEMENTED

### Data Consistency Model

**Eventual Consistency** with strong local consistency:
- Single SQLite file (no replication)
- WAL mode for concurrent reads
- No distributed transactions

### Transaction Management

```python
# Pattern in db.py
conn.execute("BEGIN")
try:
    conn.execute("INSERT INTO ...")
    conn.execute("UPDATE ...")
    conn.commit()
except:
    conn.rollback()
    raise
```

### Connection Pooling

NOT IMPLEMENTED - New connection per request:
```python
def _connect(self):
    conn = sqlite3.connect(self.db_path)  # Fresh connection
    conn.execute("PRAGMA journal_mode=WAL")
    return conn
```

### Read/Write Separation

NOT IMPLEMENTED - Single SQLite database, all operations on same file.

---

# 7️⃣ STATE MANAGEMENT

## Where Runtime State Is Stored

| State Type | Storage | Persistence |
|------------|---------|-------------|
| Transaction Data | SQLite | Persistent (disk) |
| Account/Card Data | SQLite | Persistent (disk) |
| UI State (React) | Component state | Ephemeral |
| Global UI State | Zustand store | Ephemeral |
| Theme Preference | localStorage | Persistent (browser) |
| Dashboard Mode | localStorage | Persistent (browser) |
| API Cache | React Query | Ephemeral (memory) |

## In-Memory Structures

### Backend (Python)
- No global state
- No shared memory
- Each request: new DB connection, fresh data

### Frontend (TypeScript)
```typescript
// Zustand store pattern
interface AppState {
  transactions: Transaction[];
  selectedBank: string;
  selectedCategory: string;
  // ... more state
}
```

## Session Management

NOT IMPLEMENTED - No sessions, no cookies, no JWT. Stateless API.

## Cross-Request Persistence

- **Backend**: None (stateless)
- **Frontend**: localStorage for user preferences

## Shared State

| Resource | Shared? | Protection |
|----------|---------|------------|
| SQLite DB | Yes (process level) | WAL mode + file locks |
| Uploaded files | Yes | Filesystem permissions |
| In-memory caches | No | N/A |

## Global Variables

### Backend
```python
# api.py - Module-level constants
DB_PATH = str(Path(__file__).parent.parent / "data" / "finance.db")
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
```

### Frontend
None - Uses React hooks and Zustand for state.

## Concurrency Handling

| Layer | Mechanism |
|-------|-----------|
| SQLite | WAL mode (write-ahead logging) |
| File uploads | Unique filename constraints |
| API | FastAPI async handlers (single process) |

## Thread Safety

- **Backend**: SQLite connections are per-request (not shared)
- **Frontend**: React single-threaded, no web workers

## Race Condition Risks

| Risk | Location | Mitigation |
|------|----------|------------|
| Duplicate upload | `db.py:insert_statement()` | UNIQUE(bank, file_name) |
| Duplicate transaction | `db.py:insert_transactions()` | UNIQUE hash_signature |
| Concurrent reconciliations | `db.py:insert_reconciliation()` | UNIQUE deterministic_key |

## Horizontal Scaling Implications

**NOT SUPPORTED**:
- Single SQLite file cannot be shared across multiple backend instances
- No read replicas
- No load balancing
- Single process deployment only

---

# 8️⃣ FILE SYSTEM & I/O

## File Read/Write Implementation

### Backend (Python)
```python
# Upload handling (async)
content = await file.read()
with open(save_path, "wb") as f:
    f.write(content)

# CSV import (pandas)
df = pd.read_csv(file_path)
```

### Frontend (TypeScript)
```typescript
// API client
const res = await fetch(`${API_BASE}/api/upload`, {
  method: 'POST',
  body: formData,
});
```

## Streaming vs Buffered I/O

| Operation | Mode | Buffer Size |
|-----------|------|-------------|
| PDF Upload | Buffered | Entire file in memory |
| CSV Import | Buffered | pandas loads entire file |
| Transaction query | Streaming | SQLite cursor (chunked) |
| CSV Export | Streaming | StringIO buffer |

## Large File Handling

**NOT OPTIMIZED** - PDFs loaded entirely into memory:
```python
content = await file.read()  # Entire file in memory
# No streaming, no chunking
```

Risk: Large PDFs (>100MB) may cause memory issues.

## Temporary File Usage

NOT IMPLEMENTED - Files saved directly to `backend/data/uploads/`:
```python
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
save_path = UPLOAD_DIR / filename
```

No temp directory, no cleanup of failed uploads.

## File Locking Strategy

NOT IMPLEMENTED - Relies on SQLite WAL mode for concurrency:
```sql
PRAGMA journal_mode=WAL
```

## Backup/Rollback Strategy

NOT IMPLEMENTED - No automated backups:
- SQLite `.backup` command not used
- No point-in-time recovery
- Manual copy of `finance.db` only

## Destructive Action Protection

| Action | Protection |
|--------|------------|
| File overwrite | None - `open(path, "wb")` overwrites |
| DB delete | Immutable triggers prevent txn deletion |
| Statement delete | Removed (Phase 2A.1) - ledger immutable |

## Sandboxing

NOT IMPLEMENTED - Backend has full filesystem access to:
- `backend/data/`
- `backend/src/`
- Any path readable by OS user

## Permission Model

| Resource | Permissions |
|----------|-------------|
| SQLite DB | OS user permissions |
| Upload directory | OS user permissions |
| Source code | OS user permissions |
| API endpoints | No authentication (open) |

---

# 9️⃣ ERROR HANDLING & RESILIENCE

## Global Error Handler

NOT IMPLEMENTED - Each endpoint handles errors individually:
```python
@app.get("/api/overview")
def get_overview():
    try:
        # ... logic
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Structured Error Types

NOT IMPLEMENTED - All errors are generic `Exception` with string messages.

## Retry Policies

NOT IMPLEMENTED - No automatic retry for:
- Database connections
- File operations
- HTTP requests

## Exponential Backoff

NOT IMPLEMENTED

## Dead-Letter Queues

NOT IMPLEMENTED - No queue system.

## Logging System

NOT IMPLEMENTED - No structured logging:
- No log levels (DEBUG, INFO, WARN, ERROR)
- No log rotation
- Console output only via `print()` statements

## Monitoring Hooks

NOT IMPLEMENTED - No metrics, no health checks, no telemetry.

## Observability Stack

NOT IMPLEMENTED - No:
- APM (Application Performance Monitoring)
- Distributed tracing
- Error tracking (Sentry, etc.)
- Dashboards (Grafana, etc.)

## Alerting Mechanisms

NOT IMPLEMENTED - No alerts for:
- High error rates
- Slow queries
- Disk space
- Service downtime

## Crash Recovery Behavior

| Scenario | Behavior |
|----------|----------|
| Backend crash | Transactions may be incomplete; SQLite WAL recovers |
| Frontend crash | React ErrorBoundary shows fallback UI |
| Browser refresh | State lost (except localStorage) |

---

# 🔟 SECURITY MODEL

## Input Sanitization

NOT IMPLEMENTED - No explicit sanitization:
- SQL injection protection: Parameterized queries (✓)
- XSS protection: React escapes by default (✓)
- File path validation: None (trusts OS)

## Validation Strategy

| Layer | Validation |
|-------|------------|
| API | Pydantic models for POST/PUT |
| Database | SQLite type constraints |
| Frontend | Form validation (minimal) |

## Auth System

NOT IMPLEMENTED - Open API, no authentication.

## Authorization Model

NOT IMPLEMENTED - No RBAC, no permissions, no user roles.

## Secret Management

NOT IMPLEMENTED - No secrets to manage (no API keys, no tokens).

## Environment Variable Protection

```bash
# .env.example (no secrets)
NEXT_PUBLIC_API_URL=http://localhost:8000  # Public, safe
DATABASE_PATH=./data/finance.db            # Path only
```

## Command Execution Safety

NOT IMPLEMENTED - Backend does not execute shell commands.

## Sandbox Boundaries

| Boundary | Status |
|----------|--------|
| Process | Backend runs as OS user |
| Filesystem | Full access to project directory |
| Network | Full outbound access |
| Database | File-based, no network exposure |

## External Attack Surface

| Vector | Risk | Mitigation |
|--------|------|------------|
| SQL Injection | LOW | Parameterized queries |
| XSS | LOW | React escaping |
| File Upload | MEDIUM | Extension check only |
| Path Traversal | MEDIUM | No validation on paths |
| CSRF | MEDIUM | No CSRF tokens |
| DoS | HIGH | No rate limiting |

## Dependency Vulnerability Management

NOT IMPLEMENTED - No:
- Dependency scanning (Snyk, Dependabot)
- Automated updates
- SBOM generation

## Rate Limiting

NOT IMPLEMENTED - No rate limits on any endpoint.

## DOS Protection

NOT IMPLEMENTED - No protection against:
- Large file uploads
- Expensive query parameters
- Brute force attacks

---

# 1️⃣1️⃣ PERFORMANCE PROFILE

PERFORMANCE METRICS NOT IMPLEMENTED

No monitoring, no benchmarks, no profiling data collected.

## Inferred Characteristics

| Metric | Estimated Value |
|--------|-----------------|
| Average API response | 100-500ms |
| Large file upload | 5-30s (depends on PDF size) |
| Balance computation | O(n) with n=transaction count |
| Reconciliation matching | O(n²) - quadratic slowdown risk |

## Known Bottlenecks

| Bottleneck | Location | Impact |
|------------|----------|--------|
| PDF table extraction | `camelot_extractor.py` | CPU-intensive, blocking |
| Reconciliation matching | `reconciliation_engine.py` | O(n²) - slow with many transactions |
| Database queries | `db.py:get_all_transactions_with_bank()` | No pagination, loads all rows |
| Frontend build | `npm run build` | Next.js static export |

---

# 1️⃣2️⃣ CONCURRENCY & SCALING

## Threading Model

| Component | Model |
|-----------|-------|
| Backend | Single-threaded async (FastAPI + uvicorn) |
| SQLite | Multi-threaded safe (WAL mode) |
| Frontend | Single-threaded (JavaScript event loop) |

## Worker Processes

NOT IMPLEMENTED - Single process deployment only.

## Clustering

NOT IMPLEMENTED - Cannot run multiple backend instances (SQLite limitation).

## Load Balancing

NOT IMPLEMENTED - Single server only.

## Horizontal Scaling Support

NOT SUPPORTED - Would require:
- PostgreSQL instead of SQLite
- Shared file storage (S3)
- Session store (Redis)
- Load balancer

## Stateless Design

**PARTIAL** - Backend is stateless but SQLite file ties to single instance.

## Shared Resource Contention

| Resource | Contention Risk | Mitigation |
|----------|-----------------|------------|
| SQLite DB | Medium | WAL mode |
| Upload directory | Low | Unique filenames |
| Memory | Low | Single process |

## Locking Mechanisms

| Layer | Mechanism |
|-------|-----------|
| SQLite | File-level locking via WAL |
| Application | None (single process) |

## Async Queue Usage

NOT IMPLEMENTED - No queues, all processing inline.

---

# 1️⃣3️⃣ DEPLOYMENT PIPELINE

CI/CD SYSTEM: NOT IMPLEMENTED

No automated build, test, or deployment pipeline.

## Manual Deployment Steps

```bash
# 1. Build frontend
cd frontend
npm install
npm run build

# 2. Start backend
cd ../backend
source venv/bin/activate
uvicorn src.api:app --host 0.0.0.0 --port 8000

# 3. Serve frontend
npx serve out -p 3000
```

## Build Stages

NOT IMPLEMENTED - No CI pipeline.

## Test Stages

NOT IMPLEMENTED - Manual test execution:
```bash
cd frontend
npx playwright test
```

## Artifact Generation

NOT IMPLEMENTED - No artifacts, no versioning, no releases.

## Containerization

NOT IMPLEMENTED - No Dockerfile, no Docker Compose.

## Infrastructure-as-Code

NOT IMPLEMENTED - No Terraform, no CloudFormation, no Helm charts.

## Environment Separation

NOT IMPLEMENTED - No dev/stage/prod environments.

## Rollback Strategy

NOT IMPLEMENTED - No rollback capability.

## Versioning Strategy

NOT IMPLEMENTED - No semantic versioning, no release tags.

---

# 1️⃣4️⃣ CODE QUALITY ANALYSIS

## Dead Code

| Location | Issue |
|----------|-------|
| `backend/_archived_reflex_dashboard/` | Entire directory unused |
| `backend/src/structural/layout_analyzer.py` | Likely unused |
| `frontend/lib/parser/` | Legacy parser code |

## Unused Modules

| Module | Status |
|--------|--------|
| `backend/src/ingest.py` | May be unused (duplicate of upload) |
| `backend/src/validator.py` | Unclear usage |

## Circular Dependencies

NOT DETECTED - Clean import tree.

## Overly Large Files

| File | Lines | Issue |
|------|-------|-------|
| `backend/src/api.py` | ~1800 | Too many endpoint groups |
| `backend/src/db.py` | ~1200 | DDL + DML + migrations mixed |
| `frontend/lib/api/client.ts` | ~400 | Multiple concerns |

## God Classes/Functions

| Function | Lines | Responsibility |
|----------|-------|----------------|
| `api.get_overview()` | ~150 | Query + compute + format |
| `api.upload_statement()` | ~120 | Upload + extract + validate + insert |
| `db.insert_transactions()` | ~80 | Insert + hash + dedupe |

## Tight Coupling

| Area | Coupling |
|------|----------|
| API → DB | Direct instantiation (no repository) |
| Engines → DB | Direct SQL queries |
| Frontend → Backend | Hardcoded API URLs |

## Duplicate Logic

| Duplication | Locations |
|-------------|-----------|
| Date parsing | `db.py`, `api.py`, `behavior_engine.py`, `balance_engine.py` |
| INR formatting | `api.py:format_inr()`, `balance_engine.py:_format_paise()` |
| Amount parsing | `db.py:_parse_amount()`, multiple engines |

## Test Coverage

| Component | Coverage |
|-----------|----------|
| Backend engines | ~40% (minimal unit tests) |
| API endpoints | ~10% (no integration tests) |
| Frontend | ~5% (E2E only) |
| Database layer | ~0% (no tests) |

## Linting Rules

### Frontend
- ESLint: Configured (`eslint.config.mjs`)
- TypeScript: Strict mode enabled

### Backend
- Pyright: Configured (`pyrightconfig.json`)
- No flake8/black configuration

## Formatting Rules

NOT ENFORCED - No pre-commit hooks, no CI checks.

## Technical Debt Areas

| Priority | Issue |
|----------|-------|
| High | O(n²) reconciliation matching |
| High | No pagination on large queries |
| Medium | Inline SQL (no ORM) |
| Medium | No automated testing in CI |
| Low | Duplicate date parsing logic |

## Refactor Candidates

| Candidate | Reason |
|-----------|--------|
| Extract service layer | API too coupled to DB |
| Add repository pattern | Better testability |
| Implement pagination | Handle large datasets |
| Add async job queue | PDF processing blocks |
| Consolidate date parsing | Single utility function |

---

# 1️⃣5️⃣ FULL ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  Browser (Chrome, Firefox, Safari, Mobile)                               │   │
│  │  • User interactions                                                     │   │
│  │  • LocalStorage (theme, dashboard mode)                                  │   │
│  └─────────────────────────────────┬───────────────────────────────────────┘   │
└────────────────────────────────────┼────────────────────────────────────────────┘
                                     │ HTTP/REST (CORS: localhost:3000, 3001)
┌────────────────────────────────────┼────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                       │
│  ┌─────────────────────────────────▼─────────────────────────────────────────┐  │
│  │  Next.js 16 Application (Port 3000)                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │  App Router (app/)                                                   │  │  │
│  │  │  • dashboard/page.tsx    • transactions/page.tsx                     │  │  │
│  │  │  • analytics/page.tsx    • cards/page.tsx                            │  │  │
│  │  │  • categories/page.tsx   • import/page.tsx                           │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │  React Components (components/)                                      │  │  │
│  │  │  • dashboard/ModeToggle.tsx                                          │  │  │
│  │  │  • dashboard/PersonalDashboard.tsx                                   │  │  │
│  │  │  • dashboard/FamilyDashboard.tsx                                     │  │  │
│  │  │  • ui/* (shadcn/ui components)                                       │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │  State Management                                                    │  │  │
│  │  │  • Zustand (lib/store/)                                              │  │  │
│  │  │  • React Query (server state)                                        │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │  API Client (lib/api/client.ts)                                      │  │  │
│  │  │  • fetchOverview()     • fetchTransactions()                         │  │  │
│  │  │  • uploadStatement()   • fetchBehaviorSummary()                      │  │  │
│  │  │  • createAccount()     • createCard()                                │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────────┘
                                     │ HTTP/REST (JSON)
┌────────────────────────────────────┼────────────────────────────────────────────┐
│                          API LAYER (FastAPI)                                     │
│  ┌─────────────────────────────────▼─────────────────────────────────────────┐  │
│  │  FastAPI Application (Port 8000)                                           │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │  CORS Middleware (api.py:85-92)                                      │  │  │
│  │  │  allow_origins=["http://localhost:3000", "http://localhost:3001"]    │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │  API Routers (api.py)                                                │  │  │
│  │  │  ┌─────────────────┐ ┌─────────────────┐ ┌────────────────────────┐ │  │  │
│  │  │  │ Dashboard       │ │ Data Management │ │ Behavioral Intelligence│ │  │  │
│  │  │  │ • /overview     │ │ • /transactions │ │ • /behavior/summary    │ │  │  │
│  │  │  │ • /categories   │ │ • /statements   │ │ • /behavior/score      │ │  │  │
│  │  │  │ • /analytics    │ │ • /members      │ │ • /behavior/insights   │ │  │  │
│  │  │  └─────────────────┘ └─────────────────┘ └────────────────────────┘ │  │  │
│  │  │  ┌─────────────────┐ ┌─────────────────┐ ┌────────────────────────┐ │  │  │
│  │  │  │ Account         │ │ Reconciliation  │ │ Audit                  │ │  │  │
│  │  │  │ • /accounts/*   │ │ • /reconciliations    │ │ • /audit/report        │ │  │  │
│  │  │  │ • /cards/*      │ │ • /reconciliations/scan│ │                        │ │  │  │
│  │  │  └─────────────────┘ └─────────────────┘ └────────────────────────┘ │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │  Pydantic Models (api.py)                                            │  │  │
│  │  │  • CategoryUpdate, BulkCategoryUpdate                                │  │  │
│  │  │  • AccountCreate, AccountUpdate                                      │  │  │
│  │  │  • CardCreate, CardUpdate                                            │  │  │
│  │  │  • MemberCreate                                                      │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────────┘
                                     │ Python function calls
┌────────────────────────────────────┼────────────────────────────────────────────┐
│                         SERVICE LAYER (Engines)                                  │
│  ┌─────────────────────────────────▼─────────────────────────────────────────┐  │
│  │  Deterministic Computation Engines                                         │  │
│  │                                                                             │  │
│  │  ┌──────────────────────────┐  ┌────────────────────────────────────────┐ │  │
│  │  │ BalanceEngine            │  │ BehaviorEngine                         │ │  │
│  │  │ (balance_engine.py)      │  │ (behavior_engine.py)                   │ │  │
│  │  │                          │  │                                        │ │  │
│  │  │ • compute_running_       │  │ • compute_behavior_profile()           │ │  │
│  │  │   balance()              │  │ • _compute_loss_aversion_index()       │ │  │
│  │  │ • compute_account_       │  │ • _compute_impulsivity_score()         │ │  │
│  │  │   balance()              │  │ • _compute_habit_stability_score()     │ │  │
│  │  │ • validate_statement_    │  │ • _compute_financial_stress_index()    │ │  │
│  │  │   balance()              │  │ • _compute_savings_discipline_score()  │ │  │
│  │  │ • get_accounts_list()    │  │ • detect_india_risk_patterns()         │ │  │
│  │  └──────────────────────────┘  └────────────────────────────────────────┘ │  │
│  │                                                                             │  │
│  │  ┌──────────────────────────┐  ┌────────────────────────────────────────┐ │  │
│  │  │ ReconciliationEngine     │  │ LedgerAuditEngine                      │ │  │
│  │  │ (reconciliation_engine   │  │ (ledger_audit_engine.py)               │ │  │
│  │  │  .py)                    │  │                                        │ │  │
│  │  │                          │  │ • validate_ledger_integrity()          │ │  │
│  │  │ • find_potential_        │  │ • verify_hash_signatures()             │ │  │
│  │  │   matches()              │  │ • run_full_audit()                     │ │  │
│  │  │ • _calculate_confidence()│  │   Checks: account_id NOT NULL          │ │  │
│  │  │ • _check_match()         │  │           debit >= 0                   │ │  │
│  │  │ • O(n²) matching algo    │  │           hash_signature unique        │ │  │
│  │  └──────────────────────────┘  └────────────────────────────────────────┘ │  │
│  │                                                                             │  │
│  │  ┌──────────────────────────┐  ┌────────────────────────────────────────┐ │  │
│  │  │ InsightGenerator         │  │ NudgeEngine                            │ │  │
│  │  │ (insight_generator.py)   │  │ (nudge_engine.py)                      │ │  │
│  │  │                          │  │                                        │ │  │
│  │  │ • generate_behavioral_   │  │ • generate_nudges()                    │ │  │
│  │  │   insights()             │  │ • get_top_nudge()                      │ │  │
│  │  │ • generate_summary_text()│  │ • get_nudge_summary()                  │ │  │
│  │  └──────────────────────────┘  └────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────────┘
                                     │ Python function calls
┌────────────────────────────────────┼────────────────────────────────────────────┐
│                        PDF PROCESSING PIPELINE                                   │
│  ┌─────────────────────────────────▼─────────────────────────────────────────┐  │
│  │  Statement Extraction                                                      │  │
│  │  ┌──────────────┐ → ┌──────────────┐ → ┌──────────────┐ → ┌──────────┐   │  │
│  │  │ Table        │   │ Column       │   │ Transaction  │   │ Categorizer│   │  │
│  │  │ Extractor    │   │ Mapper       │   │ Parser       │   │            │   │  │
│  │  │              │   │              │   │              │   │            │   │  │
│  │  │ camelot-py   │   │ map_columns()│   │ parse_       │   │ categorize()│  │  │
│  │  │ pdfplumber   │   │ has_required │   │ dataframe()  │   │ keyword    │   │  │
│  │  │              │   │ _fields()    │   │              │   │ matching   │   │  │
│  │  └──────────────┘   └──────────────┘   └──────────────┘   └──────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────────┘
                                     │ SQL (sqlite3)
┌────────────────────────────────────┼────────────────────────────────────────────┐
│                          DATA LAYER                                              │
│  ┌─────────────────────────────────▼─────────────────────────────────────────┐  │
│  │  SQLite Database (backend/data/finance.db)                                 │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │  Core Tables                                                         │  │  │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │  │  │
│  │  │  │ statements  │ │ transactions│ │reconciliations│ │   accounts  │   │  │  │
│  │  │  │             │ │ (IMMUTABLE) │ │             │ │             │   │  │  │
│  │  │  │ • bank      │ │ • hash_sig  │ │ • match_conf│ │ • balance_  │   │  │  │
│  │  │  │ • file_name │ │ • date_iso  │ │ • status    │ │   paise     │   │  │  │
│  │  │  │ • period    │ │ • debit     │ │ • deterministic_key │       │   │  │  │
│  │  │  │ • metadata  │ │ • credit    │ │             │ │ • is_active │   │  │  │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │  │  │
│  │  │  ┌─────────────┐ ┌─────────────┐                                     │  │  │
│  │  │  │    cards    │ │   members   │                                     │  │  │
│  │  │  │             │ │             │                                     │  │  │
│  │  │  │ • card_type │ │ • name      │                                     │  │  │
│  │  │  │ • last_four │ │ • color     │                                     │  │  │
│  │  │  │ • credit_   │ │             │                                     │  │  │
│  │  │  │   limit_paise│ │             │                                     │  │  │
│  │  │  └─────────────┘ └─────────────┘                                     │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │  Integrity Mechanisms                                                │  │  │
│  │  │  • PRAGMA journal_mode=WAL                                           │  │  │
│  │  │  • UNIQUE INDEX on hash_signature                                    │  │  │
│  │  │  • TRIGGER prevent_transaction_update (blocks UPDATE)                │  │  │
│  │  │  • TRIGGER prevent_transaction_delete (blocks DELETE)                │  │  │
│  │  │  • INTEGER paise amounts (no floating point)                         │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

# 1️⃣6️⃣ KNOWN LIMITATIONS & FAILURE MODES

## Known Unstable Modules

| Module | Issue | Trigger |
|--------|-------|---------|
| ReconciliationEngine | O(n²) algorithm | >1000 transactions |
| PDF Extraction | camelot-py failures | Corrupted PDFs, scanned images |
| Date Parser | Multiple format ambiguity | Unusual date formats |
| Balance Replay | Performance degradation | >10,000 transactions |

## Performance Degradation Scenarios

| Scenario | Symptom | Root Cause |
|----------|---------|------------|
| Large PDF upload | Timeout | Entire file loaded into memory |
| Many transactions | Slow API response | No pagination, loads all rows |
| Cross-account matching | Hanging | O(n²) nested loops |
| Dashboard load | Slow | Multiple sequential API calls |

## Edge Cases Not Handled

| Edge Case | Current Behavior |
|-----------|------------------|
| Duplicate hash_signature | INSERT OR IGNORE (silent skip) |
| Invalid date format | Empty date_iso, may break sorting |
| Negative amounts | Stored as-is, may break calculations |
| Concurrent uploads | SQLite locking may fail |
| Network interruption | No retry, operation fails |

## Resource Leaks

| Resource | Leak Risk | Location |
|----------|-----------|----------|
| Database connections | MEDIUM | No connection pooling |
| File handles | LOW | Context managers used |
| Memory (PDF processing) | HIGH | Entire PDF in memory |

## Memory Growth Risks

| Scenario | Risk | Mitigation |
|----------|------|------------|
| Large transaction queries | Loads all rows | None (no streaming) |
| PDF processing | Full file in memory | None |
| Long-running sessions | Context growth | Context window limit |

## Deadlock Risks

NOT IDENTIFIED - Single-threaded design avoids deadlocks.

## Failure Cascades

| Initial Failure | Cascade Effect |
|-----------------|----------------|
| SQLite corruption | All data operations fail |
| Disk full | Uploads fail, no cleanup |
| Backend crash | Frontend shows errors |
| PDF extraction failure | Upload appears successful but no transactions |

## Data Corruption Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Hash collision | VERY LOW | SHA256 |
| Silent duplicate skip | MEDIUM | INSERT OR IGNORE |
| Partial upload | MEDIUM | No transaction rollback |
| Concurrent modification | LOW | SQLite WAL mode |

## Unhandled Exceptions

| Exception Type | Handling |
|----------------|----------|
| Database locked | May propagate to user |
| File not found | May propagate to user |
| Network error | May propagate to user |
| Memory error | Process crash |

---

# 1️⃣7️⃣ TOP 20 STRUCTURAL RISKS

| Rank | Risk | Severity | Impact | Mitigation Priority |
|------|------|----------|--------|---------------------|
| 1 | **NO AUTHENTICATION** | 🔴 CRITICAL | Anyone can access/modify data | Implement JWT/OAuth |
| 2 | **SQLite Single-Instance** | 🔴 CRITICAL | No horizontal scaling | Migrate to PostgreSQL |
| 3 | **O(n²) Reconciliation** | 🔴 CRITICAL | Quadratic slowdown | Optimize algorithm |
| 4 | **No Input Validation** | 🔴 CRITICAL | SQL injection, XSS risk | Add Pydantic validators |
| 5 | **No Rate Limiting** | 🔴 CRITICAL | DoS vulnerability | Add rate limit middleware |
| 6 | **No Backup System** | 🟡 HIGH | Data loss risk | Automated backups |
| 7 | **No Pagination** | 🟡 HIGH | Memory exhaustion | Cursor-based pagination |
| 8 | **Large File Handling** | 🟡 HIGH | Memory crashes | Streaming uploads |
| 9 | **No Error Tracking** | 🟡 HIGH | Silent failures | Add Sentry/error logging |
| 10 | **No Health Checks** | 🟡 HIGH | Undetected downtime | Health endpoint + monitoring |
| 11 | **No CI/CD** | 🟡 HIGH | Manual deployment errors | GitHub Actions |
| 12 | **Tight Coupling** | 🟡 HIGH | Testing difficulty | Repository pattern |
| 13 | **God Functions** | 🟡 HIGH | Maintenance burden | Extract services |
| 14 | **No Automated Tests** | 🟡 HIGH | Regression risk | Increase coverage |
| 15 | **No Secret Management** | 🟡 HIGH | Credential exposure | Vault/secrets manager |
| 16 | **No Audit Logging** | 🟠 MEDIUM | No change tracking | Audit table |
| 17 | **Duplicate Logic** | 🟠 MEDIUM | Maintenance burden | Consolidate utilities |
| 18 | **No API Versioning** | 🟠 MEDIUM | Breaking changes | /api/v1/ prefix |
| 19 | **No Documentation** | 🟠 MEDIUM | Onboarding friction | OpenAPI spec |
| 20 | **No Containerization** | 🟢 LOW | Environment inconsistency | Docker |

---

# END OF PROJECT AUDIT REPORT

## Document Statistics

| Metric | Value |
|--------|-------|
| Total Lines of Code (Backend) | ~8,000 Python |
| Total Lines of Code (Frontend) | ~15,000 TypeScript |
| Database Tables | 7 |
| API Endpoints | 30+ |
| Test Files | 12 Playwright specs |
| Engine Modules | 6 |
| Configuration Files | 10+ |

## Critical Architectural Decisions

1. **Immutable Ledger**: Transactions cannot be updated/deleted (triggers block)
2. **Deterministic Computation**: All financial calculations are pure functions
3. **Integer Paise**: All monetary values stored as integers (no floating point)
4. **Hash Deduplication**: SHA256 signatures prevent duplicate transactions
5. **Local-First**: SQLite for simplicity, single-instance deployment

## Summary

ClariFin_OS is a **modular monolith** personal finance application with:
- Clean separation between frontend (Next.js) and backend (FastAPI)
- Deterministic financial computation engines
- Immutable ledger design with strong data integrity
- Local SQLite storage for simplicity
- **Major gaps**: No auth, no scaling, minimal testing, no CI/CD

END OF PROJECT AUDIT REPORT
