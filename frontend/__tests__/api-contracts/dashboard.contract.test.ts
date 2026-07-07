import { describe, it, expect } from 'vitest'

describe('GET /api/dashboard/summary contract', () => {
  it('returns an object with required fields', async () => {
    const response = await fetch('/api/dashboard/summary')
    const data = await response.json()

    expect(data).toHaveProperty('net_cash_flow_paise')
    expect(data).toHaveProperty('savings_rate')
    expect(data).toHaveProperty('emi_ratio')
    expect(data).toHaveProperty('buffer_days')
    expect(data).toHaveProperty('financial_health_score')
    expect(data).toHaveProperty('recent_transactions')
  })

  it('numeric fields are numbers', async () => {
    const response = await fetch('/api/dashboard/summary')
    const data = await response.json()

    expect(typeof data.net_cash_flow_paise).toBe('number')
    expect(typeof data.savings_rate).toBe('number')
    expect(typeof data.emi_ratio).toBe('number')
    expect(typeof data.buffer_days).toBe('number')
    expect(typeof data.financial_health_score).toBe('number')
  })

  it('net_cash_flow_paise is an integer (paise convention)', async () => {
    const response = await fetch('/api/dashboard/summary')
    const data = await response.json()

    expect(Number.isInteger(data.net_cash_flow_paise)).toBe(true)
  })
})
