import { describe, it, expect } from 'vitest'

describe('GET /api/cashflow/monthly contract', () => {
  it('returns months array with required fields', async () => {
    const response = await fetch('/api/cashflow/monthly')
    const data = await response.json()

    expect(data).toHaveProperty('months')
    expect(Array.isArray(data.months)).toBe(true)
    expect(data).toHaveProperty('total_income_paise')
    expect(data).toHaveProperty('total_expense_paise')
    expect(data).toHaveProperty('total_net_paise')
  })

  it('each month has required fields in paise', async () => {
    const response = await fetch('/api/cashflow/monthly')
    const data = await response.json()

    const month = data.months[0]
    expect(month).toHaveProperty('month_key')
    expect(month).toHaveProperty('month_label')
    expect(month).toHaveProperty('income_paise')
    expect(month).toHaveProperty('expense_paise')
    expect(month).toHaveProperty('net_paise')
  })

  it('all monetary values are integers (paise convention)', async () => {
    const response = await fetch('/api/cashflow/monthly')
    const data = await response.json()

    data.months.forEach((month: { income_paise: number; expense_paise: number; net_paise: number }) => {
      expect(typeof month.income_paise).toBe('number')
      expect(Number.isInteger(month.income_paise)).toBe(true)
      expect(typeof month.expense_paise).toBe('number')
      expect(Number.isInteger(month.expense_paise)).toBe(true)
      expect(typeof month.net_paise).toBe('number')
      expect(Number.isInteger(month.net_paise)).toBe(true)
    })
  })

  it('months are in ascending order', async () => {
    const response = await fetch('/api/cashflow/monthly')
    const data = await response.json()

    const keys = data.months.map((m: { month_key: string }) => m.month_key)
    const sorted = [...keys].sort()
    expect(keys).toEqual(sorted)
  })
})