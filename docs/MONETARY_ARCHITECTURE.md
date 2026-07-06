# Monetary Architecture Documentation

## Overview

This document defines the canonical monetary architecture for ClariFin_OS. All financial operations must adhere to these rules to ensure correctness, prevent unit confusion, and maintain data integrity.

## Canonical Rules

### Rule 1 — Canonical Storage Unit

Every monetary value stored in the database or processed by business logic must represent **integer paise**.

- **1 INR = 100 paise**
- Example: ₹1,234.56 = 123456 paise
- **Floating-point monetary values must never be used internally**

```python
# ✅ CORRECT
balance_paise = 123456  # ₹1,234.56

# ❌ WRONG
balance_rupees = 1234.56  # Floating-point, prone to precision errors
```

### Rule 2 — API Contract

Every monetary field exposed through the API must explicitly indicate its unit using the `_paise` suffix.

**Required naming convention:**
```python
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

**Prohibited naming (unit ambiguity):**
```python
# ❌ WRONG - Generic names without unit suffix
amount
balance
interest
```

### Rule 3 — Business Logic

Business logic must operate exclusively on integer paise.

- All calculations use the `Money` domain class
- No business logic should depend on floating-point rupee values
- Arithmetic operations return new `Money` instances (immutable)

```python
from core.domain.money import Money

# ✅ CORRECT
balance1 = Money(100000)  # ₹1,000.00
balance2 = Money(50000)   # ₹500.00
total = balance1.add(balance2)  # Money(150000) = ₹1,500.00

# ❌ WRONG
balance1 = 1000.00  # Float, unit ambiguity
balance2 = 500.00
total = balance1 + balance2  # 1500.0 - is this paise or rupees?
```

### Rule 4 — Presentation Layer

The frontend must never perform monetary calculations.

**Frontend responsibilities:**
- Receive API data (already in paise)
- Pass paise values into formatting utilities
- Render formatted output

**Frontend must NOT:**
- Perform arithmetic on monetary values
- Convert between paise and rupees for calculations
- Implement business logic

```typescript
// ✅ CORRECT
const formatted = formatINR(account.balance_paise);

// ❌ WRONG
const rupees = account.balance / 100;  // Conversion in UI
const total = rupees1 + rupees2;  // Arithmetic in UI
```

### Rule 5 — Formatting
 
The application must have **one canonical formatting system**.
 
**Canonical formatter hierarchy:**
 1. `formatINR(paise)` — Primary formatter for all new code
 2. `formatPaise(paise)` — Alias for `formatINR` (backward compatibility)
 3. `formatRupees(rupees)` — **DEPRECATED** - use `formatINR(rupeesToPaise(rupees))`
 4. `formatINRCompact(paise)` — Compact display (e.g., "₹12.5K")
 5. `formatRupeesCompact(rupees)` — **DEPRECATED**

## Architecture

### Data Flow
 
```
Database (paise)
    ↓
Repository Layer
    ↓
Domain Layer (Money class)
    ↓
Mapper Layer (DTO transformation)
    ↓
API Response (JSON with _paise fields)
    ↓
Frontend (TypeScript types with _paise suffix)
    ↓
Formatting Utilities (formatINR)
    ↓
UI Display (₹1,234.56)
```
 
### Backend Architecture
 
#### Domain Layer (`backend/src/core/domain/`)
 
**Purpose:** Single source of truth for monetary operations
 
**Key class:** `Money`
- Immutable value object
- Stores amount as integer paise
- Provides safe arithmetic operations
- Prevents floating-point drift
 
**Usage:**
```python
from core.domain.money import Money
 
# Create from paise
amount = Money(100000)  # ₹1,000.00
 
# Arithmetic
total = amount1.add(amount2)
difference = amount1.subtract(amount2)
percentage = amount.percentage(25)  # 25% of amount
 
# Conversion (display only)
rupees = amount.to_rupees()  # 1000.0
```

#### DTO Layer (`backend/src/core/dtos/`)

**Purpose:** Define API contract with explicit units

**Key principles:**
- All monetary fields use `_paise` suffix
- Backward compatibility fields use `_rupees` suffix (temporary)
- Pydantic models provide validation
- Self-documenting via Field descriptions

**Example:**
```python
class AccountDTO(BaseModel):
    id: str
    name: str
    balance_paise: int  # Canonical field
    balance_rupees: Optional[float] = None  # TODO: Remove in Phase 2
```

#### Mapper Layer (`backend/src/core/mappers/`)

**Purpose:** Transform domain objects to DTOs

**Key principles:**
- ONLY location where API responses are constructed
- Controllers must never manually build response dictionaries
- All monetary conversions happen here
- Backward compatibility fields added here

**Example:**
```python
class AccountMapper:
    @staticmethod
    def to_dto(account_id, name, balance: Money, ...):
        dto = {
            "id": account_id,
            "balance_paise": balance.paise,
        }
        
        # TODO: Remove in Phase 2
        dto["balance_rupees"] = balance.to_rupees()
        
        return AccountDTO(**dto)
```

### Frontend Architecture

#### Domain Layer (`frontend/lib/domain/`)

**Purpose:** Type-safe monetary representation in frontend

**Key class:** `Money`
- Mirrors backend Money class
- Type-safe operations
- Prevents unit confusion
- Formatting methods

**Usage:**
```typescript
import { Money } from '@/lib/domain/money';

// Create from paise
const amount = new Money(100000);  // ₹1,000.00

// Format for display
const display = amount.format();  // "₹1,000"

// Type-safe
const balance: number = account.balance_paise;  // Explicit unit
```

#### Type Definitions (`frontend/types/`)

**Purpose:** Type-safe API contracts

**Key principles:**
- All monetary fields use `_paise` suffix
- Backward compatibility fields use `_rupees` suffix (temporary)
- Align with backend DTOs

**Example:**
```typescript
export interface Account {
  id: string;
  name: string;
  balance_paise: number;  // Canonical field
  balance_rupees?: number;  // TODO: Remove in Phase 2
}
```

#### Formatting (`frontend/lib/format.ts`, `frontend/lib/utils/format.ts`)
 
**Purpose:** Single canonical formatting system
 
**Primary formatter:** `formatINR(paise)`
- Accepts integer paise
- Returns formatted INR string
- Handles Indian grouping (lakhs, crores)
 
**Example:**
```typescript
import { formatINR } from '@/lib/utils/format';
 
const display = formatINR(123456);  // "₹1,234.56"
const display2 = formatINR(10000000);  // "₹1,00,000.00"
```

## Backward Compatibility Strategy

### Phase 1 (Current)
- API returns both `field_paise` and `field_rupees`
- Frontend migrates to use `_paise` fields
- `_rupees` fields marked as deprecated

### Phase 2 (Future)
- Frontend fully migrated to `_paise` fields
- Backend removes `_rupees` fields
- Remove deprecated formatter functions
- Clean up dead code

### Migration Pattern

**Backend:**
```python
# In mapper
dto_data = {
    "balance_paise": balance.paise,  # Primary
}

# TODO: Remove in Phase 2
if include_rupees_field:
    dto_data["balance_rupees"] = balance.to_rupees()
```

**Frontend:**
```typescript
// Use _paise field
const balance = account.balance_paise;
const display = formatINR(balance);

// Ignore _rupees field
// (Still present in API, but not used)
```

## Field Naming Conventions

### Monetary Fields

**Pattern:** `{entity}_{metric}_paise`

**Examples:**
- `balance_paise` - Account balance
- `amount_paise` - Transaction amount
- `total_spend_paise` - Total spending
- `net_cash_flow_paise` - Net cash flow
- `emi_paise` - EMI amount
- `credit_limit_paise` - Credit limit

### Non-Monetary Fields

**Pattern:** No suffix needed

**Examples:**
- `transaction_count` - Count (unitless)
- `savings_rate` - Percentage (0-100)
- `buffer_days` - Days (unitless)
- `category` - String (unitless)

## Conversion Guidelines

### When to Convert

**Convert paise → rupees ONLY for:**
- Display/formatting
- User-facing output
- Debug logging

**Never convert for:**
- Calculations
- Comparisons
- Business logic
- Storage

### Conversion Methods

**Backend:**
```python
from core.domain.money import Money

amount = Money(100000)
rupees = amount.to_rupees()  # 1000.0 (float, display only)
```

**Frontend:**
```typescript
import { paiseToRupees } from '@/lib/utils/format';

const rupees = paiseToRupees(100000);  // 1000 (display only)
```

## Validation
 
### Backend Validation
 
**Money class enforces:**
- Type checking (must be int)
- Type safety (rejects floats)
 
```python
# ✅ Valid
amount = Money(100000)
 
# ❌ Raises TypeError
amount = Money(100000.50)
```

### Frontend Validation

**TypeScript enforces:**
- Type checking (number type)
- Naming convention (_paise suffix)
- No arithmetic on monetary values

```typescript
// ✅ Valid
const balance: number = account.balance_paise;

// ❌ Type error if using wrong field
const balance: number = account.balance;  // Field doesn't exist
```

## Testing

### Backend Tests
 
**Test Money class:**
- Arithmetic operations
- Comparison operations
- Validation (type)
- Edge cases (zero, negative, large values)
 
**Test mappers:**
- Domain → DTO transformation
- Backward compatibility fields
- Field naming conventions
 
### Frontend Tests
 
**Test formatting:**
- `formatINR()` with various inputs
- Edge cases (zero, negative, large values)

**Test types:**
- Type definitions match API contract
- No unit ambiguity in types
- Backward compatibility fields present

## Common Pitfalls

### ❌ DON'T: Use floats for money

```python
# WRONG
balance = 1234.56  # Float, precision errors
```

### ❌ DON'T: Perform calculations in presentation layer

```typescript
// WRONG
const total = (account1.balance + account2.balance) / 100;
```

### ❌ DON'T: Use generic field names

```python
# WRONG
{"balance": 100000}  # What unit is this?
```

### ❌ DON'T: Mix units in API

```python
# WRONG - some fields in paise, some in rupees
{
    "balance_paise": 100000,
    "interest": 5.5  # Is this rupees? percentage?
}
```

### ✅ DO: Use Money class everywhere

```python
# CORRECT
balance = Money(100000)
interest = Money(5500)
total = balance.add(interest)
```

### ✅ DO: Use explicit field names

```python
# CORRECT
{
    "balance_paise": 100000,
    "interest_paise": 5500
}
```

### ✅ DO: Keep units consistent

```python
# CORRECT - all monetary fields in paise
{
    "balance_paise": 100000,
    "interest_paise": 5500,
    "fee_paise": 500
}
```

## Migration Checklist

### Phase 1 (Current)
- [x] Create Money domain class
- [x] Create DTOs with _paise fields
- [x] Create mappers
- [x] Update API endpoints to use mappers
- [x] Add backward compatibility _rupees fields
- [x] Create frontend Money class
- [x] Update frontend types
- [x] Consolidate formatters
- [x] Fix accounts page (R1)

### Phase 2 (Future)
- [ ] Remove _rupees fields from DTOs
- [ ] Remove `include_rupees_field` parameter from mappers
- [ ] Remove deprecated formatter functions
- [ ] Clean up dead code
- [ ] Migrate all components to use domain layer
- [ ] Remove transitional documentation

## References

- **Audit Report:** `Audit_Report.md` (Phase 4: Financial Unit Consistency)
- **Money Class:** `backend/src/core/domain/money.py`
- **DTOs:** `backend/src/core/dtos/`
- **Mappers:** `backend/src/core/mappers/`
- **Frontend Domain:** `frontend/lib/domain/money.ts` (to be created)
- **Formatter:** `frontend/lib/utils/format.ts`

## Version

- **Created:** 2026-07-05
- **Phase:** 1 - Monetary Canonical Rules & Domain Foundation
- **Status:** Active