# Architecture Boundary Tests

These tests enforce the QEA (Query-Execute-Architecture) rules using lightweight Python AST inspection.

## Purpose

Prevent architectural violations by automatically checking:
- Engines remain pure (no database, router, or FastAPI imports)
- Repositories only perform SQL access (no business logic)
- Services orchestrate only (no raw SQL)
- Routers validate + delegate (no business logic)

## Running the Tests

```bash
# Run all architecture tests
pytest tests/architecture -q

# Run specific boundary test
pytest tests/architecture/test_layer_boundaries.py -v
```

## QEA Rules Enforced

| Rule | Layer | Allowed | Forbidden |
|------|-------|---------|-----------|
| QEA-1 | Engines | pure Python, domain calculations | sqlite3, sqlalchemy, repositories, routers, FastAPI |
| QEA-2 | Repositories | database access, SQL queries | business calculations, calling engines |
| QEA-3 | Services | orchestration, repositories, engines | raw SQL |
| QEA-4 | Routers | validation, delegation | repository calls, business logic |

## Adding New Rules

Add a new test method to the appropriate class in `test_layer_boundaries.py`. Use AST-based import inspection for efficiency.