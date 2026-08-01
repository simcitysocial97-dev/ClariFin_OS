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
    A[cards_statements.py] -->|uses| B[StatementRepository]
    B -->|uses| C[BaseRepository]
    C -->|uses| D[core/db/connection.py]
```
- ❌ **Non-Compliant**: Router bypasses `Service` layer and directly uses `StatementRepository`.

---

### Reconciliation
```mermaid
graph TD
    A[reconciliation.py] -->|uses| B[ReconciliationService]
    A -->|uses| C[ReconciliationRepository]
    B -->|uses| C
    C -->|uses| D[BaseRepository]
    D -->|uses| E[core/db/connection.py]
```
- ❌ **Non-Compliant**: Router directly imports `ReconciliationRepository` alongside `ReconciliationService`.

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
    A[investments.py] -->|uses| B[InvestmentRepository]
    B -->|uses| C[BaseRepository]
    C -->|uses| D[core/db/connection.py]
```
- ❌ **Non-Compliant**: Router bypasses `Service` layer and directly uses `InvestmentRepository`.

---

### Members
```mermaid
graph TD
    A[members.py] -->|uses| B[MemberRepository]
    B -->|uses| C[BaseRepository]
    C -->|uses| D[core/db/connection.py]
```
- ❌ **Non-Compliant**: Router bypasses `Service` layer and directly uses `MemberRepository`.

---

### Export
```mermaid
graph TD
    A[export.py] -->|uses| B[TransactionRepository]
    B -->|uses| C[BaseRepository]
    C -->|uses| D[core/db/connection.py]
```
- ❌ **Non-Compliant**: Router bypasses `Service` layer and directly uses `TransactionRepository`.

---

### Banks
```mermaid
graph TD
    A[banks.py] -->|uses| B[BankRepository]
    B -->|uses| C[BaseRepository]
    C -->|uses| D[core/db/connection.py]
```
- ❌ **Non-Compliant**: Router bypasses `Service` layer and directly uses `BankRepository`.

---

### Import
```mermaid
graph TD
    A[import_router.py] -->|uses| B[StatementRepository]
    A -->|uses| C[TransactionRepository]
    A -->|uses| D[behavior_engine]
    B -->|uses| E[BaseRepository]
    C -->|uses| E
    E -->|uses| F[core/db/connection.py]
```
- ❌ **Non-Compliant**: Router bypasses `Service` layer and directly uses `StatementRepository`, `TransactionRepository`, and `behavior_engine`.

---

## 2. Engine Dependency Graphs

### Behavior Engine
```mermaid
graph TD
    A[behavior_engine.py] -->|uses| B[sqlite3.connect]
```
- ❌ **Non-Compliant**: Engine directly accesses the database.

---

### Reconciliation Engine
```mermaid
graph TD
    A[reconciliation_engine.py] -->|uses| B[sqlite3.connect]
```
- ❌ **Non-Compliant**: Engine directly accesses the database.

---

### Ledger Audit Engine
```mermaid
graph TD
    A[ledger_audit_engine.py] -->|uses| B[sqlite3.connect]
```
- ❌ **Non-Compliant**: Engine directly accesses the database.

---

### Balance Engine
```mermaid
graph TD
    A[balance_engine.py] -->|uses| B[sqlite3.connect]
```
- ❌ **Non-Compliant**: Engine directly accesses the database.

---

## 3. Summary of Violations

| Feature          | Violation Type                          | Details                                                                                     |
|------------------|-----------------------------------------|---------------------------------------------------------------------------------------------|
| Credit Cards     | Router → Repository Bypass              | `cards_statements.py` directly uses `StatementRepository`.                                 |
| Reconciliation   | Router → Repository + Service           | `reconciliation.py` directly imports `ReconciliationRepository`.                           |
| Investments      | Router → Repository Bypass              | `investments.py` directly uses `InvestmentRepository`.                                     |
| Members          | Router → Repository Bypass              | `members.py` directly uses `MemberRepository`.                                             |
| Export           | Router → Repository Bypass              | `export.py` directly uses `TransactionRepository`.                                         |
| Banks            | Router → Repository Bypass              | `banks.py` directly uses `BankRepository`.                                                 |
| Import           | Router → Repository + Engine Bypass     | `import_router.py` directly uses `StatementRepository`, `TransactionRepository`, and `behavior_engine`. |
| Behavior Engine  | Engine → Database Access                | Direct `sqlite3.connect()` calls.                                                          |
| Reconciliation Engine | Engine → Database Access            | Direct `sqlite3.connect()` calls.                                                          |
| Ledger Audit Engine | Engine → Database Access             | Direct `sqlite3.connect()` calls.                                                          |
| Balance Engine   | Engine → Database Access                | Direct `sqlite3.connect()` calls.                                                          |