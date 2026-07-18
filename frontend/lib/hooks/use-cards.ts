import { useAppQuery } from '@/lib/query'
import { queryKeys } from '@/lib/query'
import { STALE_TIME } from '@/lib/query'
import { CreditCardsResponseSchema } from '../contracts/api/cards'
import { mapCreditCardsToModel } from '../mappers/cards'
import type { CreditCardsModel } from '../models/cards'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

// Types based on /api/v1/credit-cards response
export interface CardSummary {
  card_id: string
  bank: string
  card_last4: string
  credit_limit: number
  current_outstanding: number
  minimum_due: number
  payment_due_date: string | null
  statement_date: string | null
  bill_cycle_start: string | null
  bill_cycle_end: string | null
  utilization_percent: number
  days_until_due: number | null
  payment_status: 'due_soon' | 'upcoming' | 'on_track' | 'overdue' | 'unknown'
  validation_status: string
  statement_count: number
  latest_statement_id: number
}

export interface CardsData {
  cards: CardSummary[]
  total_cards: number
  total_outstanding: number
  total_credit_limit: number
  total_utilization_percent: number
}

async function fetchCards(): Promise<CreditCardsModel> {
  const response = await fetch(`${API_BASE}/api/v1/credit-cards`)
  if (!response.ok) throw new Error(`Cards fetch failed: ${response.status}`)
  const dto = CreditCardsResponseSchema.parse(await response.json())
  return mapCreditCardsToModel(dto)
}

export function useCards() {
  return useAppQuery({
    queryKey: queryKeys.cards.list(),
    queryFn: fetchCards,
    capability: 'cards',
    staleTime: STALE_TIME.NORMAL,
  })
}