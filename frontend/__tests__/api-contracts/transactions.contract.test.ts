import { describe, it, expect } from 'vitest'

describe('GET /api/transactions contract', () => {
  it('returns a wrapped response with transactions array and total', async () => {
    const response = await fetch('/api/transactions')
    const data = await response.json()

    expect(data).toHaveProperty('transactions')
    expect(Array.isArray(data.transactions)).toBe(true)
    expect(data).toHaveProperty('total')
    expect(typeof data.total).toBe('number')
    expect(Number.isInteger(data.total)).toBe(true)
  })

  it('each transaction has required canonical fields', async () => {
    const response = await fetch('/api/transactions')
    const data = await response.json()

    const tx = data.transactions[0]
    expect(tx).toHaveProperty('id')
    expect(tx).toHaveProperty('date')
    expect(tx).toHaveProperty('description')
    expect(tx).toHaveProperty('type')
    expect(['debit', 'credit']).toContain(tx.type)
    expect(tx).toHaveProperty('category')
    expect(typeof tx.category).toBe('string')
    expect(tx).toHaveProperty('bank')
  })

  it('amount uses canonical MoneyDTO with paise integer', async () => {
    const response = await fetch('/api/transactions')
    const data = await response.json()

    data.transactions.forEach((tx: { amount: { paise: number } }) => {
      expect(tx.amount).toBeDefined()
      expect(tx.amount.paise).toBeDefined()
      expect(Number.isInteger(tx.amount.paise)).toBe(true)
    })
  })
})
