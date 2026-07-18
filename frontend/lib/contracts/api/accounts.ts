/**
 * Accounts API Contract - Zod schemas for DTO validation
 *
 * These schemas validate raw API responses before mapping to ViewModels.
 * SourceReference schema mirrors backend model exactly.
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

// Account summary schema
const AccountSummarySchema = z.object({
  account_id: z.string(),
  name: z.string(),
  bank: z.string(),
  account_type: z.string(),
  balance_paise: z.number().int(),
  average_balance_paise: z.number().int(),
  trend: z.string(),
  velocity_paise_per_day: z.number().int(),
  is_active: z.boolean(),
})

// Accounts response schema - matches backend /api/v1/accounts/summary
export const AccountsResponseSchema = z.object({
  accounts: z.array(AccountSummarySchema),
  total_balance_paise: z.number().int(),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: ExplanationSchema.optional(),
})

export type AccountSummaryDto = z.infer<typeof AccountSummarySchema>
export type AccountsDto = z.infer<typeof AccountsResponseSchema>