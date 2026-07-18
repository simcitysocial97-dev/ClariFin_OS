/**
 * Overview Model - Domain-friendly ViewModel for UI consumption
 *
 * IMPORTANT: This model contains only raw numeric values and UI flags.
 * Formatting is handled by components using formatINR() etc.
 * This keeps the mapper pure and presentation-agnostic.
 */

import type { Explanation } from '@/lib/explainability'

/**
 * Behavioral insight for UI consumption
 */
export interface BehavioralInsightModel {
  title: string
  description: string
  severity: 'warning' | 'positive' | 'neutral'
  icon: string
}

/**
 * Monthly chart point for UI consumption
 */
export interface MonthlyChartPointModel {
  month: string
  amount: number
}

/**
 * Category chart point for UI consumption
 */
export interface CategoryChartPointModel {
  name: string
  value: number
}

/**
 * Overview response for UI consumption
 */
export interface OverviewModel {
  totalSpend: number
  totalSpendDisplay: string
  thisMonth: number
  thisMonthDisplay: string
  lastMonth: number
  lastMonthDisplay: string
  monthChange: string
  transactionCount: number
  cardCount: number
  monthsOfData: number
  monthlyAverage: number
  monthlyAverageDisplay: string
  aboveBelowAvg: string
  aboveAvgIsBad: boolean
  monthlyChart: MonthlyChartPointModel[]
  categoryChart: CategoryChartPointModel[]
  behavioralInsights: BehavioralInsightModel[]
  isPartial: boolean
  partialReason: string | null
  lastUpdated: string | null
  explanation: Explanation | null
}