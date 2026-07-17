/**
 * NetWorth Mapper Tests
 *
 * Tests pure transformation correctness without React rendering.
 */

import { describe, it, expect } from 'vitest'
import { mapNetworthToModel } from '../networth'

describe('mapNetworthToModel', () => {
  const validDto = {
    net_worth_paise: 12500000,
    assets: {
      total_paise: 15000000,
      accounts_paise: 10000000,
      investments_paise: 5000000,
      account_count: 3,
      investment_count: 2,
    },
    liabilities: {
      total_paise: 2500000,
      loans_paise: 2000000,
      cards_paise: 500000,
      loan_count: 1,
      card_count: 1,
    },
    is_partial: false,
    partial_reason: null,
    last_updated: null,
  }

  it('transforms DTO to Model with correct values', () => {
    const result = mapNetworthToModel(validDto)

    // Core values
    expect(result.netWorthPaise).toBe(12500000)
    expect(result.assetsTotalPaise).toBe(15000000)
    expect(result.assetsAccountsPaise).toBe(10000000)
    expect(result.assetsInvestmentsPaise).toBe(5000000)
    expect(result.liabilitiesTotalPaise).toBe(2500000)
    expect(result.liabilitiesLoansPaise).toBe(2000000)
    expect(result.liabilitiesCardsPaise).toBe(500000)
  })

  it('transforms counts correctly', () => {
    const result = mapNetworthToModel(validDto)

    expect(result.accountCount).toBe(3)
    expect(result.investmentCount).toBe(2)
    expect(result.loanCount).toBe(1)
    expect(result.cardCount).toBe(1)
  })

  it('derives trend as up when assets > liabilities', () => {
    const result = mapNetworthToModel(validDto)
    expect(result.trend).toBe('up')
  })

  it('derives trend as down when assets < liabilities', () => {
    const dtoDown = {
      ...validDto,
      net_worth_paise: -500000,
      assets: { ...validDto.assets, total_paise: 2000000 },
      liabilities: { ...validDto.liabilities, total_paise: 2500000 },
    }
    const result = mapNetworthToModel(dtoDown)
    expect(result.trend).toBe('down')
  })

  it('derives trend as flat when assets equal liabilities', () => {
    const dtoFlat = {
      ...validDto,
      net_worth_paise: 0,
      assets: { ...validDto.assets, total_paise: 10000000 },
      liabilities: { ...validDto.liabilities, total_paise: 10000000 },
    }
    const result = mapNetworthToModel(dtoFlat)
    expect(result.trend).toBe('flat')
  })

  it('preserves isPartial flag', () => {
    const result = mapNetworthToModel(validDto)
    expect(result.isPartial).toBe(false)
  })

  it('preserves partialReason', () => {
    const dtoWithReason = {
      ...validDto,
      is_partial: true,
      partial_reason: 'Missing account data',
    }
    const result = mapNetworthToModel(dtoWithReason)
    expect(result.isPartial).toBe(true)
    expect(result.partialReason).toBe('Missing account data')
  })

  it('is deterministic - same input produces same output', () => {
    const result1 = mapNetworthToModel(validDto)
    const result2 = mapNetworthToModel(validDto)

    expect(result1).toEqual(result2)
    expect(result1).toStrictEqual(result2)
  })

  it('handles zero values correctly', () => {
    const zeroDto = {
      net_worth_paise: 0,
      assets: {
        total_paise: 0,
        accounts_paise: 0,
        investments_paise: 0,
        account_count: 0,
        investment_count: 0,
      },
      liabilities: {
        total_paise: 0,
        loans_paise: 0,
        cards_paise: 0,
        loan_count: 0,
        card_count: 0,
      },
      is_partial: true,
      partial_reason: 'No financial data',
      last_updated: null,
    }
    const result = mapNetworthToModel(zeroDto)

    expect(result.netWorthPaise).toBe(0)
    expect(result.trend).toBe('flat')
    expect(result.isPartial).toBe(true)
  })

  it('handles negative net worth correctly', () => {
    const negativeDto = {
      ...validDto,
      net_worth_paise: -100000,
      assets: { ...validDto.assets, total_paise: 2000000 },
      liabilities: { ...validDto.liabilities, total_paise: 2100000 },
    }
    const result = mapNetworthToModel(negativeDto)

    expect(result.netWorthPaise).toBe(-100000)
    expect(result.trend).toBe('down')
  })
})