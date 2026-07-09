# Enterprise Roadmap

*P0-P3 prioritized feature timeline*

---

## P0 - Critical Before Production

### 1. Bank API Integration (Plaid/Yodlee/FinBox-style)

| Attribute | Value |
|-----------|-------|
| **Business Value** | Eliminates manual import friction; enables real-time sync |
| **User Impact** | 95% of users expect automatic bank sync |
| **Implementation Effort** | High (OAuth, webhooks, 2FA) |
| **Technical Risk** | Medium (bank API stability, rate limits) |
| **Dependencies** | None |
| **Estimated Time** | 6-8 weeks |

**Why Critical**: Every competitor has this. Manual PDF upload has <10% adoption.

---

### 2. Budget Module (Category Budgets + Tracking)

| Attribute | Value |
|-----------|-------|
| **Business Value** | Core workflow for conscious spenders; drives retention |
| **User Impact** | 80% of users budget actively |
| **Implementation Effort** | Medium (budgets table, vs actual logic, alerts) |
| **Technical Risk** | Low (well-trodden path) |
| **Dependencies** | Categories module |
| **Estimated Time** | 2-3 weeks |

**Why Critical**: YNAB, Monarch, Copilot all center around budgets.

---

### 3. Goal Tracking

| Attribute | Value |
|-----------|-------|
| **Business Value** | Forward-looking planning; upsell path to wealth |
| **User Impact** | 60% of users have financial goals |
| **Implementation Effort** | Medium (goals table, progress tracking, projections) |
| **Technical Risk** | Low |
| **Dependencies** | Budgets, investments |
| **Estimated Time** | 3-4 weeks |

---

### 4. Net Worth History + Trends

| Attribute | Value |
|-----------|-------|
| **Business Value** | Progress visualization; retention driver |
| **User Impact** | Universal expectation |
| **Implementation Effort** | Low (monthly snapshots table) |
| **Technical Risk** | Low |
| **Dependencies** | Networth module |
| **Estimated Time** | 1-2 weeks |

---

## P1 - High Value

### 5. Cashflow Forecasting

| Attribute | Value |
|-----------|-------|
| **Business Value** | Proactive financial decisions; premium differentiation |
| **User Impact** | 70% of users plan ahead |
| **Implementation Effort** | Medium (time-series models, confidence bands) |
| **Technical Risk** | Medium (accuracy varies by user behavior) |
| **Dependencies** | Categories, budget trends |
| **Estimated Time** | 3-4 weeks |

**Approach**: Statistical ARIMA-light or exponential smoothing on historical patterns.

---

### 6. Subscription Detection

| Attribute | Value |
|-----------|-------|
| **Business Value** | Saves 5-15% of user's income; viral potential |
| **User Impact** | 85% of users have subscriptions |
| **Implementation Effort** | Medium (recurring pattern detection) |
| **Technical Risk** | Low |
| **Dependencies** | Transactions, categories |
| **Estimated Time** | 2-3 weeks |

**Why High Value**: Direct measurable savings = clear user value.

---

### 7. Investment Analytics (XIRR, CAGR, Allocation)

| Attribute | Value |
|-----------|-------|
| **Business Value** | Differentiates from basic tracking apps |
| **User Impact** | 60% of users track investments |
| **Implementation Effort** | Medium (XIRR algorithm, sector mapping) |
| **Technical Risk** | Medium (XIRR edge cases) |
| **Dependencies** | Investments table, dividends table |
| **Estimated Time** | 4-5 weeks |

**Key Features**:
- XIRR calculation engine
- Asset allocation by sector
- CAGR and time-weighted returns
- Benchmark comparison (NIFTY/Sensex)

---

### 8. Enhanced Loan Features

| Attribute | Value |
|-----------|-------|
| **Business Value** | Loan-focused users are high-LTV segment |
| **User Impact** | 50% of users have loans |
| **Implementation Effort** | Medium-High |
| **Technical Risk** | Low |
| **Dependencies** | Loans table |
| **Estimated Time** | 3-4 weeks |

**Features**:
- Floating interest rate support
- Recurring prepayment schedules
- Tax deduction tracking (80C, 24)
- Missed payment impact calculator
- Refinance simulation

---

## P2 - Competitive Differentiation

### 9. Tax Module

| Attribute | Value |
|-----------|-------|
| **Business Value** | Compliance upsell; wealth management bridge |
| **User Impact** | High in India (tax season anxiety) |
| **Implementation Effort** | High (Indian tax rules are complex) |
| **Technical Risk** | Medium (regulation changes) |
| **Dependencies** | Investments, transactions |
| **Estimated Time** | 6-8 weeks |

**Features**:
- Capital gains calculator (STCG/LTCG)
- Section 80C/24 deductions
- Tax-loss harvesting suggestions
- ITR-ready reports

---

### 10. Mobile App (React Native/Flutter)

| Attribute | Value |
|-----------|-------|
| **Business Value** | 75% of interactions are mobile; retention driver |
| **User Impact** | Universal expectation |
| **Implementation Effort** | High (new codebase, app store) |
| **Technical Risk** | Medium (offline sync, performance) |
| **Dependencies** | All backend modules |
| **Estimated Time** | 8-12 weeks |

---

### 11. Notification System

| Attribute | Value |
|-----------|-------|
| **Business Value** | Drives engagement and action |
| **User Impact** | 60% of users want alerts |
| **Implementation Effort** | Medium (notification service, push/email) |
| **Technical Risk** | Low |
| **Dependencies** | Budgets, goals, loans |
| **Estimated Time** | 3-4 weeks |

**Features**:
- Budget threshold alerts
- Subscription renewal reminders
- Loan EMI due notifications
- Large transaction alerts

---

### 12. Rules Engine

| Attribute | Value |
|-----------|-------|
| **Business Value** | Reduces manual categorization; reduces churn |
| **User Impact** | Power user expectation |
| **Implementation Effort** | Medium (rules DSL, UI builder) |
| **Technical Risk** | Low |
| **Dependencies** | Categories, transactions |
| **Estimated Time** | 3-4 weeks |

---

## P3 - Future Innovation

### 13. AI-Powered Financial Coach

| Attribute | Value |
|-----------|-------|
| **Business Value** | Premium tier upsell |
| **User Impact** | 40% of users want financial guidance |
| **Implementation Effort** | High (LLM integration, prompts) |
| **Technical Risk** | Medium (accuracy, hallucination) |
| **Dependencies** | Behavior engine, budget |
| **Estimated Time** | 6-8 weeks |

**Approach**: Phi-3 Mini local for privacy-safe coaching.

---

### 14. Credit Monitoring

| Attribute | Value |
|-----------|-------|
| **Business Value** | Adjacent revenue stream |
| **User Impact** | 70% of users check credit periodically |
| **Implementation Effort** | High (bureau APIs, disputes) |
| **Technical Risk** | High (compliance requirements) |
| **Dependencies** | Audit engine, user identity |
| **Estimated Time** | 8-10 weeks |

---

### 15. Retirement Planning

| Attribute | Value |
|-----------|-------|
| **Business Value** | Wealth management upsell |
| **User Impact** | 50% of users planning retirement |
| **Implementation Effort** | High (Monte Carlo, NPS) |
| **Technical Risk** | Medium (actuarial assumptions) |
| **Dependencies** | Investments, goals |
| **Estimated Time** | 6-8 weeks |

---

### 16. Spending Insights Engine

| Attribute | Value |
|-----------|-------|
| **Business Value** | Engagement and retention |
| **User Impact** | Secondary value |
| **Implementation Effort** | Medium (seasonal analysis, trends) |
| **Technical Risk** | Low |
| **Dependencies** | Behavior engine |
| **Estimated Time** | 3-4 weeks |

---

## Development Timeline

### Quarter 1 (P0 + P1)

```
Month 1-2: Bank API integration (P0)
Month 2-3: Budget module (P0)
Month 3-4: Goal tracking (P0)
Month 4-5: Net worth history (P0)
Month 5-6: Cashflow forecasting (P1)
Month 6-7: Subscription detection (P1)
```

### Quarter 2 (P1 + P2)

```
Month 7-9: Investment analytics (P1)
Month 9-11: Enhanced loan features (P1)
Month 11-13: Tax module foundation (P2)
Month 13-15: Notification system (P2)
Month 15-16: Rules engine (P2)
```

### Quarter 3 (P3)

```
Month 16-18: Mobile MVP (P2)
Month 18-20: AI financial coach (P3)
Month 20-22: Credit monitoring (P3)
Month 22-24: Retirement planning (P3)
```

---

## Resource Requirements

### Engineering Team

| Role | Count | Responsibilities |
|------|-------|------------------|
| Backend Engineer | 2 | Bank sync, forecasting, tax |
| Frontend Engineer | 1 | Web + Mobile |
| ML/LLM Engineer | 0.5 | Part-time for AI features |
| Product Manager | 0.5 | Roadmap, user research |
| QA Engineer | 1 | Testing all workflows |

### Infrastructure

- **Local LLM Server**: 4GB RAM for Phi-3 + Qwen-VL
- **Database**: SQLite (current) → PostgreSQL (for scale)
- **Bank Sync**: Plaid Developer account ($0-500/month)
- **Push Notifications**: Firebase/FCM (~$50/month)

---

## Success Metrics

| Metric | P0 Target | P1 Target | P2 Target |
|--------|-----------|-----------|-----------|
| Transaction Coverage | 95% auto-sync | 100% | 100% |
| Budget Feature Adoption | 50% | 70% | 80% |
| Forecast Accuracy | N/A | 70%+ | 85%+ |
| NPS Score | >40 | >60 | >70 |
| Churn Rate | <5% | <3% | <2% |