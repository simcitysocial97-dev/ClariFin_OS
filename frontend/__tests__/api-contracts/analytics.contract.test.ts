import { describe, it, expect } from 'vitest'

describe('GET /api/analytics contract', () => {
  it('returns an object with required fields', async () => {
    const response = await fetch('/api/analytics')
    const data = await response.json()

    expect(data).toHaveProperty('highest_month')
    expect(data).toHaveProperty('highest_month_amount')
    expect(data).toHaveProperty('avg_monthly')
    expect(data).toHaveProperty('unique_merchants')
    expect(data).toHaveProperty('top_merchants')
    expect(data).toHaveProperty('recurring_charges')
    expect(data).toHaveProperty('largest_transactions')
  })

  it('highest_month_amount is a string with ₹ symbol', async () => {
    const response = await fetch('/api/analytics')
    const data = await response.json()

    expect(data.highest_month_amount).toMatch(/^₹/)
  })

  it('top_merchants array has correct structure', async () => {
    const response = await fetch('/api/analytics')
    const data = await response.json()

    if (data.top_merchants.length > 0) {
      const merchant = data.top_merchants[0]
      expect(merchant).toHaveProperty('merchant')
      expect(merchant).toHaveProperty('amount_display')
      expect(merchant).toHaveProperty('count')
    }
  })

  it('recurring_charges array has correct structure', async () => {
    const response = await fetch('/api/analytics')
    const data = await response.json()

    if (data.recurring_charges.length > 0) {
      const charge = data.recurring_charges[0]
      expect(charge).toHaveProperty('description')
      expect(charge).toHaveProperty('frequency')
      expect(charge).toHaveProperty('avg_display')
      expect(charge).toHaveProperty('annual_display')
    }
  })

  it('unique_merchants is a positive integer', async () => {
    const response = await fetch('/api/analytics')
    const data = await response.json()

    expect(Number.isInteger(data.unique_merchants)).toBe(true)
    expect(data.unique_merchants).toBeGreaterThanOrEqual(0)
  })
})