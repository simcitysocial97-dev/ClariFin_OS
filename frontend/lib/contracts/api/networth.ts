/**
 * NetWorth API Contract - Zod schemas for DTO validation
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

// NetWorth explanation schema - uses the canonical ExplanationSchema
const NetWorthExplanationSchema = z.object({
  netWorth: ExplanationSchema,
  assets: ExplanationSchema,
  liabilities: ExplanationSchema,
  confidenceReason: z.string().optional(),
})

// Re-export the NetWorthExplanationSchema for use in other files
export { NetWorthExplanationSchema }

/**
 * NetWorth response from /api/networth
 */
export const NetWorthResponseSchema = z.object({
  net_worth_paise: z.number().int(),
  assets: z.object({
    total_paise: z.number().int(),
    accounts_paise: z.number().int(),
    investments_paise: z.number().int(),
    account_count: z.number().int(),
    investment_count: z.number().int(),
  }),
  liabilities: z.object({
    total_paise: z.number().int(),
    loans_paise: z.number().int(),
    cards_paise: z.number().int(),
    loan_count: z.number().int(),
    card_count: z.number().int(),
  }),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: NetWorthExplanationSchema.optional(),
})

export type NetWorthDto = z.infer<typeof NetWorthResponseSchema>