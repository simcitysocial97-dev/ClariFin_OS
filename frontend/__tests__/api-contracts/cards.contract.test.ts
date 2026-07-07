import { describe, it, expect } from 'vitest'

describe('GET /api/cards contract', () => {
  it('returns an object with cards array', async () => {
    const response = await fetch('/api/cards')
    const data = await response.json()

    expect(data).toHaveProperty('cards')
    expect(Array.isArray(data.cards)).toBe(true)
  })

  it('each card has required fields', async () => {
    const response = await fetch('/api/cards')
    const data = await response.json()

    const card = data.cards[0]
    expect(card).toHaveProperty('card_id')
    expect(card).toHaveProperty('bank')
    expect(card).toHaveProperty('card_last4')
    expect(card).toHaveProperty('credit_limit')
    expect(card).toHaveProperty('current_outstanding')
    expect(card).toHaveProperty('minimum_due')
    expect(card).toHaveProperty('payment_due_date')
    expect(card).toHaveProperty('statement_date')
    expect(card).toHaveProperty('bill_cycle_start')
    expect(card).toHaveProperty('bill_cycle_end')
    expect(card).toHaveProperty('utilization_percent')
    expect(card).toHaveProperty('days_until_due')
    expect(card).toHaveProperty('payment_status')
    expect(card).toHaveProperty('validation_status')
    expect(card).toHaveProperty('statement_count')
    expect(card).toHaveProperty('latest_statement_id')
  })

  it('utilization_percent is between 0-100', async () => {
    const response = await fetch('/api/cards')
    const data = await response.json()

    for (const card of data.cards) {
      expect(card.utilization_percent).toBeGreaterThanOrEqual(0)
      expect(card.utilization_percent).toBeLessThanOrEqual(100)
    }
  })

  it('days_until_due is a number or null', async () => {
    const response = await fetch('/api/cards')
    const data = await response.json()

    for (const card of data.cards) {
      expect(
        card.days_until_due === null || typeof card.days_until_due === 'number'
      ).toBe(true)
    }
  })

  it('monetary values are correct type', async () => {
    const response = await fetch('/api/cards')
    const data = await response.json()

    for (const card of data.cards) {
      expect(typeof card.credit_limit).toBe('number')
      expect(typeof card.current_outstanding).toBe('number')
      expect(typeof card.minimum_due).toBe('number')
    }
  })

  it('response has summary fields', async () => {
    const response = await fetch('/api/cards')
    const data = await response.json()

    expect(data).toHaveProperty('total_cards')
    expect(data).toHaveProperty('total_outstanding')
    expect(data).toHaveProperty('total_credit_limit')
    expect(data).toHaveProperty('total_utilization_percent')
  })
})