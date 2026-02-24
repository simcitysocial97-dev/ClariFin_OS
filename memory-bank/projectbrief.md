# ClariFin_OS - Project Brief

## Overview
A personal finance tracking system with Next.js frontend and FastAPI backend for parsing bank statement PDFs and visualizing transaction data with automatic categorization.

## Core Requirements
1. **PDF Parsing**: Parse credit card statements from multiple Indian banks (HDFC, ICICI, SBI, Axis, IDFC, IndusInd)
2. **Transaction Extraction**: Extract date, description, amount, and type (debit/credit)
3. **Auto-Categorization**: Categorize transactions (Food, Shopping, Transport, Bills, etc.)
4. **Dashboard**: Visualize spending with charts and statistics
5. **Data Management**: Export/import data, persistent storage

## Tech Stack
- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, Python 3.x
- **Database**: SQLite
- **Charts**: Recharts, Chart.js
- **PDF**: pdfjs-dist, pdfplumber
- **State**: Zustand

## Project Structure
```
ClariFin_OS/
├── frontend/              # Next.js application
│   ├── app/               # Pages (dashboard, transactions, analytics, etc.)
│   ├── components/        # React components
│   ├── lib/               # API client, hooks, parser
│   └── types/             # TypeScript types
├── backend/               # FastAPI + SQLite
│   ├── src/               # API code
│   ├── data/              # Database + uploads
│   └── _archived_reflex_dashboard/
├── data/                  # Root data
│   └── test/              # Test files
├── memory-bank/           # Cline context
├── servers/               # MCP servers
└── scripts/               # Utility scripts
```

## Key Features
- Drag & drop PDF upload
- Real-time parsing with progress indicator
- Dark/light theme toggle
- Responsive sidebar navigation
- Transaction filtering and search
- CSV export
- Multi-card support
- REST API for data access

## Status
✅ Core functionality complete
✅ Build successful
✅ Architectural cleanup complete (22/02/2026)
✅ Reflex deprecated and archived

## Deprecated
- **Reflex Dashboard**: Moved to `backend/_archived_reflex_dashboard/`