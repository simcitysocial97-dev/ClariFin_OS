# Program 5.3B — Dependency Graph Verification

**Date:** 2026-08-02
**Phase:** Program 5.3B — Backend Architecture Verification & Gap Closure
**Status:** Audit Complete

---

## 1. Feature Dependency Graphs

### Accounts
```mermaid
graph TD
    A[accounts.py] -->|uses| B[AccountService]
    B -->|uses| C[AccountRepository]
    B -->|uses| D[AccountBalanceRepository]
    B -->|uses| E[AccountLinkRepository]
    C -->|uses| F[BaseRepository]
    D -->|uses| F
    E -->|uses| F
    F -->|uses| G[core/db/connection.py]
```
- ✅ **Compliant**: Router → Service → Repository → `core/db`.

---

### Loans
```mermaid
graph TD
    A[loans.py] -->|uses| B[LoanService]
    A -->|uses| C[LoanAnalysisService]
    A -->|uses| D[LoanSimulationService]
    B -->|uses| E[LoanRepository]
    B -->|uses| F[LoanPaymentRepository]
    C -->|uses| E
    D -->|uses| E
    E -->|uses| G[BaseRepository]
    F -->|uses| G
    G -->|uses| H[core/db/connection.py]
```
- ✅ **Compliant**: Router → Service → Repository → `core/db`.

---

### Credit Cards
```mermaid
graph TD
    A[cards_statements.py] -->|uses| B[StatementService]
    A -->|bypasses| C[StatementRepository]
    B -->|uses| C
    C -->|uses| D[BaseRepository]
    D -->|uses| E[core/db/connection.py]
```
- ❌ **Non-Compliant**: Router directly uses `StatementRepository` alongside `StatementService`.

---

### Reconciliation
```mermaid
graph TD
    A[reconciliation.py] -->|uses| B[ReconciliationService]
    B -->|uses| C[ReconciliationRepository]
    C -->|uses| D[BaseRepository]
    D -->|uses| E[core/db/connection.py]
```
- ✅ **Compliant**: Router → Service → Repository → `core/db`.

---

### Cashflow
```mermaid
graph TD
    A[cashflow.py] -->|uses| B[CashflowService]
    B -->|uses| C[CashflowRepository]
    B -->|uses| D[TransactionRepository]
    C -->|uses| E[BaseRepository]
    D -->|uses| E
    E -->|uses| F[core/db/connection.py]
```
- ✅ **Compliant**: Router → Service → Repository → `core/db`.

---

### Investments
```mermaid
graph TD
    A[investments.py] -->|uses| B[InvestmentService]
    B -->|uses| C[InvestmentRepository]
    C -->|uses| D[BaseRepository]
    D -->|uses| E[core/db/connection.py]
```
- ✅ **Compliant**: Router → Service → Repository → `core/db`.

---

### Members
```mermaid
graph TD
    A[members.py] -->|uses| B[MemberService]
    B -->|uses| C[MemberRepository]
    C -->|uses| D[BaseRepository]
    D -->|uses| E[core/db/connection.py]
```
- ✅ **Compliant**: Router → Service → Repository → `core/db`.

---

### Export
```mermaid
graph TD
    A[export.py] -->|uses| B[ExportService]
    B -->|uses| C[TransactionRepository]
    C -->|uses| D[BaseRepository]
    D -->|uses| E[core/db/connection.py]
```
- ✅ **Compliant**: Router → Service → Repository → `core/db`.

---

### Banks
```mermaid
graph TD
    A[banks.py] -->|uses| B[BankService]
    B -->|uses| C[BankRepository]
    C -->|uses| D[BaseRepository]
    D -->|uses| E[core/db/connection.py]
```
- ✅ **Compliant**: Router → Service → Repository → `core/db`.

---

### Import
```mermaid
graph TD
    A[import_router.py] -->|uses| B[ImportService]
    B -->|uses| C[StatementRepository]
    B -->|uses| D[TransactionRepository]
    C -->|uses| E[BaseRepository]
    D -->|uses| E
    E -->|uses| F[core/db/connection.py]
```
- ✅ **Compliant**: Router → Service → Repository → `core/db`.

---

## 2. Engine Dependency Graphs

### Behavior Engine
```mermaid
graph TD
    A[behavior_engine.py] -->|uses| B[No Database Access]
```
- ✅ **Compliant**: Engine does not access the database.

---

### Reconciliation Engine
```mermaid
graph TD
    A[reconciliation_engine.py] -->|uses| B[core/db/connection.py]
```
- ✅ **Compliant**: Engine uses `core.db.connection.get_connection()`.

---

### Ledger Audit Engine
```mermaid
graph TD
    A[ledger_audit_engine.py] -->|uses| B[core/db/connection.py]
```
- ✅ **Compliant**: Engine uses `core.db.connection.get_connection()`.

---

### Balance Engine
```mermaid
graph TD
    A[balance_engine.py] -->|uses| B[core/db/connection.py]
```
- ✅ **Compliant**: Engine uses `core.db.connection.get_connection()`.

---

## 3. Summary of Violations

| Feature          | Violation Type                          | Details                                                                                     | Status      |
|------------------|-----------------------------------------|---------------------------------------------------------------------------------------------|-------------|
| Credit Cards     | Router → Repository Bypass              | `cards_statements.py` directly uses `StatementRepository`.                                 | ❌ Pending  |
| **All Engines**  | **Engine → Database Access**            | **All engines now use `core.db.connection.get_connection()`.**                             | ✅ Complete |

---

## 4. Recommendations
1. **Refactor `cards_statements.py`**: Replace direct `StatementRepository` usage with `StatementService`.
2. **Update Tests/Scripts**: Replace direct `sqlite3.connect()` calls with `core.db.connection.get_connection()`.
3. **Implement DTOs/Mappers**: Restore the DTO and mapper pipeline for frontend contract stability.