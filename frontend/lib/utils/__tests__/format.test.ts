import { describe, it, expect } from 'vitest'
import { formatINR, formatINRCompact, rupeesToPaise, paiseToRupees } from '../format'

describe('formatINR', () => {
  describe('correct paise-to-rupees conversion', () => {
    it('converts 100 paise to ₹1.00', () => {
      expect(formatINR(100)).toBe('₹1.00')
    })

    it('converts 50000 paise to ₹500.00', () => {
      expect(formatINR(50000)).toBe('₹500.00')
    })

    it('converts 100000 paise to ₹1,000.00', () => {
      expect(formatINR(100000)).toBe('₹1,000.00')
    })

    it('converts 10000000 paise to ₹1,00,000.00 (Indian number format)', () => {
      expect(formatINR(10000000)).toBe('₹1,00,000.00')
    })
  })

  describe('edge cases', () => {
    it('handles zero', () => {
      expect(formatINR(0)).toBe('₹0.00')
    })

    it('handles null gracefully', () => {
      expect(formatINR(null)).toBe('₹0.00')
    })

    it('handles undefined gracefully', () => {
      expect(formatINR(undefined)).toBe('₹0.00')
    })

    it('handles negative values', () => {
      expect(formatINR(-50000)).toBe('-₹500.00')
    })

    it('handles fractional paise (rounds correctly)', () => {
      // 50050 paise = 500.50 rupees
      expect(formatINR(50050)).toBe('₹500.50')
    })
  })

  describe('does NOT accept rupees input', () => {
    it('treats 500 as 500 paise = ₹5.00 (documents paise-first convention)', () => {
      expect(formatINR(500)).toBe('₹5.00')
    })
  })
})

describe('formatINRCompact', () => {
  it('formats thousands as K', () => {
    // 100000 paise = ₹1,000 = ₹1.0K
    expect(formatINRCompact(100000)).toBe('₹1.0K')
  })

  it('formats lakhs correctly', () => {
    // 10000000 paise = ₹1,00,000 = ₹1.0L
    expect(formatINRCompact(10000000)).toBe('₹1.0L')
  })

  it('handles null gracefully', () => {
    expect(formatINRCompact(null)).toBe('—')
  })

  it('handles undefined gracefully', () => {
    expect(formatINRCompact(undefined)).toBe('—')
  })

  it('returns full format for small amounts', () => {
    expect(formatINRCompact(50000)).toBe('₹500.00')
  })
})

describe('rupeesToPaise', () => {
  it('converts rupees to paise', () => {
    expect(rupeesToPaise(123.45)).toBe(12345)
  })

  it('converts whole rupees to paise', () => {
    expect(rupeesToPaise(100)).toBe(10000)
  })

  it('uses Math.round for floating point precision', () => {
    expect(rupeesToPaise(100.005)).toBe(10001)
  })
})

describe('paiseToRupees', () => {
  it('converts paise to rupees', () => {
    expect(paiseToRupees(12345)).toBe(123.45)
  })

  it('converts whole paise to rupees', () => {
    expect(paiseToRupees(10000)).toBe(100)
  })
})