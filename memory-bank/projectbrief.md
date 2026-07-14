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

## Audit Status

**Audit Phases 0–6: COMPLETE**
- **Phase 0**: Repository Structure & Initial Assessment
- **Phase 1**: Frontend Static Analysis
- **Phase 2**: Backend Static Analysis
- **Phase 3**: API & Hook Consistency
- **Phase 4**: Financial Unit & Type Safety
- **Phase 5**: Dead Code & Orphaned Components
- **Phase 6 (Retry)**: Runtime Verification & Evidence Collection

**Key Findings:**
- ✅ **3 BLOCKER issues** verified at runtime
- ✅ **4 HIGH priority issues** verified
- ✅ **1 CRITICAL financial unit violation** confirmed (account balance displayed 100x too high)
- ✅ **2 dead routes** confirmed (/loans, /investments)
- ✅ **19 dead backend endpoints** identified
- ✅ **11 dead API client functions** identified
- ✅ **10 dead React Query hooks** identified
- ✅ **7 unused business components** identified
- ✅ **Dual currency convention** confirmed (paise + rupees)

## Implementation Plan

**Engineering Implementation Blueprint: COMPLETE**
- **Document**: `Implementation_Blueprint.md`
- **Phases**: 12 implementation phases
- **PRs**: 28 small, reviewable pull requests
- **Timeline**: 6 weeks (July 7 – August 16, 2026)
- **Strategy**: Incremental delivery with rollback capability

**Key Implementation Goals:**
- ✅ Establish single currency convention (paise as canonical unit)
- ✅ Fix all unit violations
- ✅ Remove all dead code
- ✅ Consolidate duplicate systems
- ✅ Fix broken navigation
- ✅ Add comprehensive test coverage
- ✅ Achieve zero runtime errors

## Success Metrics

| Metric | Target |
|--------|--------|
| Zero BLOCKER issues | ✅ |
| Zero CRITICAL issues | ✅ |
| Zero HIGH priority issues | ✅ |
| Zero runtime errors | ✅ |
| Zero console errors | ✅ |
| Zero failed API requests | ✅ |
| Zero 404 routes | ✅ |
| Zero dead code | ✅ |
| Zero duplicate systems | ✅ |
| Single currency convention | ✅ |
| All financial data displays correctly | ✅ |
| All navigation routes work | ✅ |
| 100% test coverage for critical paths | ✅ |
| Zero unit violations | ✅ |

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
├── Implementation_Blueprint.md  # Engineering implementation plan
└── README.md              # Project overview
```

## Deprecated

- **Reflex Dashboard**: Archived to `backend/_archived_reflex_dashboard/`