# QEA Rules
- Engines: pure functions. No sqlite3, repos, routers, FastAPI.
- Repos: SQL only. No business logic.
- Services: orchestrate only. No raw SQL.
- Routers: validation + delegation only.
- Money: INTEGER paise. Confidence: INTEGER bps. State: lowercase snake_case.
- Scope: accounts.owner_id/household_id is source of truth. transactions.member is legacy.
- Invariants: income-expense=surplus, loan principal monotonically decreases, forecast confidence 0-1.

## Database Rules
- All dates use ISO YYYY-MM-DD internally.
- Transactions use date_iso for logic.
- Never compare raw date strings.
- Financial amounts never use float.

## Change Rules
- Before modifying architecture, inspect existing patterns.
- Prefer existing repository/service boundaries.
- Do not delete unused variables without understanding creation intent.
- Future placeholders require TODO comments.

## Testing Rules
- Prefer property tests over example tests for engines.
- Prefer contract tests over router mocks.
- Prefer golden datasets over large fixture trees.
