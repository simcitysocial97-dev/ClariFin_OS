# V2 API Contract Facts

> **Purpose:** Reference document for frontend integration with the V2 staging-based import pipeline (B1–B5).
> **Last Updated:** 2026-01-03

---

## Overview

The V2 API introduces a staging-based PDF import pipeline with validation before commit to the immutable ledger. It consists of three main router modules:

- **Jobs Router** (`/api/jobs/*`) - Async job queue management
- **Imports Router** (`/api/imports/*`) - Staged PDF import pipeline
- **Quarantine Router** (`/api/quarantine/*`) - Failed validation remediation

---

## Jobs Endpoints

> **File:** `backend/src/routers/jobs.py`

### Create Job

```
POST /api/jobs
```

Creates a new background job for async processing.

**Request Body (JSON):**

```typescript
interface JobCreateRequest {
  job_type: string;        // minLength: 1, maxLength: 100
  payload?: object;        // Job-specific data
  total_items: number;     // >= 0, for progress tracking
}
```

**Response (200 OK):**

```typescript
interface JobCreateResponse {
  job_id: string;          // UUID for tracking
}
```

### Get Job Status

```
GET /api/jobs/{job_id}
```

Retrieves job status and progress information.

**Response (200 OK):**

```typescript
interface JobResponse {
  id: string;
  job_type: string;
  status: string;          // PENDING | CLAIMED | COMPLETED | FAILED
  payload: object;
  total_items: number;
  processed_items: number;
  progress_pct: number;    // 0.0 - 100.0
  created_at: string;      // ISO timestamp
  started_at?: string;     // ISO timestamp
  finished_at?: string;    // ISO timestamp
  error?: string;
  worker_id?: string;
}
```

**Error Response (404):**

```typescript
{ error: "Job not found" }
```

---

## Imports Endpoints

> **File:** `backend/src/routers/imports.py`

### Upload PDF (Multipart)

```
POST /api/imports/pdf
```

Upload and process a PDF bank statement with staging. Extracts transactions, stages them, validates balances, and optionally commits to ledger.

**Request Body (multipart/form-data):**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | File | Yes | - | PDF file to upload (max 50MB) |
| `member` | string | No | "Self" | Member name for transactions |
| `auto_commit` | boolean | No | true | Auto-commit if validation passes |

**Response (200 OK):**

```typescript
interface ImportPdfResponse {
  success: boolean;
  statement_id: string;           // UUID for this import
  status: "STAGED" | "NEEDS_REVIEW" | "COMMITTED" | "FAILED";
  delta_paise: number;            // Balance discrepancy (0 = balanced)
  transaction_count: number;
  bank: string;
  filename: string;
  extractor: "legacy" | "docling";
  validation: {
    valid: boolean;
    reason?: string;
    opening_balance_paise?: number;
    closing_balance_paise?: number;
  };
  committed?: {                   // Only if status === "COMMITTED"
    inserted: number;
    skipped: number;
  };
  error?: string;                 // Only if status === "FAILED"
}
```

**Error Responses:**
- `400` - Invalid file (not PDF, exceeds 50MB, no filename)
- `422` - PDF extraction failed
- `500` - Import processing failed

### List Imports

```
GET /api/imports?status={status}&page={page}&per_page={per_page}
```

List staged imports with pagination.

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `status` | string | No | - | Filter: "STAGED", "NEEDS_REVIEW", "COMMITTED", "FAILED" |
| `page` | int | No | 1 | Page number (1-indexed) |
| `per_page` | int | No | 50 | Items per page |

**Response (200 OK):**

```typescript
interface ImportListResponse {
  items: ImportItem[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
}

interface ImportItem {
  id: string;
  status: string;
  source_filename: string;
  bank: string;
  delta_paise: number | null;
  opening_balance_paise: number | null;
  closing_balance_paise: number | null;
  transaction_count: number;
  created_at: string;
  committed_at: string | null;
  error: string | null;
}
```

### Get Import Status

```
GET /api/imports/{statement_id}
```

Get detailed status of a specific staged import.

**Response (200 OK):**

```typescript
interface ImportStatusResponse {
  id: string;
  status: "STAGED" | "NEEDS_REVIEW" | "COMMITTED" | "FAILED";
  source_filename: string;
  bank: string;
  delta_paise: number | null;
  opening_balance_paise: number | null;
  closing_balance_paise: number | null;
  transaction_count: number;
  created_at: string;
  committed_at: string | null;
  error: string | null;
}
```

**Error Response (404):**

```typescript
{ detail: "Import not found" }
```

### Commit Staged Import

```
POST /api/imports/{statement_id}/commit
```

Manually commit a staged import to the immutable ledger (if validation passes).

**Request Body (multipart/form-data):**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `member` | string | No | "Self" | Member name for transactions |

**Response (200 OK):**

```typescript
interface CommitResponse {
  success: boolean;
  inserted: number;        // Transactions inserted to ledger
  skipped: number;         // Duplicates skipped
  error: string | null;
}
```

**Error Response (404):**

```typescript
{ detail: "Import not found" }
```

**Error Response (400):**

```typescript
{ detail: "Import already committed" }
```

### Discard Staged Import

```
POST /api/imports/{statement_id}/discard
```

Discard a staged import. Deletes staging records (not the PDF file).

**Response (200 OK):**

```typescript
interface DiscardResponse {
  success: boolean;
}
```

**Error Responses:**
- `404` - Import not found
- `400` - Cannot discard committed import

### Revalidate Import

```
POST /api/imports/{statement_id}/revalidate
```

Revalidate a statement by rebuilding staged transactions from corrected extraction data (from resolved quarantine pages). If delta becomes 0, automatically commits to ledger.

**Request Body (multipart/form-data):**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `member` | string | No | "Self" | Member name for transactions |

**Response (200 OK):**

```typescript
interface RevalidateResponse {
  success: boolean;
  delta_paise: number;     // New computed delta
  valid: boolean;          // Whether validation passed
  committed: boolean;      // Whether transactions were committed
  inserted: number;        // Number of transactions inserted
  skipped: number;         // Number of duplicates skipped
  error: string | null;
}
```

**Error Response (404):**

```typescript
{ detail: "Import not found" }
```

---

## Quarantine Endpoints

> **File:** `backend/src/routers/quarantine.py`

Quarantine pages are created when a statement fails validation (delta != 0). Each page can be individually corrected and resolved.

### List Quarantine Pages

```
GET /api/quarantine/pages?status={status}&page={page}&per_page={per_page}
```

List quarantine pages with optional status filter.

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `status` | string | No | "QUARANTINED" | Filter: "QUARANTINED", "RESOLVED", or omit for all |
| `page` | int | No | 1 | Page number (1-indexed) |
| `per_page` | int | No | 50 | Items per page |

**Response (200 OK):**

```typescript
interface QuarantineListResponse {
  items: QuarantinePage[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
}

interface QuarantinePage {
  id: string;                    // quarantine_page_id (UUID)
  statement_id: string;          // Links to import
  page_number: number;
  reason: string | null;         // Why it was quarantined
  delta_paise: number | null;
  status: "QUARANTINED" | "RESOLVED";
  created_at: string;
  resolved_at: string | null;
  resolution_notes: string | null;
  source_filename: string | null;
  bank: string | null;
}
```

**Error Response (400):**

```typescript
{ detail: "Status must be 'QUARANTINED' or 'RESOLVED'" }
```

### Get Quarantine Page Details

```
GET /api/quarantine/pages/{quarantine_id}
```

Get full details including raw and corrected extraction JSON.

**Response (200 OK):**

```typescript
interface QuarantinePageDetail extends QuarantinePage {
  raw_extraction_json: string | null;        // Original extraction
  corrected_extraction_json: string | null;  // User corrections
}
```

**Extraction JSON Structure:**

```typescript
interface ExtractionJson {
  transactions: {
    date: string;
    date_iso: string | null;
    description: string;
    debit_paise: number;
    credit_paise: number;
    balance_paise: number | null;
    raw_row_json: string | null;
  }[];
  page_number: number;
  statement_id: string;
}
```

**Error Response (404):**

```typescript
{ detail: "Quarantine page {id} not found" }
```

### Resolve Quarantine Page

```
PATCH /api/quarantine/pages/{quarantine_id}
```

Resolve a quarantine page with corrected extraction data. Marks as RESOLVED and stores corrected JSON for revalidation.

**Request Body (JSON):**

```typescript
interface ResolveQuarantineRequest {
  corrected_extraction_json: string;  // JSON string of corrected extraction
  resolution_notes?: string;          // Optional notes
}
```

**Response (200 OK):**

```typescript
interface ResolveQuarantineResponse {
  success: boolean;
  id: string;
  status: "RESOLVED";
  message: "Quarantine page resolved successfully. Run revalidation to commit.";
}
```

**Error Responses:**
- `404` - Quarantine page not found
- `400` - Quarantine page already resolved (or other status)
- `500` - Failed to resolve quarantine page

---

## Environment Flags

The following environment variables control V2 API behavior:

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `CLARIFIN_ENABLE_WORKER` | `"1"` or unset | unset | Enable background job worker thread for async job processing |
| `CLARIFIN_EXTRACTOR` | `"legacy"`, `"docling"` | `"legacy"` | PDF extraction engine: legacy (Camelot) or docling (AI-powered) |
| `CLARIFIN_ENABLE_AUTO_HEAL` | `"1"` or unset | unset | Enable conservative auto-heal engine for failed validations |

### Flag Details

**CLARIFIN_ENABLE_WORKER**
- Set to `"1"` to enable the background job worker
- Worker polls DB for PENDING jobs every 5 seconds
- Single worker instance (no concurrency by default)
- Configurable worker ID via `CLARIFIN_WORKER_ID` (default: "worker-1")

**CLARIFIN_EXTRACTOR**
- `"legacy"`: Proven Camelot-based extraction pipeline (always available)
- `"docling"`: AI-powered Docling extraction (requires `pip install 'docling>=2.0.0'`)
- Falls back to legacy if docling not installed

**CLARIFIN_ENABLE_AUTO_HEAL**
- Set to `"1"` to enable auto-heal on validation failure
- Runs before quarantining: sign flip detection, numeral scrubbing, multiline merge
- Only applies fix if delta becomes exactly 0
- All changes recorded in `auto_heal_events` table for audit

---

## Frontend Integration Notes

### Polling Requirements

| Endpoint | Polling? | Notes |
|----------|----------|-------|
| `GET /api/jobs/{job_id}` | **Yes** | Poll every 2-5 seconds for async job status; stop when status is COMPLETED or FAILED |
| `GET /api/imports/{statement_id}` | Optional | Poll if waiting for auto-commit result; otherwise single check |
| `GET /api/quarantine/pages` | Optional | Refresh when user navigates to quarantine view |

### Authoritative Response Fields

| Field | Source Endpoint | Meaning |
|-------|-----------------|---------|
| `delta_paise` | `POST /api/imports/pdf`, `GET /api/imports/{id}` | **Authoritative** balance discrepancy. `0` = perfectly balanced. Non-zero = needs review/quarantine. |
| `status` | All import endpoints | **Authoritative** import state. Flow: `STAGED` → (`COMMITTED` or `NEEDS_REVIEW` or `FAILED`) |
| `validation.valid` | `POST /api/imports/pdf` | Whether validation passed at upload time. Use `delta_paise` for definitive check. |
| `committed` | `POST /api/imports/{id}/revalidate` | Whether revalidation resulted in commit. Check `success` and `delta_paise` together. |

### ID Reference Guide

| ID Type | Format | Created By | Used For | Example |
|---------|--------|------------|----------|---------|
| `job_id` | UUID v4 | `POST /api/jobs` | Tracking async job progress | `"550e8400-e29b-41d4-a716-446655440000"` |
| `statement_id` | UUID v4 | `POST /api/imports/pdf` | All import operations (also called `import_id` in code) | `"6ba7b810-9dad-11d1-80b4-00c04fd430c8"` |
| `quarantine_id` | UUID v4 | Validation engine (auto-created) | Quarantine resolution operations | `"6ba7b811-9dad-11d1-80b4-00c04fd430c8"` |

### Typical Flows

#### 1. Upload with Auto-Commit (Happy Path)
```
POST /api/imports/pdf (auto_commit=true)
  ↓
Response: status="COMMITTED", delta_paise=0
  ↓
Done! Transactions in ledger.
```

#### 2. Upload with Validation Failure (Quarantine Path)
```
POST /api/imports/pdf (auto_commit=true)
  ↓
Response: status="NEEDS_REVIEW", delta_paise=1500
  ↓
GET /api/quarantine/pages?status=QUARANTINED
  ↓
For each page: GET /api/quarantine/pages/{id} → review extraction
  ↓
PATCH /api/quarantine/pages/{id} (with corrected_extraction_json)
  ↓
POST /api/imports/{statement_id}/revalidate
  ↓
Response: committed=true, delta_paise=0
  ↓
Done! Transactions committed after corrections.
```

#### 3. Manual Commit Flow
```
POST /api/imports/pdf (auto_commit=false)
  ↓
Response: status="STAGED", validation.valid=true
  ↓
(User reviews in UI)
  ↓
POST /api/imports/{statement_id}/commit
  ↓
Response: success=true, inserted=42
  ↓
Done!
```

---

## Router Registration

Routers are registered in `backend/src/api.py`:

```python
from src.routers import jobs, imports, quarantine

app.include_router(jobs.router)
app.include_router(imports.router)
app.include_router(quarantine.router)
```

Base path for all endpoints: `http://localhost:8000` (or configured host)

CORS enabled for: `http://localhost:3000`, `http://localhost:3001`

---

## See Also

- `backend/BACKEND_STABILIZATION_FACTS.md` - Backend architecture and stabilization notes
- `backend/src/engines/statement_validator.py` - Validation logic details
- `backend/src/engines/auto_heal_engine.py` - Auto-heal cycle documentation
