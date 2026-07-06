import { describe, it, expect } from 'vitest'

describe('GET /api/banks contract', () => {
  it('returns an object with banks array', async () => {
    const response = await fetch('/api/banks')
    const data = await response.json()

    expect(data).toHaveProperty('banks')
    expect(Array.isArray(data.banks)).toBe(true)
  })

  it('banks array contains strings', async () => {
    const response = await fetch('/api/banks')
    const data = await response.json()

    data.banks.forEach((bank: any) => {
      expect(typeof bank).toBe('string')
    })
  })
})