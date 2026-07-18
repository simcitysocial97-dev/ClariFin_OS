import { useAsyncQuery, HookState } from './use-async-query'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

// Types based on /api/cards response
export interface CardSummary {
  card_id: string
  bank: string
  card_last4: string
  credit_limit: number  // In paise (canonical)
  current_outstanding: number  // In paise (canonical)
  minimum_due: number  // In paise (canonical)
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
  total_outstanding: number  // In paise (canonical)
  total_credit_limit: number  // In paise (canonical)
  total_utilization_percent: number
}

// Convert rupees to paise at the hook boundary
function rupeesToPaise(rupees: number): number {
  return Math.round(rupees * 100)
}

async function fetchCards(): Promise<CardsData> {
  const response = await fetch(`${API_BASE}/api/cards`)
  if (!response.ok) throw new Error(`Cards fetch failed: ${response.status}`)
  const raw = await response.json()
  
  // Convert all monetary values from rupees to paise (canonical)
  const cards = (raw.cards || []).map((card: any) => ({
    ...card,
    credit_limit: rupeesToPaise(card.credit_limit || 0),
    current_outstanding: rupeesToPaise(card.current_outstanding || 0),
    minimum_due: rupeesToPaise(card.minimum_due || 0),
  }))
  
  return {
    ...raw,
    cards,
    total_outstanding: rupeesToPaise(raw.total_outstanding || 0),
    total_credit_limit: rupeesToPaise(raw.total_credit_limit || 0),
  }
}

export function useCards(): HookState<CardsData> {
  return useAsyncQuery(
    ['cards'],
    fetchCards
  )
}