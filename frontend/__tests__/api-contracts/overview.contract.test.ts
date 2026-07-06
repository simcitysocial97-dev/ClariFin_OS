import { describe, it, expect } from 'vitest'

describe('GET /api/overview contract', () => {
  it('returns an object with required fields', async () => {
    const response = await fetch('/api/overview')
    const data = await response.json()

    expect(data).toHaveProperty('total_spend')
    expect(data).toHaveProperty('this_month')
    expect(data).toHaveProperty('last_month')
    expect(data).toHaveProperty('transaction_count')
    expect(data).toHaveProperty('monthly_chart')
    expect(data).toHaveProperty('category_chart')
    expect(data).toHaveProperty('bank_chart')
  })

  it('display fields are strings with ₹ symbol', async () => {
    const response = await fetch('/api/overview')
    const data = await response.json()

    expect(data.total_spend_display).toMatch(/^₹/)
    expect(data.this_month_display).toMatch(/^₹/)
    expect(data.last_month_display).toMatch(/^₹/)
  })
})