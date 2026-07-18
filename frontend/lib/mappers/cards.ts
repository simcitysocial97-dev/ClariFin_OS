/**
 * Credit Cards Mapper - Pure transformation from DTO to Model
 *
 * This mapper transforms raw API responses to domain-friendly models.
 * It is deterministic, side-effect free, and fully typed.
 *
 * IMPORTANT: The explanation is PRESERVED from the backend, not generated.
 * The backend is the source of truth for all explainability data.
 */

import type { CreditCardsDto, CreditCardSummaryDto } from '../contracts/api/cards'
import type { CreditCardsModel, CreditCardSummaryModel } from '../models/cards'

/**
 * Map CreditCardSummary DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 */
export function mapCreditCardSummaryToModel(dto: CreditCardSummaryDto): CreditCardSummaryModel {
  return {
    cardId: dto.card_id,
    bank: dto.bank,
    cardLast4: dto.card_last4,
    creditLimitPaise: dto.credit_limit_paise,
    currentOutstandingPaise: dto.current_outstanding_paise,
    minimumDuePaise: dto.minimum_due_paise,
    utilizationBps: dto.utilization_bps,
    isActive: dto.is_active,
  }
}

/**
 * Map CreditCards DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 * - Preserve explanation unchanged
 */
export function mapCreditCardsToModel(dto: CreditCardsDto): CreditCardsModel {
  return {
    cards: dto.cards.map(mapCreditCardSummaryToModel),
    totalOutstandingPaise: dto.total_outstanding_paise,
    totalCreditLimitPaise: dto.total_credit_limit_paise,
    totalUtilizationBps: dto.total_utilization_bps,
    isPartial: dto.is_partial,
    partialReason: dto.partial_reason,
    lastUpdated: dto.last_updated,
    explanation: dto.explanation ?? null,
  }
}

// Re-export types for convenience
export type { CreditCardsModel, CreditCardSummaryModel }