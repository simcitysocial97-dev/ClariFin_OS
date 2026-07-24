# Database Map

## Tables (19 core tables)

| Table | Key Columns | Relationships | Ownership |
|-------|-------------|---------------|-----------|
| `accounts` | id, name, bank, balance_paise, owner_id, household_id | Multi-user scoping | AccountRepository |
| `account_balances` | id, account_id, balance_paise, date_iso | FK→accounts | AccountBalanceRepository |
| `audit_business_logic` | id, action, table_name, record_id, timestamp | Audit trail | AuditService |
| `audit_database_tables` | id, table_name, column_name, data_type | Schema audit | AuditService |
| `audit_endpoint_dependencies` | id, endpoint, depends_on | API audit | AuditService |
| `audit_endpoints` | id, path, method | Endpoint audit | AuditService |
| `audit_financial_fields` | id, field_name, table_name, is_paise | Financial audit | AuditService |
| `audit_request_models` | id, model_name | Request audit | AuditService |
| `audit_response_models` | id, model_name | Response audit | AuditService |
| `audit_routers` | id, router_name | Router audit | AuditService |
| `audit_sql_queries` | id, query_text, table_name | SQL audit | AuditService |
| `audit_unit_hints` | id, hint_text | Unit hints | AuditService |
| `auto_heal_events` | id, event_type, amount_paise | Event tracking | StatementService |
| `cards` | id, bank, last4, limit_paise, outstanding_paise | Credit cards | CreditCardRepository |
| `financial_events` | id, event_type, amount_paise, date_iso, month_bucket, account_id, lifecycle_state, outstanding_paise, confidence_bps | Phase 6 table | FinancialEventRepository |
| `events` | id, account_id, amount_paise, date_iso | Event log | EventRepository |
| `import_mappings` | id, mapping_name, date_column, description_column, amount_column | Column mapping | ImportMappingRepository |
| `income_sources` | id, name, account_id | Income tracking | CashflowRepository |
| `investments` | id, name, type, value_paise | Investment tracking | InvestmentRepository |
| `jobs` | id, status, progress, created_at | Job queue | ImportMapper |
| `layout_templates` | id, bank_name, template_json | PDF templates | CSVImporter |
| `loan_payments` | id, loan_id, amount_paise, date_iso | FK→loans | LoanPaymentRepository |
| `loans` | id, name, lender, principal_paise, outstanding_paise, interest_rate | Loan tracking | LoanRepository |
| `members` | id, name, color | Household members | MemberRepository |
| `monthly_snapshots` | id, month_bucket, net_worth_paise | Snapshots | NetWorthRepository |
| `quarantine_pages` | id, statement_id, page_number, reason | Quarantine | StatementRepository |
| `reconciliations` | id, debit_txn_id, credit_txn_id, amount_paise, confidence_bps, deterministic_key | FK→transactions(x2) | ReconciliationRepository |
| `reconciliation_audit_log` | id, reconciliation_id, action, changed_fields | FK→reconciliations | ReconciliationAuditRepository |
| `recurring_transactions` | id, account_id, amount_paise, frequency | Recurring | TransactionRepository |
| `staged_transactions` | id, statement_id, raw_data | Staged | TransactionRepository |
| `statement_imports` | id, filename, status | Import tracking | StatementRepository |
| `statement_pages` | id, statement_id, page_number, page_data | PDF pages | StatementRepository |
| `statements` | id, bank, card_last4, total_amount_due, payment_due_date, source | PK for transactions | StatementRepository |
| `transactions` | id, statement_id, date, description, amount_paise, type, category, hash_signature | FK→statements, immutable | TransactionRepository |

## Primary Relationships

```
statements (id) ←→ transactions (statement_id)
accounts (id) ←→ transactions (account_id, optional)
loans (id) ←→ loan_payments (loan_id)
reconciliations (id) ←→ reconciliation_audit_log (reconciliation_id)
financial_events (id) ←→ financial_event_links (event_id, linked_event_id)
```

## Important Invariants

| Invariant | Rule |
|-----------|------|
| Monetary Values | All amounts INTEGER paise (₹1 = 100 paise) |
| Confidence | All confidence INTEGER bps (0-10000) |
| Dates | ISO YYYY-MM-DD internally |
| Transactions | `hash_signature` immutability triggers |
| Income-Expense | Must equal surplus (verified invariant) |
| Loan Principal | Must monotonically decrease |
| Forecast Confidence | Must be between 0 and 1 |

## Financial Event Lifecycle

States: `open` → `closed` → `archived`

Linked events:
- `financial_event_links` tracks `settles`, `funds`, `rolls_over` relationships

## Key Repository Mappings

| Repository | Tables Accessed |
|------------|-----------------|
| AccountRepository | accounts, account_balances |
| CreditCardRepository | cards, credit_card_statements |
| LoanRepository | loans, loan_payments, loan_amortization_schedule |
| TransactionRepository | transactions, staged_transactions |
| ReconciliationRepository | reconciliations, reconciliation_audit_log |
| FinancialEventRepository | financial_events, financial_event_links, financial_event_lifecycle_log |
| CashflowRepository | cashflow_monthly, income_sources |