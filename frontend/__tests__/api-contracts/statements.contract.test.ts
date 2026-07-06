import { describe, it, expect } from 'vitest'

describe('GET /api/statements contract', () => {
  it('returns an array of statements', async () => {
    const response = await fetch('/api/statements')
    const data = await response.json()

    expect(Array.isArray(data)).toBe(true)
  })

  it('each statement has required fields', async () => {
    const response = await fetch('/api/statements')
    const data = await response.json()

    const stmt = data[0]
    expect(stmt).toHaveProperty('id')
    expect(stmt).toHaveProperty('bank')
    expect(stmt).toHaveProperty('file_name')
    expect(stmt).toHaveProperty('transaction_count')
    expect(stmt).toHaveProperty('total_debit')
    expect(stmt).toHaveProperty('total_credit')
    expect(stmt).toHaveProperty('validation_status')
  })
})