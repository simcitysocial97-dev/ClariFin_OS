# API Contract Plan - ClariFinOS 2.0

*All REST endpoints for the five core engines*

---

## Account Intelligence Engine APIs

### Accounts Collection
```
GET /api/v1/accounts
Response: AccountCardData[]

POST /api/v1/accounts
Body: {name, bank, account_type, balance_paise, institution_id}
Response: AccountDetailData
```

### Account Detail
```
GET /api/v1/accounts/{account_id}
Response: AccountDetailData

PUT /api/v1/accounts/{account_id}
Body: {name?, notes?, account_type?}
Response: AccountDetailData

DELETE /api/v1/accounts/{account_id}
Response: {success: true}
```

### Account Intelligence
```
GET /api/v1/accounts/{account_id}/balance-history
Query: limit=90, start_date, end_date
Response: {dates: string[], balances: number[]}

GET /api/v1/accounts/{account_id}/cash-flow
Query: days=30
Response: {net_flow_paise: number, daily_average: number, trend: "up|down|stable"}

GET /api/v1/accounts/{account_id}/health
Response: {
  score: number,
  components: {activity, balance, fees, relationship},
  recommendations: string[]
}

GET /api/v1/accounts/{account_id}/trends
Response: {
  direction: "improving|stable|deteriorating",
  velocity_paise_per_day: number,
  seasonality: number
}
```

---

## Reconciliation Engine APIs

### Scan & Match
```
POST /api/v1/reconciliation/scan
Body: {max_date_window_days?: number, auto_confirm_threshold?: number}
Response: {matches_found: number, high_confidence: number}

GET /api/v1/reconciliation/pending
Query: limit=50, page=1
Response: ReconciliationMatchData[]
```

### Reconciliation Actions
```
GET /api/v1/reconciliation/{match_id}
Response: ReconciliationMatchData

POST /api/v1/reconciliation/{match_id}/confirm
Body: {actor?: string}  # defaults to "user"
Response: {success: true, explanation: string}

POST /api/v1/reconciliation/{match_id}/reject
Body: {reason?: string}
Response: {success: true}

POST /api/v1/reconciliation/{match_id}/split
Body: {leg_amounts: number[]}
Response: ReconciliationMatchData[]  # multiple created

POST /api/v1/reconciliation/{match_id}/undo
Response: {success: true, restored_state: string}
```

### Statistics
```
GET /api/v1/reconciliation/stats
Response: {
  coverage_ratio: number,
  health_score: number,
  pending_count: number,
  confirmed_count: number,
  rejected_count: number
}

GET /api/v1/reconciliation/transactions/{txn_id}/matches
Response: ReconciliationMatchData[]
```

---

## Loan Intelligence Engine APIs

### Loans Collection
```
GET /api/v1/loans
Response: LoanSummaryData[]

POST /api/v1/loans
Body: {
  name, lender, loan_type, principal_paise,
  interest_rate, tenure_months, disbursed_date,
  interest_type?, prepayment_mode?
}
Response: LoanDetailData
```

### Loan Detail
```
GET /api/v1/loans/{loan_id}
Response: LoanDetailData

PUT /api/v1/loans/{loan_id}
Body: {name?, notes?, next_emi_date?, interest_rate?}
Response: LoanDetailData

DELETE /api/v1/loans/{loan_id}
Response: {success: true}
```

### Loan Intelligence
```
GET /api/v1/loans/{loan_id}/schedule
Query: months_ahead=24
Response: AmortizationEntry[]

POST /api/v1/loans/{loan_id}/prepayment-simulation
Body: {
  prepayment_paise,
  prepayment_date,
  mode: "reduce_tenure|reduce_emi"
}
Response: PrepaymentImpact

GET /api/v1/loans/{loan_id}/health
Response: {
  score: number,
  components: {dti, utilization, stress, payment},
  recommendations: string[]
}

POST /api/v1/loans/{loan_id}/refinance-analysis
Body: {
  new_interest_rate,
  new_tenure,
  processing_fee_paise
}
Response: RefinanceEvaluation

POST /api/v1/loans/{loan_id}/record-payment
Body: {
  payment_date,
  amount_paise,
  late_fee_paise?,
  source_account_id
}
Response: LoanPaymentRecord
```

### Aggregates
```
GET /api/v1/loans/stats/dti
Response: {ratio: number, interpretation: string}

GET /api/v1/loans/stats/liability-ratio
Response: {ratio: number, total_liabilities: number}

GET /api/v1/loans/strategies
Query: avalanche=true,snowball=true
Response: {
  avalanche_order: LoanId[],
  snowball_order: LoanId[],
  interest_savings_1yr: number
}
```

---

## Credit Card Intelligence Engine APIs

### Credit Cards Collection
```
GET /api/v1/credit-cards
Response: CreditCardSummary[]

POST /api/v1/credit-cards
Body: {
  account_id, name, bank, card_last4,
  credit_limit_paise, annual_fee_paise,
  interest_rate_pa, billing_day
}
Response: CreditCardDetail
```

### Credit Card Detail
```
GET /api/v1/credit-cards/{card_id}
Response: CreditCardDetail

PUT /api/v1/credit-cards/{card_id}
Body: {name?, notes?, reward_rate_json?}
Response: CreditCardDetail
```

### Credit Card Intelligence
```
GET /api/v1/credit-cards/{card_id}/statements
Query: limit=12
Response: CreditCardStatement[]

GET /api/v1/credit-cards/{card_id}/utilization
Query: days=90
Response: {
  current_utilization: number,
  average_utilization: number,
  trend: "up|down|stable"
}

GET /api/v1/credit-cards/{card_id}/rewards
Query: months=12
Response: {
  points_earned: number,
  cashback_earned: number,
  redemption_value: number
}

POST /api/v1/credit-cards/{card_id}/optimize-payment
Body: {amount_available_paise}
Response: PaymentRecommendation

GET /api/v1/credit-cards/{card_id}/health
Response: {
  score: number,
  components: {utilization, payment, reward, risk},
  recommendations: string[]
}

GET /api/v1/credit-cards/subscriptions
Response: CreditCardSubscription[]
```

---

## Behavioural Intelligence Engine APIs

### Behaviour Core
```
GET /api/v1/behaviour/score
Response: {
  wellness_score: number,
  components: {
    savings_discipline,
    cashflow_stability,
    resilience_index,
    salary_dependence
  }
}

GET /api/v1/behaviour/monthly-trends
Query: months=12
Response: {
  savings_trend: "up|down|stable",
  expense_trend: "up|down|stable",
  income_trend: "up|down|stable"
}
```

### Patterns & Alerts
```
GET /api/v1/behaviour/patterns
Query: type=IMPULSE|SUBSCRIPTION|NIGHT_SPEND
Response: BehaviourPattern[]

GET /api/v1/behaviour/alerts
Query: active=true, limit=20
Response: AlertData[]
```

### Recommendations
```
GET /api/v1/behaviour/recommendations
Query: limit=10
Response: RecommendationData[]

POST /api/v1/behaviour/recommendations/{id}/acknowledge
Response: {success: true}
```

### Deep Analysis
```
GET /api/v1/behaviour/spending-insights
Query: days=90
Response: {
  essential_vs_discretionary: {essential, discretionary},
  top_categories: CategorySpend[],
  impulse_score: number
}

GET /api/v1/behaviour/lifestyle-inflation
Response: {
  rate: number,
  flagged_categories: string[],
  trend_months: number
}

GET /api/v1/behaviour/resilience
Response: {
  buffer_months: number,
  resilience_score: number,
  recommendations: string[]
}
```

---

## Dashboard APIs

### Executive Summary
```
GET /api/v1/dashboard/summary
Response: {
  net_worth_paise: number,
  cash_flow_paise: number,
  wellness_score: number,
  accounts_summary: AccountSummary[],
  loans_summary: LoanSummary[],
  credit_summary: CreditSummary[]
}

GET /api/v1/dashboard/upcoming-obligations
Query: days_ahead=30
Response: ObligationData[]
```

---

## Forecast APIs

```
GET /api/v1/forecasts/cashflow
Query: months=6
Response: CashflowForecast[]

GET /api/v1/forecasts/net-worth
Query: months=12
Response: NetWorthProjection[]

GET /api/v1/forecasts/loan-payoff
Query: loan_id, months_ahead=24
Response: LoanPayoffProjection[]
```

---

## Shared Types

### Common Response Wrapper
```typescript
interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  warnings?: string[];
}
```

### Pagination
```typescript
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}
```

### Date Range
```typescript
interface DateRange {
  start_date: string;  // ISO
  end_date: string;    // ISO
}
```

---

## Versioning Strategy

All APIs versioned as `/api/v1/` with plan to migrate to `/api/v2/` for breaking changes.

Webhook endpoints for:
- Bank sync callbacks (`/api/v1/webhooks/bank-sync`)
- Alert delivery (`/api/v1/webhooks/alerts`)

---

## Rate Limiting

- **Authenticated**: 1000 req/minute
- **Import**: 10 req/minute
- **Reconciliation**: 30 req/minute
- **Forecast**: 60 req/minute

All responses include headers:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`