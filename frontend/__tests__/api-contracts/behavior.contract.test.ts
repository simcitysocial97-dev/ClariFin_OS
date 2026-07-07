import { describe, it, expect } from 'vitest'

describe('GET /api/behavior/score contract', () => {
  it('returns an object with required fields', async () => {
    const response = await fetch('/api/behavior/score')
    const data = await response.json()

    expect(data).toHaveProperty('financial_health_score')
    expect(data).toHaveProperty('confidence')
    expect(data).toHaveProperty('components')
    expect(data).toHaveProperty('risk_flags')
    expect(data).toHaveProperty('summary')
  })

  it('financial_health_score is between 0 and 100', async () => {
    const response = await fetch('/api/behavior/score')
    const data = await response.json()

    expect(data.financial_health_score).toBeGreaterThanOrEqual(0)
    expect(data.financial_health_score).toBeLessThanOrEqual(100)
  })

  it('components has all required scores', async () => {
    const response = await fetch('/api/behavior/score')
    const data = await response.json()

    expect(data.components).toHaveProperty('savings_discipline')
    expect(data.components).toHaveProperty('habit_stability')
    expect(data.components).toHaveProperty('impulsivity')
    expect(data.components).toHaveProperty('financial_stress')
    expect(data.components).toHaveProperty('loss_aversion')
  })

  it('risk_flags has all required flags', async () => {
    const response = await fetch('/api/behavior/score')
    const data = await response.json()

    expect(data.risk_flags).toHaveProperty('india_specific')
    expect(data.risk_flags).toHaveProperty('high_impulsivity')
    expect(data.risk_flags).toHaveProperty('high_stress')
    expect(data.risk_flags).toHaveProperty('low_savings')
  })
})

describe('GET /api/behavior/insights contract', () => {
  it('returns an object with required fields', async () => {
    const response = await fetch('/api/behavior/insights')
    const data = await response.json()

    expect(data).toHaveProperty('insights')
    expect(data).toHaveProperty('nudges')
    expect(data).toHaveProperty('summary')
    expect(data).toHaveProperty('financial_health_score')
  })

  it('insights array has correct structure', async () => {
    const response = await fetch('/api/behavior/insights')
    const data = await response.json()

    if (data.insights.length > 0) {
      const insight = data.insights[0]
      expect(insight).toHaveProperty('type')
      expect(insight).toHaveProperty('title')
      expect(insight).toHaveProperty('message')
      expect(insight).toHaveProperty('metric')
    }
  })
})