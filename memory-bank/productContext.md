# Product Context

## Problem Being Solved

ClariFin_OS solves the difficulty of extracting meaningful financial insights from bank statements provided in PDF format with inconsistent layouts. Traditional approaches require manual data entry or expensive proprietary software.

The core problem is not just parsing — it's **trust**. Users cannot verify whether the numbers displayed by financial software are correct. ClariFin_OS addresses this by making every calculation deterministic, every transaction traceable, and every balance verifiable.

## Target Users

- **Personal Finance Enthusiasts**: Individuals who track spending and want detailed, verifiable insights
- **Small Business Owners**: Those who need to separate personal and business expenses with reliable records
- **Budget-Conscious Users**: People looking to understand and control spending habits with mathematical certainty

## Core User Workflow

1. **Upload**: User uploads PDF bank statements via drag-and-drop
2. **Parse**: System automatically detects bank format and extracts transactions and metadata
3. **Categorize**: Transactions are automatically categorized based on merchant keywords
4. **Visualize**: Data is presented through interactive dashboards with spending insights
5. **Verify**: Every balance, category total, and financial metric can be traced back to source transactions

## Financial Correctness Philosophy

- **Backend is authoritative**: All financial calculations originate from the FastAPI/SQLite backend
- **Ledger integrity**: Transactions are append-only. No modification or deletion after insertion
- **Deterministic replay**: Same input always produces same output. No silent auto-balancing
- **End-to-end traceability**: Every monetary value displayed in the frontend can be traced to a database row
- **Explicit confirmation**: Any mismatch between expected and computed values triggers user confirmation

## Privacy-First Architecture

- Local SQLite deployment — no cloud dependency
- User retains full data ownership
- No telemetry, no data monetization
- Self-hosted, single-user system

## Current Strategy

The project has transitioned from feature implementation to **Architecture Validation and Pipeline Audit**.

```
Architecture Validation
        ↓
    Correctness
        ↓
    Reliability
        ↓
 Implementation
```

The audit establishes a verified understanding of the complete data pipeline before any new features are built. This ensures the foundation is correct before adding complexity.

## Long-Term Product Vision

After the audit is complete and architectural corrections are applied, ClariFin_OS will evolve toward:

- Budget setting and tracking with ledger-verified balances
- Due date reminders and payment tracking
- AI-powered insights and spending predictions (built on verified data)
- Cross-account reconciliation across multiple financial institutions