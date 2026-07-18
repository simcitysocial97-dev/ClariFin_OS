/**
 * Forecasting API Contract - Zod schemas for DTO validation
 *
 * These schemas validate raw API responses before mapping to ViewModels.
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

// Forecast month schema
const ForecastMonthSchema = z.object({
  month: z.string(),
  expected_income_paise: z.number().int(),
  expected_expense_paise: z.number().int(),
  expected_surplus_paise: z.number().int(),
  confidence_bps: z.number().int(),
})

// Forecasting response schema
export const ForecastingResponseSchema = z.object({
  cashflow: z.array(ForecastMonthSchema),
  liquidity: z.record(z.string(), z.any()),
  credit: z.record(z.string(), z.any()),
  risk_flags: z.array(z.record(z.string(), z.any())),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: ExplanationSchema.optional(),
})

export type ForecastMonthDto = z.infer<typeof ForecastMonthSchema>
export type ForecastingResponseDto = z.infer<typeof ForecastingResponseSchema>