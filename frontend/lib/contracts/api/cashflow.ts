/**
 * Cashflow API Contract - Zod schemas for DTO validation
 *
 * These schemas validate raw API responses before mapping to ViewModels.
 * SourceReference schema mirrors backend SourceReference.
 */

import { z } from 'zod'
import {
  SourceReferenceSchema,
  EvidenceSchema,
  CalculationStepSchema,
  ConfidenceSchema,
  ExplanationSchema,
} from '@/lib/explainability/contracts/explainability.zod'

// Re-export shared schemas from explainability (they are canonical)
export {
  SourceReferenceSchema,
  EvidenceSchema,
  CalculationStepSchema,
  ConfidenceSchema,
  ExplanationSchema,
}

// Cashflow month schema
const CashflowMonthSchema = z.object({
  month_key: z.string(),
  month_label: z.string(),
  income_paise: z.number().int(),
  expense_paise: z.number().int(),
  net_paise: z.number().int(),
  transaction_count: z.number().int(),
})

// Cashflow response schema - matches backend /api/cashflow/monthly
export const CashflowResponseSchema = z.object({
  months: z.array(CashflowMonthSchema),
  period_months: z.number().int(),
  total_income_paise: z.number().int(),
  total_expense_paise: z.number().int(),
  total_net_paise: z.number().int(),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: ExplanationSchema.optional(),
})

export type CashflowMonthDto = z.infer<typeof CashflowMonthSchema>
export type CashflowDto = z.infer<typeof CashflowResponseSchema>