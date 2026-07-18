/**
 * Overview Mapper - Pure transformation from DTO to Model
 *
 * This mapper transforms raw API responses to domain-friendly models.
 * It is deterministic, side-effect free, and fully typed.
 *
 * IMPORTANT: The explanation is PRESERVED from the backend, not generated.
 * The backend is the source of truth for all explainability data.
 */

import type { OverviewResponseDto } from '../contracts/api'
import type { OverviewModel } from '../models/model'

/**
 * Map Overview DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 * - Preserve explanation unchanged
 */
export function mapOverviewDtoToModel(dto: OverviewResponseDto): OverviewModel {
  return {
    totalSpend: dto.total_spend,
    totalSpendDisplay: dto.total_spend_display,
    thisMonth: dto.this_month,
    thisMonthDisplay: dto.this_month_display,
    lastMonth: dto.last_month,
    lastMonthDisplay: dto.last_month_display,
    monthChange: dto.month_change,
    transactionCount: dto.transaction_count,
    cardCount: dto.card_count,
    monthsOfData: dto.months_of_data,
    monthlyAverage: dto.monthly_average,
    monthlyAverageDisplay: dto.monthly_average_display,
    aboveBelowAvg: dto.above_below_avg,
    aboveAvgIsBad: dto.above_avg_is_bad,
    monthlyChart: dto.monthly_chart.map((p) => ({
      month: p.month,
      amount: p.amount,
    })),
    categoryChart: dto.category_chart.map((p) => ({
      name: p.name,
      value: p.value,
    })),
    behavioralInsights: dto.behavioral_insights.map((i) => ({
      title: i.title,
      description: i.description,
      severity: i.severity,
      icon: i.icon,
    })),
    isPartial: dto.is_partial,
    partialReason: dto.partial_reason,
    lastUpdated: dto.last_updated,
    explanation: dto.explanation ?? null,
  }
}

// Re-export types for convenience
export type { OverviewModel }