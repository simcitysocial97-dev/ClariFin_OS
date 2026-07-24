import { z } from 'zod'

// Cards Schema
export const CardSummarySchema = z.object({
  card_id: z.string(),
  bank: z.string(),
  card_last4: z.string(),
  credit_limit: z.number().int(), // In paise (canonical)
  current_outstanding: z.number().int(), // In paise (canonical)
  minimum_due: z.number().int(), // In paise (canonical)
  payment_due_date: z.string().nullable(),
  statement_date: z.string().nullable(),
  bill_cycle_start: z.string().nullable(),
  bill_cycle_end: z.string().nullable(),
  utilization_percent: z.number(),
  days_until_due: z.number().int().nullable(),
  payment_status: z.enum(['due_soon', 'upcoming', 'on_track', 'overdue', 'unknown']),
  validation_status: z.string(),
  statement_count: z.number().int(),
  latest_statement_id: z.number().int(),
})

export const CardsDataSchema = z.object({
  cards: z.array(CardSummarySchema),
  total_cards: z.number().int(),
  total_outstanding: z.number().int(), // In paise (canonical)
  total_credit_limit: z.number().int(), // In paise (canonical)
  total_utilization_percent: z.number(),
})

export type CardSummary = z.infer<typeof CardSummarySchema>
export type CardsData = z.infer<typeof CardsDataSchema>