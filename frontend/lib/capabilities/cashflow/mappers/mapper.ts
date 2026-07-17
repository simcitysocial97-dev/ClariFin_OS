/**
 * Cashflow Mapper - Pure transformation from DTO to Model
 *
 * This mapper transforms raw API responses to domain-friendly models.
 * It is deterministic, side-effect free, and fully typed.
 */

import type { CashflowResponseDto, CashflowMonthDto } from '../contracts/api'
import type { CashflowModel, CashflowMonthModel } from '../models/model'

/**
 * Map CashflowMonth DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 */
export function mapCashflowMonthToModel(dto: CashflowMonthDto): CashflowMonthModel {
  return {
    monthKey: dto.month_key,
    monthLabel: dto.month_label,
    incomePaise: dto.income_paise,
    expensePaise: dto.expense_paise,
    netPaise: dto.net_paise,
    transactionCount: dto.transaction_count,
  }
}

/**
 * Map Cashflow DTO to Model
 *
 * Transformation rules:
 * - Flatten nested structure for easier component access
 * - Rename fields to camelCase for consistency
 */
export function mapCashflowDtoToModel(dto: CashflowResponseDto): CashflowModel {
  return {
    months: dto.months.map(mapCashflowMonthToModel),
    periodMonths: dto.period_months,
    totalIncomePaise: dto.total_income_paise,
    totalExpensePaise: dto.total_expense_paise,
    totalNetPaise: dto.total_net_paise,
  }
}

// Re-export types for convenience
export type { CashflowModel, CashflowMonthModel }