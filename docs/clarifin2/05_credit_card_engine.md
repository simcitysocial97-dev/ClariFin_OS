# Credit Card Engine

## Purpose

Defines the deterministic liability-management engine for credit cards in ClariFin OS.

This module intentionally excludes heuristic, prediction, or recommendation features.

## Scope

### In Scope
- Billing and statement date generation
- Outstanding calculation
- Interest accrual and charge calculation
- Credit utilization
- Payment optimization
- EMI conversion
- Foreclosure payoff
- Financial metrics

### Out of Scope
- Rewards, cashback, miles
- Merchant analysis
- Subscription detection
- Credit health score
- Credit score prediction
- Heuristic recommendations

## Architecture

Reuses the established Engine/Repository/Service/Router pattern from the Loan Engine.

- `src/engines/credit_card_engine/` — pure calculations only
- `src/repositories/` — persistence only
- `src/services/credit_card_service.py` — orchestration only
- `src/routers/credit_cards.py` — API only

Loan Engine reuse:
- EMI conversion delegates to `src/engines/loan_engine.emi`
- Foreclosure payoff delegates to `src/engines/loan_engine.foreclosure`

## Units

- All monetary values are stored as integer paise
- All rates are stored as basis points

## API Contract

All endpoints return and accept paise/bps units. See router handlers in `src/routers/credit_cards.py` for exact schemas.

## Database Schema

See `scripts/migration_003_credit_card_engine.py` for:
- `credit_cards`
- `credit_card_statements`