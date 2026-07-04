# Loans API Facts

**Document Purpose:** Exact reference for all loan endpoints, what they return, and what the frontend expects.
**Last Audited:** 2026-02-03

---

## Backend Endpoints (from `backend/src/routers/loans.py`)

### CRUD Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/loans` | GET | List all loans (optional status filter) |
| `/api/loans` | POST | Create a new loan |
| `/api/loans/{loan_id}` | GET | Get single loan with payment history & computed fields |
| `/api/loans/{loan_id}` | PUT | Update an existing loan |
| `/api/loans/{loan_id}` | DELETE | Delete a loan and all its payments |

### Payment Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/loans/{loan_id}/payments` | GET | Get payment history for a loan |
| `/api/loans/{loan_id}/payments` | POST | Record a payment for a loan |

### Engine/Calculation Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/loans/{loan_id}/amortization` | GET | Generate ideal amortization schedule |
| `/api/loans/{loan_id}/summary` | GET | Get comprehensive loan summary with replay & forecast |
| `/api/loans/{loan_id}/simulate-prepayment` | POST | Simulate prepayment impact |

---

## Request/Response Details

### GET `/api/loans`

**Query Parameters:**
- `status` (optional): Filter by status - `"active"`, `"closed"`, or `"defaulted"`

**Response:**
```json
{
  "loans": [...Loan objects...],
  "total": 42
}
```

### POST `/api/loans`

**Required Fields (LoanCreate):**
| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | min 1, max 200 chars |
| `principal_paise` | int | > 0 |
| `outstanding_paise` | int | >= 0 |
| `interest_rate` | float | 0-100 |
| `start_date` | string | YYYY-MM-DD or DD/MM/YYYY |

**Optional Fields:**
| Field | Type | Default | Constraints |
|-------|------|---------|-------------|
| `lender` | string | null | max 200 chars |
| `loan_type` | string | "other" | home, car, personal, education, credit_card, gold, other |
| `emi_paise` | int | 0 | >= 0 |
| `tenure_months` | int | null | > 0 |
| `end_date` | string | null | YYYY-MM-DD or DD/MM/YYYY |
| `linked_account_id` | int | null | - |
| `status` | string | "active" | active, closed, defaulted |
| `notes` | string | null | max 1000 chars |

### GET `/api/loans/{loan_id}`

**Returns:** Loan object with these computed fields:
- `payments`: Array of payment records
- `payment_count`: Number of payments made
- `total_paid_paise`: Sum of all principal components
- `total_interest_paid_paise`: Sum of all interest components
- `remaining_payments`: Calculated from tenure_months - payment_count

### PUT `/api/loans/{loan_id}`

**Note:** CANNOT update these fields: `principal_paise`, `tenure_months`, `start_date`, `end_date`, `linked_account_id`

**Allowed Update Fields (all optional):**
- `name`, `lender`, `loan_type`, `outstanding_paise`, `interest_rate`, `emi_paise`, `status`, `notes`

### GET `/api/loans/{loan_id}/payments`

**Response:**
```json
{
  "payments": [...LoanPayment objects...],
  "total": 24
}
```

### POST `/api/loans/{loan_id}/payments`

**Request Body (LoanPaymentCreate):**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `loan_id` | int | Yes | Must match URL param |
| `transaction_id` | int | No | Link to transaction |
| `principal_component_paise` | int | Yes (default 0) | >= 0 |
| `interest_component_paise` | int | Yes (default 0) | >= 0 |
| `payment_date` | string | Yes | YYYY-MM-DD or DD/MM/YYYY |
| `remaining_principal_paise` | int | Yes (default 0) | >= 0 |

### GET `/api/loans/{loan_id}/amortization`

**Response:**
```json
{
  "loan_id": 123,
  "emi_paise": 2500000,
  "total_periods": 240,
  "total_interest_paise": 350000000,
  "schedule": [
    {
      "period": 1,
      "emi_date": "2025-01-01",
      "emi_paise": 2500000,
      "interest_paise": 833333,
      "principal_paise": 1666667,
      "remaining_principal_paise": 298333333
    }
  ]
}
```

### GET `/api/loans/{loan_id}/summary`

**Query Parameters:**
- `as_of` (optional): ISO date string (YYYY-MM-DD) for point-in-time summary

**Response Fields:**
```json
{
  "loan_id": 123,
  "loan_name": "Home Loan",
  "lender": "HDFC Bank",
  "principal_original_paise": 50000000,
  "principal_remaining_paise": 45000000,
  "total_interest_paid_paise": 2500000,
  "future_interest_paise": 30000000,
  "total_interest_full_term_paise": 35000000,
  "completion_percent": 10.0,
  "projected_closure_date": "2045-01-01",
  "days_to_close": 7300,
  "is_closed": false,
  "months_remaining": 240,
  "total_payments_made": 12
}
```

### POST `/api/loans/{loan_id}/simulate-prepayment`

**Request Body (PrepaymentSimulationRequest):**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `extra_payment_paise` | int | Yes | Amount in paise |
| `extra_payment_date` | string | Yes | ISO date (YYYY-MM-DD) |
| `strategy` | string | Yes | "REDUCE_TENURE" or "REDUCE_EMI" |

**Response Fields:**
```json
{
  "loan_id": 123,
  "loan_name": "Home Loan",
  "extra_payment_paise": 10000000,
  "extra_payment_date": "2025-06-01",
  "strategy": "REDUCE_TENURE",
  "interest_saved_paise": 8000000,
  "months_saved": 18,
  "new_closure_date": "2043-07-01",
  "new_emi_paise": 2500000,
  "effective_annual_return_percent": 8.5,
  "original_closure_date": "2045-01-01",
  "original_future_interest_paise": 35000000,
  "new_future_interest_paise": 27000000,
  "remaining_principal_after_prepayment_paise": 35000000
}
```

---

## Frontend Client Functions (from `frontend/lib/api/client.ts`)

| Function Name | Endpoint | Method |
|---------------|----------|--------|
| `fetchLoans(status?)` | `/api/loans` | GET |
| `fetchLoan(loanId)` | `/api/loans/{loanId}` | GET |
| `createLoan(data)` | `/api/loans` | POST |
| `updateLoan(loanId, data)` | `/api/loans/{loanId}` | PUT |
| `deleteLoan(loanId)` | `/api/loans/{loanId}` | DELETE |
| `fetchLoanPayments(loanId)` | `/api/loans/{loanId}/payments` | GET |
| `createLoanPayment(loanId, data)` | `/api/loans/{loanId}/payments` | POST |
| `fetchAmortizationSchedule(loanId)` | `/api/loans/{loanId}/amortization` | GET |
| `fetchLoanSummary(loanId)` | `/api/loans/{loanId}/summary` | GET |
| `simulatePrepayment(loanId, data)` | `/api/loans/{loanId}/simulate-prepayment` | POST |

---

## Frontend Types (from `frontend/types/loan.ts`)

### Core Types

- `Loan` - Full loan record with optional computed fields
- `LoanCreate` - Fields for creating a loan
- `LoanUpdate` - Fields for updating a loan (all optional)
- `LoanPayment` - Single payment record
- `LoanPaymentCreate` - Fields for recording a payment

### Engine Types

- `AmortizationEntry` - Single row of amortization schedule
- `AmortizationSchedule` - Full amortization schedule response
- `LoanSummary` - Comprehensive loan summary
- `PrepaymentSimulationRequest` - Prepayment simulation input
- `PrepaymentResult` - Prepayment simulation output

### Response Types

- `LoansResponse` - `{ loans: Loan[], total: number }`
- `LoanPaymentsResponse` - `{ payments: LoanPayment[], total: number }`

---

## Mismatches Found (ALL FIXED)

### 1. LoanPaymentCreate.loan_id Field ✅ FIXED

**Issue:** Frontend type declared `loan_id` as required in `LoanPaymentCreate`, but:
- The `createLoanPayment` client function passes `loanId` in the URL path
- The backend expected `loan_id` in the request body
- Client did NOT include `loan_id` in the JSON body

**Fix:** Made `loan_id` optional in both:
- `backend/src/dependencies.py` - `LoanPaymentCreate.loan_id: Optional[int] = Field(None, gt=0)`
- `frontend/types/loan.ts` - `loan_id?: number`

### 2. LoanSummary Fields ✅ VERIFIED

**Backend Returns:**
- `loan_id`, `loan_name`, `lender`, plus all summary fields

**Frontend Type (LoanSummary):**
- Has `loan_id`, `loan_name`, `lender` - ✓ Match
- All other fields match ✓

### 3. Update Restrictions Not Reflected in Type ✅ VERIFIED

**Backend:** PUT `/api/loans/{loan_id}` does NOT allow updating:
- `principal_paise`
- `tenure_months`
- `start_date`
- `end_date`
- `linked_account_id`

**Frontend Type (LoanUpdate):**
- Correctly excludes these fields ✓

### 4. next_emi_date Computed Field ✅ FIXED

**Issue:** Frontend Loan type included `next_emi_date?: string | null` but backend didn't compute it.

**Fix:** Added `next_emi_date` computation in `backend/src/routers/loans.py`:
- Calculates next EMI date based on start_date + payment_count months
- Only for active loans with valid tenure
- Returns ISO date string or null

---

## Payoff Projection Note

The frontend client has `fetchLoanPayoffProjection(loanId)` which calls:
- `GET /api/projections/loan/{loanId}`

This is NOT part of the loans router - it's in the projections router. Returns `LoanPayoffProjection` type.

---

## Summary Table

| Feature | Backend Endpoint | Frontend Function | Status |
|---------|------------------|-------------------|--------|
| List loans | GET `/api/loans` | `fetchLoans()` | ✓ Match |
| Get loan | GET `/api/loans/{id}` | `fetchLoan(id)` | ✓ Match |
| Create loan | POST `/api/loans` | `createLoan(data)` | ✓ Match |
| Update loan | PUT `/api/loans/{id}` | `updateLoan(id, data)` | ✓ Match |
| Delete loan | DELETE `/api/loans/{id}` | `deleteLoan(id)` | ✓ Match |
| List payments | GET `/api/loans/{id}/payments` | `fetchLoanPayments(id)` | ✓ Match |
| Create payment | POST `/api/loans/{id}/payments` | `createLoanPayment(id, data)` | ⚠️ Mismatch on loan_id in body |
| Amortization | GET `/api/loans/{id}/amortization` | `fetchAmortizationSchedule(id)` | ✓ Match |
| Loan summary | GET `/api/loans/{id}/summary` | `fetchLoanSummary(id)` | ✓ Match |
| Prepayment sim | POST `/api/loans/{id}/simulate-prepayment` | `simulatePrepayment(id, data)` | ✓ Match |
