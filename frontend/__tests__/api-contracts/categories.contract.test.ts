import { describe, it, expect } from 'vitest'

describe('GET /api/categories/list contract', () => {
  it('returns an object with categories array', async () => {
    const response = await fetch('/api/categories/list')
    const data = await response.json()

    expect(data).toHaveProperty('categories')
    expect(Array.isArray(data.categories)).toBe(true)
  })

  it('categories array contains strings', async () => {
    const response = await fetch('/api/categories/list')
    const data = await response.json()

    data.categories.forEach((cat: string) => {
      expect(typeof cat).toBe('string')
    })
  })
})