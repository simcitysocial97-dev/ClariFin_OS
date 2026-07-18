/**
 * Cashflow API Contract - Zod schemas for DTO validation
 *
 * These schemas validate raw API responses before mapping to ViewModels.
 * SourceReference schema mirrors backend SourceReference.
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

// Cashflow response schema - matches backend /api/cashflow/monthly
export const CashflowResponseSchema = z.object({
  total_income_paise: z.number().int(),
  total_expense_paise: z.number().int(),
  total_net_paise: z.number().int(),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: z.any().optional(),
})

export type CashflowDto = z.infer<typeof CashflowResponseSchema>