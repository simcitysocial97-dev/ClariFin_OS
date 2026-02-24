# ClariFin OS

Personal Finance Tracker - A clean, modern system for tracking and analyzing personal finances.

## Architecture

```
ClariFin_OS/
├── frontend/          # Next.js application
├── backend/           # FastAPI + SQLite
│   ├── src/           # API and database code
│   └── data/          # SQLite database + uploaded statements
├── memory-bank/       # Project documentation (Cline)
├── servers/           # MCP servers (AI tooling)
└── scripts/           # Utility scripts
```

## Tech Stack

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS, Chart.js
- **Backend**: FastAPI, Python 3.x
- **Database**: SQLite

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- pip or uv

### Run Backend

```bash
cd backend

# Create virtual environment (if not exists)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy pdfplumber

# Run the API server
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

API will be available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### Run Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Features

- 📊 **Dashboard**: Overview of spending, income, and trends
- 💳 **Cards**: Manage multiple bank accounts and cards
- 📁 **Categories**: Transaction categorization with drill-down
- 📈 **Analytics**: Spending patterns, merchant analysis, recurring charges
- 📤 **Import**: Upload PDF statements or CSV files
- ⚙️ **Settings**: Configure members, categories, and preferences

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/transactions` | Get transactions with filters |
| `GET /api/overview` | Dashboard metrics |
| `GET /api/categories` | Category breakdown |
| `GET /api/analytics` | Analytics data |
| `GET /api/statements` | List all statements |
| `POST /api/upload` | Upload PDF statement |
| `PUT /api/transactions/{id}/category` | Update category |

## Database

SQLite database located at `backend/data/finance.db`

### Key Tables

- `statements` - Uploaded bank statements
- `transactions` - Individual transactions
- `members` - Family members for expense tracking

## Development

### Build Frontend

```bash
cd frontend
npm run build
```

### Run Tests

```bash
cd frontend
npm run test
```

## Project Structure

### Frontend (`frontend/`)

```
frontend/
├── app/               # Next.js app router pages
├── components/        # React components
├── lib/               # Utilities, API client, hooks
├── types/             # TypeScript types
└── public/            # Static assets
```

### Backend (`backend/`)

```
backend/
├── src/
│   ├── api.py         # FastAPI endpoints
│   ├── db.py          # Database operations
│   ├── categorizer.py # Transaction categorization
│   └── ...            # Other modules
└── data/
    ├── finance.db     # SQLite database
    └── uploads/       # Uploaded PDF files
```

## License

MIT