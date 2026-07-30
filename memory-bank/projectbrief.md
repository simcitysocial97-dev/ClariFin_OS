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
| **Audit-driven development** | All implementation follows verified audit findings |
| **Incremental remediation** | Small, reviewable changes with rollback capability |

## Current Architecture Status

**Backend Test Infrastructure: Decoupled and Autonomous**
- Capability manifests and registries unified in `backend/tests/generated/capability-registry.yaml`
- Test suites organized into modern paths: `tests/unit/`, `tests/invariant/`, `tests/property/`, `tests/golden/`
- Memory bank reduced to essential context documents only

## Major Technologies

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, Python 3.x
- **Database**: SQLite (raw, no ORM)
- **Charts**: Recharts, Chart.js
- **PDF**: pdfjs-dist, pdfplumber
- **State**: Zustand, React Query
- **Testing**: Playwright, pytest
- **Audit**: MCP Playwright, SQLite MCP, Filesystem MCP

## High-Level Repository Structure

```
ClariFin_OS/
├── frontend/                  # Next.js + TypeScript application
│   ├── app/                   # App router pages
│   ├── components/            # React components
│   ├── hooks/                 # Custom hooks
│   ├── types/                 # TypeScript definitions
│   └── tests/                 # E2E tests
├── backend/                   # FastAPI + SQLite backend
│   ├── src/                   # Source code
│   │   ├── engines/           # Pure computation engines (15+ packages)
│   │   ├── repositories/      # SQL access layer (extends BaseRepository)
│   │   ├── services/          # Orchestration layer
│   │   ├── routers/           # HTTP entry points
│   │   └── core/              # Domain models
│   ├── tests/                 # Python test suite
│   │   ├── generated/         # Auto-generated capability registries
│   │   ├── unit/              # Unit tests
│   │   ├── invariant/         # Invariant tests
│   │   ├── property/          # Property-based tests
│   │   └── golden/            # Golden dataset tests
│   └── data/                  # Database + uploads
├── memory-bank/               # Minimal essential context only
│   ├── projectbrief.md        # Product goals and principles
│   ├── activeContext.md       # Current work focus
│   └── architecture.md        # System boundaries and layers
├── servers/                   # MCP server implementations
└── docs/                      # Project documentation
```

## Deprecated

- **Reflex Dashboard**: Archived to `backend/_archived_reflex_dashboard/`