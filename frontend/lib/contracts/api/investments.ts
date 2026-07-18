/**
 * Investments API Contract - Zod schemas for DTO validation
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

// Investment summary schema
const InvestmentSummarySchema = z.object({
  id: z.number().int(),
  name: z.string(),
  type: z.string(),
  invested_paise: z.number().int(),
  current_value_paise: z.number().int(),
  gain_paise: z.number().int(),
  gain_percent: z.number(),
  is_active: z.boolean(),
})

// Investments response schema - matches backend /api/investments
export const InvestmentsResponseSchema = z.object({
  investments: z.array(InvestmentSummarySchema),
  total_invested_paise: z.number().int(),
  total_current_value_paise: z.number().int(),
  total_gain_paise: z.number().int(),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: z.any().optional(),
})

export type InvestmentSummaryDto = z.infer<typeof InvestmentSummarySchema>
export type InvestmentsDto = z.infer<typeof InvestmentsResponseSchema>