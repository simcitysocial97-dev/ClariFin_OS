import { describe, it, expect } from 'vitest'

describe('GET /api/v1/banks contract', () => {
  it('returns an object with banks array', async () => {
    const response = await fetch('/api/v1/banks')
    const data = await response.json()

    expect(data).toHaveProperty('banks')
    expect(Array.isArray(data.banks)).toBe(true)
  })

  it('banks array contains strings', async () => {
    const response = await fetch('/api/v1/banks')
    const data = await response.json()

    data.banks.forEach((bank: string) => {
      expect(typeof bank).toBe('string')
    })
  })
})