# Technical Context

## Technologies Used

### Core Stack
- **Next.js 16.1.6** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **PDF.js** - PDF parsing with text extraction
- **FastAPI** - REST API framework
- **SQLite** - Database

### Deprecated
- **Reflex** - Archived to `backend/_archived_reflex_dashboard/`

---

## Parser Architecture

### Spatial Text Extraction
```typescript
// frontend/lib/parser/core/text-extractor.ts
export interface TextItem {
    text: string;
    x: number;           // X coordinate from PDF.js transform
    y: number;           // Y coordinate (flipped for top-down)
    width: number;
    height: number;
    fontSize: number;
    fontName: string;
}
```

**Key Implementation Details:**
- PDF.js loaded dynamically to avoid SSR issues
- Y coordinate flipped (PDF origin is bottom-left, we use top-down)
- Items grouped into lines using Y position tolerance (5px)
- Lines sorted by Y position for top-to-bottom reading

---

## FastAPI REST API

### Architecture
```python
# backend/src/api.py
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Personal Finance API", version="1.0.0")
```

### Endpoints

#### Dashboard Endpoints
- `GET /api/transactions` - List transactions with filters
- `GET /api/overview` - Overview metrics and charts
- `GET /api/categories` - Category summary and breakdown
- `GET /api/analytics` - Analytics data
- `GET /api/statements` - List statements with metadata

#### Data Endpoints
- `GET /api/banks` - List banks
- `GET /api/categories/list` - List categories
- `GET /api/members` - List members

#### Action Endpoints
- `POST /api/upload` - Upload PDF statement
- `POST /api/import/detect` - Detect CSV/Excel format
- `POST /api/import/execute` - Execute CSV/Excel import
- `POST /api/members` - Add new member
- `GET /api/export/csv` - Export transactions to CSV

#### Balance Endpoints (Phase 2A)
- `GET /api/accounts` - List all accounts with balances
- `GET /api/accounts/{id}/balance` - Single account balance
- `GET /api/accounts/{id}/running-balance` - Running balance history
- `GET /api/statements/{id}/validate` - Validate statement balance

#### Removed Endpoints (Phase 2A.1 - Ledger Immutability)
- ~~`PUT /api/transactions/{id}/category`~~ - REMOVED
- ~~`PUT /api/transactions/bulk-category`~~ - REMOVED
- ~~`DELETE /api/statements/{id}`~~ - REMOVED

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## File Structure

```
ClariFin_OS/
├── frontend/                    # Next.js application
│   ├── app/                     # Pages
│   ├── components/              # React components
│   ├── lib/                     # API client, hooks, parser
│   │   ├── parser/              # PDF parsing
│   │   ├── api/                 # API client
│   │   └── hooks/               # React hooks
│   └── types/                   # TypeScript types
├── backend/                     # FastAPI + SQLite
│   ├── src/                     # API code
│   │   ├── api.py               # FastAPI endpoints
│   │   ├── db.py                # Database operations
│   │   ├── categorizer.py       # Transaction categorization
│   │   └── ...                  # Other modules
│   ├── data/                    # Database + uploads
│   │   ├── finance.db           # SQLite database
│   │   └── uploads/             # Uploaded statements
│   └── _archived_reflex_dashboard/
├── data/                        # Root data
│   └── test/                    # Test files
├── memory-bank/                 # Cline context
├── servers/                     # MCP servers
└── scripts/                     # Utility scripts
```

---

## Dependencies

### Production (Frontend)
- `pdfjs-dist` - PDF parsing
- `react-dropzone` - File upload
- `lucide-react` - Icons
- `recharts` - Charts
- `chart.js` - Charts
- `zustand` - State management

### Production (Backend)
- `fastapi` - REST API framework
- `uvicorn` - ASGI server
- `python-multipart` - File upload handling
- `pandas` - CSV/Excel processing
- `openpyxl` - Excel file support
- `pdfplumber` - PDF extraction

---

## Build Configuration

### next.config.ts
- Turbopack enabled
- Worker root configuration

### TypeScript
- Strict mode enabled
- Path aliases configured (@/lib, @/components, etc.)
- No implicit any

---

## How to Run

**Frontend:**
```bash
cd frontend && npm run dev
```

**Backend:**
```bash
cd backend && uvicorn src.api:app --reload --port 8000
```

---

## Architectural Decisions

### 1. Single Source of Truth
The FastAPI backend (SQLite-backed) is the single source of truth for all financial data.

### 2. Transaction Type Authority
`frontend/types/transaction.ts` is the only valid Transaction definition.

### 3. Monetary Representation Policy (Phase 2)
All monetary values will migrate to integer paise representation.

---

## Known Limitations

1. **Table Detection:** May fail if table structure is unusual
2. **Proximity Matching:** Depends on consistent PDF layouts
3. **Bank Support:** Limited to 6 major banks (expandable)
4. **Date Formats:** Handles common formats but may miss edge cases

## Future Enhancements

1. Add more bank patterns
2. Implement machine learning for table detection
3. Support for debit card statements
4. Multi-currency support
5. Add authentication to API