/**
 * Accounts Mapper - Pure transformation from DTO to Model
 *
 * This mapper transforms raw API responses to domain-friendly models.
 * It is deterministic, side-effect free, and fully typed.
 */

import type { AccountsResponseDto, AccountDto } from '../contracts/api'
import type { AccountsModel, AccountModel } from '../models/model'

/**
 * Map Account DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 */
export function mapAccountToModel(dto: AccountDto): AccountModel {
  return {
    id: dto.id,
    name: dto.name,
    bank: dto.bank,
    accountType: dto.account_type,
    balancePaise: dto.balance_paise,
    accountNumberLast4: dto.account_number_last4,
    isActive: dto.is_active,
    notes: dto.notes,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  }
}

/**
 * Map Accounts DTO to Model
 *
 * Transformation rules:
 * - Map each account to ViewModel
 * - Rename fields to camelCase for consistency
 */
export function mapAccountsDtoToModel(dto: AccountsResponseDto): AccountsModel {
  return {
    accounts: dto.accounts.map(mapAccountToModel),
    total: dto.total,
  }
}

// Re-export types for convenience
export type { AccountsModel, AccountModel }