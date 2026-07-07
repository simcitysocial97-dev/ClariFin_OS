import { describe, it, expect } from 'vitest'

describe('GET /api/reconciliations contract', () => {
  it('returns an object with reconciliations array', async () => {
    const response = await fetch('/api/reconciliations')
    const data = await response.json()

    expect(data).toHaveProperty('reconciliations')
    expect(Array.isArray(data.reconciliations)).toBe(true)
  })

  it('each reconciliation has required fields', async () => {
    const response = await fetch('/api/reconciliations')
    const data = await response.json()

    const rec = data.reconciliations[0]
    expect(rec).toHaveProperty('id')
    expect(rec).toHaveProperty('debit_txn_id')
    expect(rec).toHaveProperty('credit_txn_id')
    expect(rec).toHaveProperty('debit_account_id')
    expect(rec).toHaveProperty('credit_account_id')
    expect(rec).toHaveProperty('amount')
    expect(rec).toHaveProperty('date_diff_days')
    expect(rec).toHaveProperty('match_confidence')
    expect(rec).toHaveProperty('match_type')
    expect(rec).toHaveProperty('status')
  })

  it('each reconciliation has transaction details', async () => {
    const response = await fetch('/api/reconciliations')
    const data = await response.json()

    const rec = data.reconciliations[0]
    // Debit transaction details
    expect(rec).toHaveProperty('debit_date')
    expect(rec).toHaveProperty('debit_date_iso')
    expect(rec).toHaveProperty('debit_description')
    expect(rec).toHaveProperty('debit_amount_paise')
    expect(rec).toHaveProperty('debit_bank')
    // Credit transaction details
    expect(rec).toHaveProperty('credit_date')
    expect(rec).toHaveProperty('credit_date_iso')
    expect(rec).toHaveProperty('credit_description')
    expect(rec).toHaveProperty('credit_amount_paise')
    expect(rec).toHaveProperty('credit_bank')
  })

  it('match_confidence is between 0 and 1', async () => {
    const response = await fetch('/api/reconciliations')
    const data = await response.json()

    for (const rec of data.reconciliations) {
      expect(rec.match_confidence).toBeGreaterThanOrEqual(0)
      expect(rec.match_confidence).toBeLessThanOrEqual(1)
    }
  })

  it('match_type is valid', async () => {
    const response = await fetch('/api/reconciliations')
    const data = await response.json()

    const validTypes = ['exact', 'window', 'fuzzy', 'manual']
    for (const rec of data.reconciliations) {
      expect(validTypes).toContain(rec.match_type)
    }
  })

  it('status is valid', async () => {
    const response = await fetch('/api/reconciliations')
    const data = await response.json()

    const validStatuses = ['pending', 'confirmed', 'rejected']
    for (const rec of data.reconciliations) {
      expect(validStatuses).toContain(rec.status)
    }
  })
})

describe('GET /api/reconciliations/pending contract', () => {
  it('returns only pending reconciliations', async () => {
    const response = await fetch('/api/reconciliations/pending')
    const data = await response.json()

    for (const rec of data.reconciliations) {
      expect(rec.status).toBe('pending')
    }
  })
})

describe('GET /api/reconciliations/scan contract', () => {
  it('returns matches array and count', async () => {
    const response = await fetch('/api/reconciliations/scan')
    const data = await response.json()

    expect(data).toHaveProperty('matches')
    expect(Array.isArray(data.matches)).toBe(true)
    expect(data).toHaveProperty('count')
    expect(typeof data.count).toBe('number')
  })

  it('each match has required fields', async () => {
    const response = await fetch('/api/reconciliations/scan')
    const data = await response.json()

    const match = data.matches[0]
    expect(match).toHaveProperty('debit_txn_id')
    expect(match).toHaveProperty('credit_txn_id')
    expect(match).toHaveProperty('amount')
    expect(match).toHaveProperty('match_confidence')
    expect(match).toHaveProperty('match_type')
  })
})