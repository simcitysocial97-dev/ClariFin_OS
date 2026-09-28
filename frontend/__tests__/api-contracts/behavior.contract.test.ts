import { describe, it, expect } from 'vitest'

describe('GET /api/v1/behaviour/wellness-score contract', () => {
  it('returns wellness score response with required fields', async () => {
    const response = await fetch('/api/v1/behaviour/wellness-score')
    const data = await response.json()

    expect(data).toHaveProperty('score')
    expect(typeof data.score).toBe('number')
    expect(data.score).toBeGreaterThanOrEqual(0)
    expect(data.score).toBeLessThanOrEqual(100)
    expect(data).toHaveProperty('band')
    expect(['Excellent', 'Healthy', 'Developing', 'Risk', 'Critical']).toContain(data.band)
    expect(data).toHaveProperty('components')
    expect(typeof data.components).toBe('object')
    expect(data).toHaveProperty('snapshot_date')
    expect(data).toHaveProperty('version')
    expect(Number.isInteger(data.version)).toBe(true)
  })

  it('components has wellness sub-scores', async () => {
    const response = await fetch('/api/v1/behaviour/wellness-score')
    const data = await response.json()

    expect(data.components).toHaveProperty('cashflow_health')
    expect(data.components).toHaveProperty('savings_behaviour')
    expect(data.components).toHaveProperty('resilience')
  })

  it('optional legacy fields are present for backward compat', async () => {
    const response = await fetch('/api/v1/behaviour/wellness-score')
    const data = await response.json()

    // financial_health_score as alias for score
    if (data.financial_health_score !== undefined) {
      expect(data.financial_health_score).toBeGreaterThanOrEqual(0)
      expect(data.financial_health_score).toBeLessThanOrEqual(100)
    }
  })
})
