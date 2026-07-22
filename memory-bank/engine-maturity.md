# Engine Maturity

| Engine | State | Properties | Golden | Invariants | Mutation |
|--------|-------|------------|--------|------------|----------|
| CashflowEngine | Mature | ✅ | ✅ | ✅ | ❌ |
| LoanEngine | Mature | ✅ | ⚠️ | ✅ | ❌ |
| CreditCardEngine | Stable | ❌ → ✅ | ❌ → ✅ | ✅ | ❌ |
| BehaviourEngine | Stable | ❌ → ✅ | ✅ | ❌ → ✅ | ❌ |
| AccountEngine | Stable | ❌ → ✅ | ❌ → ✅ | ❌ → ✅ | ❌ |
| ReconciliationEngine | Good | ❌ | ❌ | ❌ | ❌ |
| FinancialIntelligence | Experimental | ✅ | ❌ | ✅ | ❌ |
| TransactionIntelligence | Experimental | ❌ | ❌ | ❌ | ❌ |
| FinancialEvents | Experimental | ❌ | ❌ | ❌ | ❌ |
| NudgeEngine | Prototype | ❌ | ❌ | ❌ | ❌ |
| InsightGenerator | Prototype | ❌ | ❌ | ❌ | ❌ |
| RecommendationEngine | Prototype | ❌ | ❌ | ❌ | ❌ |
| LedgerAuditEngine | Prototype | ❌ | ❌ | ❌ | ❌ |

### Maturity Definitions

| Level | Definition |
|-------|------------|
| **Mature** | Contracts documented, properties passing, golden scenarios, invariants defined. Ready for mutation testing. |
| **Stable** | Production-hardened but validation gaps exist. |
| **Good** | Working well but needs more validation coverage. |
| **Experimental** | Recently added, core logic works, validation sparse. |
| **Prototype** | Early stage, limited validation. |
