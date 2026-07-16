# Active Context

## Frontend Development — Financial Operating System Dashboard (In Progress)

### Changes Made (July 2026)

**Widget Infrastructure Created:**
- `types/widget.ts` - Widget contract types (BaseWidgetProps, WidgetStatus, WidgetQueryState)
- `components/dashboard/shared/widget-shell.tsx` - Consistent container with loading/error/empty states
- `components/dashboard/widgets/financial-health-hero.tsx` - Conversation-first health score widget
- `components/dashboard/widgets/financial-inbox-widget.tsx` - Actionable items feed (alerts, nudges, insights)
- `components/dashboard/widgets/money-position-widget.tsx` - Net Worth & assets summary
- `components/dashboard/widgets/borrowing-widget.tsx` - Loans & credit cards summary

**Spending Intelligence Module (Completed):**
- `components/dashboard/widgets/spending/schema.ts` - Zod validation for /api/categories and /api/analytics
- `components/dashboard/widgets/spending/types.ts` - TypeScript interfaces (SpendingInsight, MerchantSpending)
- `components/dashboard/widgets/spending/hook.ts` - useSpending() React Query hook
- `components/dashboard/widgets/spending/SpendingWidget.tsx` - "Where is my money going?" with category breakdown
- `components/dashboard/widgets/spending/MerchantWidget.tsx` - "Who receives my money?" with top merchants
- `components/dashboard/widgets/widget-registry.ts` - Centralized widget registry

### Validation Status
- Next.js build: ✓ SUCCESS
- TypeScript check: ✓ CLEAN
- FVF Framework: Toolchain Lock PASS, ESLint clean on new files

### Next Steps
- Integrate SpendingWidget and MerchantWidget into dashboard/page.tsx
- Verify ARCHITECTURE.md updates for layer file counts

### OpenAPI Schema Exported (July 2026)
- Exported complete OpenAPI schema to `backend/clarifin_openapi.json`
- Contains 105 unique paths with 126 total endpoints
- All 22 routers included (accounts, audit, banks, behavior, behaviour, cards_statements, cashflow, credit_cards, dashboard, export, financial_intelligence, goals, health, import, investments, loans, managed_accounts, members, networth, optimization, patterns, reconciliation, scenarios, transactions)
- File size: 235 KB (7941 lines)
- Generated TypeScript types: `backend/api_types.ts` (7331 lines)
- Created `backend/CAPABILITY_INVENTORY.md` with domain-organized endpoints (159 lines)
```
