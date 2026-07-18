/**
 * Loans Mapper - Pure transformation from DTO to Model
 *
 * This mapper transforms raw API responses to domain-friendly models.
 * It is deterministic, side-effect free, and fully typed.
 *
 * IMPORTANT: The explanation is PRESERVED from the backend, not generated.
 * The backend is the source of truth for all explainability data.
 */

import type { LoansDto, LoanSummaryDto } from '../contracts/api/loans'
import type { LoansModel, LoanSummaryModel } from '../models/loans'

/**
 * Map LoanSummary DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 */
export function mapLoanSummaryToModel(dto: LoanSummaryDto): LoanSummaryModel {
  return {
    id: dto.id,
    name: dto.name,
    lender: dto.lender,
    loanType: dto.loan_type || 'other',
    principalPaise: dto.principal_paise,
    outstandingPaise: dto.outstanding_paise,
    emiPaise: dto.emi_paise,
    interestRate: dto.interest_rate,
    tenureMonths: dto.tenure_months,
    disbursedDate: dto.disbursed_date,
    isActive: dto.is_active,
  }
}

/**
 * Map Loans DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 * - Preserve explanation unchanged
 */
export function mapLoansToModel(dto: LoansDto): LoansModel {
  return {
    loans: dto.loans.map(mapLoanSummaryToModel),
    totalOutstandingPaise: dto.total_outstanding_paise,
    totalPrincipalPaise: dto.total_principal_paise,
    totalMonthlyEmiPaise: dto.total_monthly_emi_paise,
    isPartial: dto.is_partial,
    partialReason: dto.partial_reason,
    lastUpdated: dto.last_updated,
    explanation: dto.explanation ?? null,
  }
}

// Re-export types for convenience
export type { LoansModel, LoanSummaryModel }