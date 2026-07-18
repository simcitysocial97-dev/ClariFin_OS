/**
 * Loans API Contract - Zod schemas for DTO validation
 *
 * These schemas validate raw API responses before mapping to ViewModels.
 * SourceReference schema mirrors backend model exactly.
 */

import { z } from 'zod'

// Re-export shared schemas from networth (they are canonical)
export type {
  SourceReferenceSchema,
  EvidenceSchema,
  CalculationStepSchema,
  ConfidenceSchema,
  ExplanationSchema,
} from './networth'

// Loan summary schema
const LoanSummarySchema = z.object({
  id: z.number().int(),
  name: z.string(),
  lender: z.string().nullable(),
  loan_type: z.string().nullable(),
  principal_paise: z.number().int(),
  outstanding_paise: z.number().int().nullable(),
  emi_paise: z.number().int().nullable(),
  interest_rate: z.number(),
  tenure_months: z.number().int().nullable(),
  disbursed_date: z.string().nullable(),
  is_active: z.boolean(),
})

// Loans response schema - matches backend /api/loans
export const LoansResponseSchema = z.object({
  loans: z.array(LoanSummarySchema),
  total_outstanding_paise: z.number().int(),
  total_principal_paise: z.number().int(),
  total_monthly_emi_paise: z.number().int(),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: z.any().optional(),
})

export type LoanSummaryDto = z.infer<typeof LoanSummarySchema>
export type LoansDto = z.infer<typeof LoansResponseSchema>