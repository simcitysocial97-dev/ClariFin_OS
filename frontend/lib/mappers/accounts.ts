/**
 * Accounts Mapper - Pure transformation from DTO to Model
 *
 * This mapper transforms raw API responses to domain-friendly models.
 * It is deterministic, side-effect free, and fully typed.
 *
 * IMPORTANT: The explanation is PRESERVED from the backend, not generated.
 * The backend is the source of truth for all explainability data.
 */

import type { AccountsDto, AccountSummaryDto } from '../contracts/api/accounts'
import type { AccountsModel, AccountSummaryModel } from '../models/accounts'

/**
 * Map AccountSummary DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 */
export function mapAccountSummaryToModel(dto: AccountSummaryDto): AccountSummaryModel {
  return {
    accountId: dto.account_id,
    name: dto.name,
    bank: dto.bank,
    accountType: dto.account_type,
    balancePaise: dto.balance_paise,
    averageBalancePaise: dto.average_balance_paise,
    trend: dto.trend,
    velocityPaisePerDay: dto.velocity_paise_per_day,
    isActive: dto.is_active,
  }
}

/**
 * Map Accounts DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 * - Preserve explanation unchanged
 */
export function mapAccountsToModel(dto: AccountsDto): AccountsModel {
  return {
    accounts: dto.accounts.map(mapAccountSummaryToModel),
    totalBalancePaise: dto.total_balance_paise,
    isPartial: dto.is_partial,
    partialReason: dto.partial_reason,
    lastUpdated: dto.last_updated,
    explanation: dto.explanation ?? null,
  }
}

// Re-export types for convenience
export type { AccountsModel, AccountSummaryModel }