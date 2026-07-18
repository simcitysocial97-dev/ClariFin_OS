/**
 * Overview API Contract - Zod schemas for DTO validation
 *
 * These schemas validate raw API responses before mapping to ViewModels.
 */

import { z } from 'zod'

// Re-export shared schemas from networth (they are canonical)
export type {
  SourceReferenceSchema,
  EvidenceSchema,
  CalculationStepSchema,
  ConfidenceSchema,
  ExplanationSchema,
} from '../../../contracts/api/networth'

// Behavioral insight schema
const BehavioralInsightSchema = z.object({
  title: z.string(),
  description: z.string(),
  severity: z.enum(['warning', 'positive', 'neutral']),
  icon: z.string(),
})

// Monthly chart point schema
const MonthlyChartPointSchema = z.object({
  month: z.string(),
  amount: z.number(),
})

// Category chart point schema
const CategoryChartPointSchema = z.object({
  name: z.string(),
  value: z.number(),
})

// Overview response schema - matches backend /api/overview
export const OverviewResponseSchema = z.object({
  total_spend: z.number(),
  total_spend_display: z.string(),
  this_month: z.number(),
  this_month_display: z.string(),
  last_month: z.number(),
  last_month_display: z.string(),
  month_change: z.string(),
  transaction_count: z.number().int(),
  card_count: z.number().int(),
  months_of_data: z.number().int(),
  monthly_average: z.number(),
  monthly_average_display: z.string(),
  above_below_avg: z.string(),
  above_avg_is_bad: z.boolean(),
  monthly_chart: z.array(MonthlyChartPointSchema),
  category_chart: z.array(CategoryChartPointSchema),
  behavioral_insights: z.array(BehavioralInsightSchema),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: z.any().optional(),
})

export type BehavioralInsightDto = z.infer<typeof BehavioralInsightSchema>
export type MonthlyChartPointDto = z.infer<typeof MonthlyChartPointSchema>
export type CategoryChartPointDto = z.infer<typeof CategoryChartPointSchema>
export type OverviewResponseDto = z.infer<typeof OverviewResponseSchema>