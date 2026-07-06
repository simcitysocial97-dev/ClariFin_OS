import { describe, it, expect } from 'vitest'

describe('GET /api/transactions contract', () => {
  it('returns an object with transactions array and total count', async () => {
    const response = await fetch('/api/transactions')
    const data = await response.json()

    expect(data).toHaveProperty('transactions')
    expect(Array.isArray(data.transactions)).toBe(true)
    expect(data).toHaveProperty('total')
    expect(typeof data.total).toBe('number')
  })

  it('each transaction has required fields', async () => {
    const response = await fetch('/api/transactions')
    const data = await response.json()

    const tx = data.transactions[0]
    expect(tx).toHaveProperty('id')
    expect(tx).toHaveProperty('date')
    expect(tx).toHaveProperty('description')
    expect(tx).toHaveProperty('amount_paise')
    expect(typeof tx.amount_paise).toBe('number')
    expect(Number.isInteger(tx.amount_paise)).toBe(true)
  })

  it('amount_paise is always an integer (paise convention enforced)', async () => {
    const response = await fetch('/api/transactions')
    const data = await response.json()

    data.transactions.forEach((tx: any) => {
      expect(Number.isInteger(tx.amount_paise)).toBe(true)
    })
  })
})