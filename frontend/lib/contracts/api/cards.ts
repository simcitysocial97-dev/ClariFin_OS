/**
 * Credit Cards API Contract - Zod schemas for DTO validation
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

// Credit card summary schema
const CreditCardSummarySchema = z.object({
  card_id: z.string(),
  bank: z.string(),
  card_last4: z.string().nullable(),
  credit_limit_paise: z.number().int(),
  current_outstanding_paise: z.number().int(),
  minimum_due_paise: z.number().int(),
  utilization_bps: z.number().int(),
  is_active: z.boolean(),
})

// Credit cards response schema - matches backend /api/v1/credit-cards
export const CreditCardsResponseSchema = z.object({
  cards: z.array(CreditCardSummarySchema),
  total_outstanding_paise: z.number().int(),
  total_credit_limit_paise: z.number().int(),
  total_utilization_bps: z.number().int(),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: z.any().optional(),
})

export type CreditCardSummaryDto = z.infer<typeof CreditCardSummarySchema>
export type CreditCardsDto = z.infer<typeof CreditCardsResponseSchema>