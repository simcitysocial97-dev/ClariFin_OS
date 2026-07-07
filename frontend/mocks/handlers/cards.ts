import { http, HttpResponse } from 'msw'

const mockCardsResponse = {
  cards: [
    {
      card_id: 'HDFC_1234',
      bank: 'HDFC',
      card_last4: '1234',
      credit_limit: 100000.0,
      current_outstanding: 45000.0,
      minimum_due: 1350.0,
      payment_due_date: '2025-01-15',
      statement_date: '2025-01-05',
      bill_cycle_start: '2024-12-06',
      bill_cycle_end: '2025-01-05',
      utilization_percent: 45.0,
      days_until_due: 12,
      payment_status: 'on_track',
      validation_status: 'exact_match',
      statement_count: 8,
      latest_statement_id: 42,
    },
    {
      card_id: 'ICICI_5678',
      bank: 'ICICI',
      card_last4: '5678',
      credit_limit: 150000.0,
      current_outstanding: 120000.0,
      minimum_due: 3600.0,
      payment_due_date: '2025-01-08',
      statement_date: '2025-01-01',
      bill_cycle_start: '2024-12-01',
      bill_cycle_end: '2024-12-31',
      utilization_percent: 80.0,
      days_until_due: 2,
      payment_status: 'due_soon',
      validation_status: 'close_match',
      statement_count: 5,
      latest_statement_id: 38,
    },
  ],
  total_cards: 2,
  total_outstanding: 165000.0,
  total_credit_limit: 250000.0,
  total_utilization_percent: 66.0,
}

export const cardHandlers = [
  http.get('/api/cards', () => {
    return HttpResponse.json(mockCardsResponse)
  }),
]