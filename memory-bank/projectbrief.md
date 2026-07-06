# ClariFin_OS — Project Brief

## Overview

ClariFin_OS is a Personal Financial Operating System. It parses bank statement PDFs from multiple Indian banks, extracts and categorizes transactions, and provides a unified dashboard for financial analysis.

The system is designed around **mathematical correctness** and **ledger integrity** — every transaction is traceable, every balance is verifiable, and no silent auto-balancing occurs.

## Long-Term Vision

A deterministic, privacy-first personal finance platform where:

- All financial data is mathematically consistent
- Every monetary value can be traced end-to-end
- Cross-account reconciliation is supported
- Any mismatch triggers explicit user confirmation
- The user retains full data ownership (local SQLite deployment)

## Core Architectural Principles

| Principle | Description |
|-----------|-------------|
| **Backend is authoritative** | The FastAPI/SQLite backend is the single source of truth for all financial data |
| **Financial correctness before features** | No feature is added unless the data pipeline is verified |
| **Evidence over assumptions** | Every finding must include file path, function, line number, and supporting evidence |
| **Read-only audit** | During audit phases, no production code is modified |
| **Append-only reporting** | `Audit_Report.md` is never rewritten — only appended |
| **Deterministic calculations** | Same input always produces same output |
| **Privacy-first** | Local deployment, no cloud dependency, user controls their data |

## Major Technologies

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, Python 3.x
- **Database**: SQLite (raw, no ORM)
- **Charts**: Recharts, Chart.js
- **PDF**: pdfjs-dist, pdfplumber
- **State**: Zustand
- **Testing**: Playwright, pytest

## High-Level Repository Structure

```
ClariFin_OS/
├── frontend/              # Next.js application
│   ├── app/               # Pages (dashboard, transactions, accounts, etc.)
│   ├── components/        # React components (ui + business)
│   ├── hooks/             # React hooks (React Query, custom)
│   ├── types/             # TypeScript type definitions
│   └── tests/             # Playwright E2E tests
├── backend/               # FastAPI + SQLite
│   ├── src/               # API code, engines, parsers
│   │   ├── engines/       # Deterministic computation engines
│   │   ├── core/          # Core domain models and services
│   │   └── ...
│   ├── tests/             # Python test suite
│   └── data/              # Database + uploads
├── memory-bank/           # Cline context (project documentation)
├── servers/               # MCP server implementations
├── Audit_Report.md        # Append-only audit findings
└── README.md              # Project overview
```

## Deprecated

- **Reflex Dashboard**: Archived to `backend/_archived_reflex_dashboard/`