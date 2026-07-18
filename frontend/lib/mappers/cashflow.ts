/**
 * Cashflow Mapper - Pure transformation from DTO to Model
 *
 * This mapper transforms raw API responses to domain-friendly models.
 * It is deterministic, side-effect free, and fully typed.
 */

import type { CashflowDto } from '../contracts/api/cashflow'
import type { CashflowModel } from '../models/cashflow'

/**
 * Map Cashflow DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 * - Preserve explanation unchanged
 */
export function mapCashflowToModel(dto: CashflowDto): CashflowModel {
  return {
    totalIncomePaise: dto.total_income_paise,
    totalExpensePaise: dto.total_expense_paise,
    totalNetPaise: dto.total_net_paise,
    isPartial: dto.is_partial,
    partialReason: dto.partial_reason,
    lastUpdated: dto.last_updated,
    explanation: dto.explanation ?? null,
  }
}