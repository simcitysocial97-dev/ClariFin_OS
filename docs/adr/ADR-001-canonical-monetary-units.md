# ADR-001: Canonical Monetary Units

**Status:** Accepted  
**Date:** 2026-07-05  
**Authors:** Cline (AI Assistant)  
**Phase:** 1 - Monetary Canonical Rules & Domain Foundation

## Context

The ClariFin_OS application handles monetary values throughout the system, including:
- Database storage
- Business logic calculations
- API responses
- Frontend display

Previously, monetary values were represented inconsistently:
- Some values stored as floats (rupees)
- Some values stored as integers (paise)
- API fields had ambiguous names (e.g., `amount`, `balance`)
- No type safety for monetary operations
- Multiple formatting utilities with inconsistent behavior

This led to:
- Floating-point precision errors
- Unit confusion (is this value in paise or rupees?)
- Inconsistent API contracts
- Difficulty maintaining and extending financial features

## Decision

We adopt the following canonical monetary architecture:

### 1. Canonical Storage Unit: Integer Paise

All monetary values stored in the database or processed by business logic must represent **integer paise**.

```
1 INR = 100 paise
Example: ₹1,234.56 = 123456 paise
```

**Rationale:**
- Eliminates floating-point precision errors
- Integer arithmetic is exact and predictable
- Standard practice in financial systems
- Simple conversion: `paise = round(rupees * 100)`

### 2. API Contract: Explicit _paise Suffix

Every monetary field exposed through the API must explicitly indicate its unit using the `_paise` suffix.

**Required naming:**
```
amount_paise
balance_paise
available_balance_paise
interest_paise
credit_limit_paise
emi_paise
fee_paise
tax_paise
networth_paise
```

**Prohibited naming:**
```
amount
balance
interest
```

**Rationale:**
- Self-documenting API contract
- Prevents unit ambiguity
- Clear migration path (add _paise, then remove old field)

### 3. Domain Model: Money Class

A dedicated `Money` domain class represents monetary values:

**Responsibilities:**
- Enforce integer paise representation
- Provide type-safe arithmetic operations
- Prevent floating-point drift
- Support comparison and validation

**Non-responsibilities (delegated to higher layers):**
- Serialization (handled by mapper/DTO layer)
- Business limits (e.g., max amount)
- Formatting (handled by presentation layer)

**Rationale:**
- Single source of truth for monetary operations
- Immutable design prevents accidental mutation
- Type safety catches errors at development time

### 4. Mapper Layer: Domain to DTO Transformation

A dedicated mapper layer transforms domain objects to API DTOs:

**Responsibilities:**
- Convert Money instances to API field values
- Add backward compatibility fields (_rupees)
- Handle serialization to JSON-compatible format
- Single location for API response construction

**Rationale:**
- Clean separation of concerns
- Controllers never manually construct response dictionaries
- Easy to modify API contract without touching domain logic

### 5. Formatting: formatINR as Canonical

The `formatINR(paise)` function is the canonical formatter:

**Responsibilities:**
- Accept integer paise
- Return formatted INR string
- Handle Indian grouping (lakhs, crores)

**Deprecated:**
- `formatRupees(rupees)` - use `formatINR(rupeesToPaise(rupees))`
- Any other formatting utilities

**Rationale:**
- Single source of truth for display
- Consistent formatting across the application
- Clear migration path

## Constraints

### Technical Constraints
- No floating-point arithmetic for monetary values
- All API monetary fields must use `_paise` suffix
- Money class must be immutable
- Serialization handled by mapper layer only

### Business Constraints
- Business rules (limits, validation) belong in higher layers
- Domain model focuses on type safety and arithmetic integrity
- No breaking changes to existing API during Phase 1

### Migration Constraints
- Backward compatibility required during transition
- `_rupees` fields provided as temporary bridge
- Frontend can migrate at its own pace

## Migration Strategy

### Phase 1: Architecture Foundation
1. Create Money domain class
2. Create DTOs with `_paise` fields
3. Create mappers for transformation
4. Add `_rupees` fields for backward compatibility
5. Document architecture and migration path

### Phase 2: API Migration
1. Update API endpoints to use mappers
2. Remove `_rupees` fields from DTOs
3. Remove `include_rupees_field` parameter
4. Add linting rules to prevent float usage

### Phase 3: Frontend Migration
1. Create TypeScript Money class
2. Update frontend types
3. Migrate components to use `_paise` fields
4. Remove `_rupees` field usage

### Phase 4: Cleanup
1. Remove deprecated formatter functions
2. Remove old utility functions
3. Clean up dead code
4. Add comprehensive tests

## Consequences

### Positive
- **Type Safety:** Money class prevents entire classes of bugs
- **Consistency:** All monetary values use the same representation
- **Clarity:** API contract is self-documenting
- **Maintainability:** Single source of truth for monetary operations
- **Testability:** Easy to test monetary logic in isolation

### Negative
- **Migration Effort:** Existing code must be updated
- **Learning Curve:** Developers must learn new patterns
- **Temporary Duplication:** `_rupees` fields during transition
- **Context Window:** Large files require careful management

### Neutral
- **Performance:** Minimal overhead from Money class
- **Storage:** No change to database schema (already using integers)

## Alternatives Considered

### Alternative 1: Use Decimal Type
**Description:** Use Python's `Decimal` type instead of integer paise.

**Pros:**
- Built-in decimal arithmetic
- No conversion needed

**Cons:**
- Still allows unit confusion
- More complex than integer paise
- Not as performant as integers

**Decision:** Rejected. Integer paise is simpler and more explicit.

### Alternative 2: Use Rupees with String Serialization
**Description:** Store as rupees but serialize as strings to avoid precision errors.

**Pros:**
- More intuitive for developers
- No conversion needed

**Cons:**
- String arithmetic is complex
- Still allows unit confusion
- Not suitable for calculations

**Decision:** Rejected. Integer paise is the standard for financial systems.

### Alternative 3: No Domain Model, Just Naming Convention
**Description:** Just use `_paise` suffix without Money class.

**Pros:**
- Less code to write
- No learning curve

**Cons:**
- No type safety
- No arithmetic operations
- Easy to make mistakes

**Decision:** Rejected. Money class provides essential safety.

## References

- **Audit Report:** `Audit_Report.md` (Phase 4: Financial Unit Consistency)
- **Architecture Doc:** `docs/MONETARY_ARCHITECTURE.md`
- **Implementation Report:** `docs/PHASE1_IMPLEMENTATION_REPORT.md`

## Tags

`#architecture` `#monetary` `#domain-model` `#api-contract` `#phase-1`

---

**History:**
- 2026-07-05: Initial version (Phase 1)