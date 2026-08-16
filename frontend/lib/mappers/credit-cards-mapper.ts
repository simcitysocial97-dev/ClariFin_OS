import type {
  CreditCardsViewModel,
  CreditCardSummaryViewModel,
  CreditCardFiltersViewModel,
  CreditCardNavigationViewModel,
} from '../../types/credit-cards-view-model';
import type { CardSummary } from '../schemas/cards'

/**
 * Credit Cards Mapper
 * Maps raw API response to CreditCardsViewModel.
 */
export interface ICreditCardsMapper {
  mapCreditCardsDTO(raw: Record<string, unknown>): CreditCardsViewModel
  mapCreditCardSummary(dto: Record<string, unknown>): CardSummary
}

export class CreditCardsMapper implements ICreditCardsMapper {
  mapCreditCardsDTO(raw: Record<string, unknown>): CreditCardsViewModel {
    const cardsRaw = (raw.cards ?? []) as Record<string, unknown>[]
    const cards: CreditCardSummaryViewModel[] = cardsRaw.map(card => ({
      id: String(card.id ?? ''),
      name: String(card.name ?? card.bank ?? ''),
      bank: String(card.bank ?? ''),
      card_number_last4: String(card.card_number_last4 ?? card.card_last4 ?? ''),
      credit_limit_paise: Number(card.credit_limit_paise ?? 0),
      current_balance_paise: Number(card.current_balance_paise ?? card.current_outstanding ?? 0),
      available_paise: Number(card.available_paise ?? card.credit_limit_paise ?? 0),
      min_due_paise: Number(card.min_due_paise ?? card.minimum_due ?? 0),
      total_due_paise: Number(card.total_due_paise ?? 0),
      due_date: String(card.due_date ?? ''),
      status: (card.status ?? 'active') as 'active' | 'inactive' | 'closed',
      reward_points: Number(card.reward_points ?? 0),
    }))

    return {
      cards,
      total_balance_paise: Number(raw.total_outstanding ?? 0),
      total_due_paise: Number(raw.total_due ?? 0),
      total_available_paise: Number(raw.total_available ?? 0),
      card_count: cards.length,
      statements: [],
      utilization: [],
      spending: [],
      insights: [],
      filters: this.createDefaultFilters(),
      navigation: this.createDefaultNavigation(),
    }
  }

  mapCreditCardSummary(dto: Record<string, unknown>): CardSummary {
    return {
      card_id: String(dto.id ?? ''),
      bank: String(dto.bank ?? ''),
      card_last4: String(dto.card_number_last4 ?? dto.card_last4 ?? ''),
      credit_limit: Number(dto.credit_limit_paise ?? 0),
      current_outstanding: Number(dto.current_balance_paise ?? 0),
      minimum_due: Number(dto.min_due_paise ?? 0),
      payment_due_date: dto.due_date ? String(dto.due_date) : null,
      statement_date: dto.statement_date ? String(dto.statement_date) : null,
      bill_cycle_start: dto.bill_cycle_start ? String(dto.bill_cycle_start) : null,
      bill_cycle_end: dto.bill_cycle_end ? String(dto.bill_cycle_end) : null,
      utilization_percent: (Number(dto.available_paise ?? 0) && Number(dto.credit_limit_paise ?? 0))
        ? ((Number(dto.credit_limit_paise ?? 0) - Number(dto.available_paise ?? 0)) / Number(dto.credit_limit_paise ?? 1)) * 100
        : 0,
      days_until_due: dto.due_date
        ? Math.ceil((new Date(String(dto.due_date)).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
        : null,
      payment_status: dto.status === 'active' ? 'on_track' as const : 'unknown' as const,
      validation_status: 'valid' as const,
      statement_count: 0,
      latest_statement_id: 0,
    }
  }

  private createDefaultFilters(): CreditCardFiltersViewModel {
    return {}
  }

  private createDefaultNavigation(): CreditCardNavigationViewModel {
    return {
      deep_link: '/cards',
      cross_references: {
        net_worth: '/net-worth',
        accounts: '/accounts',
      },
    }
  }
}

export const creditCardsMapper = new CreditCardsMapper()
