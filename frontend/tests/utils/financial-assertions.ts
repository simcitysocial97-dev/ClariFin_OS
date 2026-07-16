/**
 * Financial Assertion Utilities
 * ==============================
 * 
 * Domain-specific assertions for financial math validation:
 * - Ledger integrity checks
 * - Net cashflow validation
 * - Credit utilization calculations
 * - Risk score delta verification
 */

import { expect } from '@playwright/test';
import type { FinancialTransaction, Account } from './financial-scenarios';

// ============================================================================
// Ledger Integrity Assertions
// ============================================================================

/**
 * Assert that total credits minus debits equals closing balance
 */
export function assertLedgerIntegrity(
  transactions: FinancialTransaction[],
  expectedBalances: Record<string, number>
): void {
  const calculatedBalances: Record<string, number> = {};
  
  for (const txn of transactions) {
    if (!calculatedBalances[txn.accountId]) {
      calculatedBalances[txn.accountId] = 0;
    }
    
    if (txn.type === 'credit') {
      calculatedBalances[txn.accountId] += txn.amount;
    } else {
      calculatedBalances[txn.accountId] -= txn.amount;
    }
  }
  
  for (const [accountId, expectedBalance] of Object.entries(expectedBalances)) {
    const calculated = calculatedBalances[accountId] || 0;
    const tolerance = 0.01; // Allow for rounding
    
    expect(
      Math.abs(calculated - expectedBalance),
      `Ledger mismatch for ${accountId}: calculated=${calculated}, expected=${expectedBalance}`
    ).toBeLessThanOrEqual(tolerance);
  }
}

/**
 * Assert that cross-account transfers net to zero
 */
export function assertTransferBalance(
  transactions: FinancialTransaction[],
  transferCategory: string = 'Transfer'
): void {
  const transfers = transactions.filter(t => 
    t.category === transferCategory || t.description.toLowerCase().includes('transfer')
  );
  
  let netTransfer = 0;
  for (const txn of transfers) {
    if (txn.type === 'credit') {
      netTransfer += txn.amount;
    } else {
      netTransfer -= txn.amount;
    }
  }
  
  expect(
    Math.abs(netTransfer),
    `Cross-account transfers do not net to zero: ${netTransfer}`
  ).toBeLessThanOrEqual(0.01);
}

// ============================================================================
// Net Cashflow Assertions
// ============================================================================

/**
 * Assert net cashflow calculation
 * Income = Salary only (excludes credit extraction)
 * Expenses = All debits from savings
 */
export function assertNetCashflow(
  transactions: FinancialTransaction[],
  expected: {
    income: number;
    expenses: number;
    netCashflow: number;
  }
): void {
  let income = 0;
  let expenses = 0;
  
  for (const txn of transactions) {
    // Only savings accounts count for cashflow
    if (txn.accountType !== 'savings') continue;
    
    if (txn.type === 'credit') {
      // Exclude debt loop transactions from income
      if (!txn.isDebtLoop && !txn.category.includes('Extraction')) {
        income += txn.amount;
      }
    } else {
      expenses += txn.amount;
    }
  }
  
  const netCashflow = income - expenses;
  const tolerance = 0.01;
  
  expect(Math.abs(income - expected.income)).toBeLessThanOrEqual(tolerance);
  expect(Math.abs(expenses - expected.expenses)).toBeLessThanOrEqual(tolerance);
  expect(Math.abs(netCashflow - expected.netCashflow)).toBeLessThanOrEqual(tolerance);
}

/**
 * Assert that credit extraction is NOT counted as income
 */
export function assertCreditExtractionNotIncome(
  transactions: FinancialTransaction[]
): void {
  const extractions = transactions.filter(t => 
    t.isDebtLoop || t.category.includes('Extraction')
  );
  
  for (const txn of extractions) {
    // These should never be counted as income in cashflow calculations
    expect(txn.type).toBe('debit');
    expect(txn.accountType).toBe('credit');
  }
}

// ============================================================================
// Credit Card Assertions
// ============================================================================

/**
 * Assert credit card outstanding calculation
 * Outstanding = Purchases + Interest - Payments
 */
export function assertCreditCardOutstanding(
  transactions: FinancialTransaction[],
  cardId: string,
  expectedOutstanding: number
): void {
  const cardTxns = transactions.filter(t => t.accountId === cardId);
  
  let purchases = 0;
  let interest = 0;
  let payments = 0;
  
  for (const txn of cardTxns) {
    if (txn.type === 'debit') {
      if (txn.category === 'Interest') {
        interest += txn.amount;
      } else {
        purchases += txn.amount;
      }
    } else {
      // Credits to credit card are payments
      payments += txn.amount;
    }
  }
  
  const outstanding = purchases + interest - payments;
  const tolerance = 0.01;
  
  expect(Math.abs(outstanding - expectedOutstanding)).toBeLessThanOrEqual(tolerance);
}

/**
 * Assert credit utilization percentage
 */
export function assertCreditUtilization(
  outstanding: number,
  limit: number,
  expectedUtilization: number
): void {
  const utilization = (outstanding / limit) * 100;
  const tolerance = 0.1; // 0.1% tolerance
  
  expect(Math.abs(utilization - expectedUtilization)).toBeLessThanOrEqual(tolerance);
  expect(utilization).toBeGreaterThanOrEqual(0);
  expect(utilization).toBeLessThanOrEqual(100);
}

/**
 * Assert no negative utilization
 */
export function assertNoNegativeUtilization(
  transactions: FinancialTransaction[],
  accounts: Account[]
): void {
  for (const account of accounts.filter(a => a.type === 'credit')) {
    const cardTxns = transactions.filter(t => t.accountId === account.id);
    
    let outstanding = 0;
    for (const txn of cardTxns) {
      if (txn.type === 'debit') {
        outstanding += txn.amount;
      } else {
        outstanding -= txn.amount;
      }
    }
    
    const utilization = account.limit 
      ? (Math.max(0, outstanding) / account.limit) * 100 
      : 0;
    
    expect(utilization).toBeGreaterThanOrEqual(0);
    expect(utilization).toBeLessThanOrEqual(100);
  }
}

// ============================================================================
// Risk Score Assertions
// ============================================================================

/**
 * Assert risk score delta after behavior
 */
export function assertRiskScoreDelta(
  initialScore: number,
  finalScore: number,
  expectedDelta: number,
  tolerance: number = 2
): void {
  const actualDelta = finalScore - initialScore;
  expect(Math.abs(actualDelta - expectedDelta)).toBeLessThanOrEqual(tolerance);
}

/**
 * Assert risk score determinism (same input = same score)
 */
export function assertRiskScoreDeterminism(
  scores: number[],
  tolerance: number = 0
): void {
  expect(scores.length).toBeGreaterThan(1);
  
  const firstScore = scores[0];
  for (let i = 1; i < scores.length; i++) {
    expect(Math.abs(scores[i] - firstScore)).toBeLessThanOrEqual(tolerance);
  }
}

/**
 * Assert expected risk deltas based on behavior
 */
export function assertBehaviorRiskDelta(
  behavior: string,
  actualDelta: number
): void {
  const expectedDeltas: Record<string, { min: number; max: number }> = {
    'minimum_due': { min: 3, max: 8 },      // +5 points
    'credit_extraction_first': { min: 12, max: 18 }, // +15 points
    'credit_extraction_repeat': { min: 22, max: 28 }, // +25 points
    'emi_discipline': { min: -12, max: -8 }, // -10 points
    'savings_growth': { min: -10, max: -6 }, // -8 points
    'late_fee': { min: 10, max: 14 },        // +12 points
    'debt_loop': { min: 27, max: 33 },       // +30 points
  };
  
  const expected = expectedDeltas[behavior];
  if (!expected) {
    throw new Error(`Unknown behavior type: ${behavior}`);
  }
  
  expect(actualDelta).toBeGreaterThanOrEqual(expected.min);
  expect(actualDelta).toBeLessThanOrEqual(expected.max);
}

// ============================================================================
// Debt Loop Assertions
// ============================================================================

/**
 * Assert debt loop detection
 */
export function assertDebtLoopDetected(
  cycles: number,
  minCycles: number = 3
): void {
  expect(cycles).toBeGreaterThanOrEqual(minCycles);
}

/**
 * Assert debt loop warning in UI
 */
export async function assertDebtLoopWarningVisible(
  page: Page
): Promise<void> {
  const warning = page.locator('text=/debt trap|debt cycle|warning|risk/i').first();
  await expect(warning).toBeVisible();
}

// ============================================================================
// UI Consistency Assertions
// ============================================================================

/**
 * Assert UI value matches backend value
 */
export function assertUIBackendMatch(
  uiValue: number,
  backendValue: number,
  context: string,
  tolerance: number = 0.01
): void {
  expect(
    Math.abs(uiValue - backendValue),
    `UI/Backend mismatch for ${context}: UI=${uiValue}, Backend=${backendValue}`
  ).toBeLessThanOrEqual(tolerance);
}

/**
 * Assert no NaN or undefined in UI values
 */
export function assertNoInvalidValues(
  values: Record<string, number>
): void {
  for (const [key, value] of Object.entries(values)) {
    expect(value, `Value ${key} is invalid`).not.toBeNaN();
    expect(value, `Value ${key} is undefined`).toBeDefined();
    expect(value, `Value ${key} is null`).not.toBeNull();
  }
}

/**
 * Assert percentage values are valid
 */
export function assertValidPercentage(
  value: number,
  context: string
): void {
  expect(value, `${context} is NaN`).not.toBeNaN();
  expect(value, `${context} is negative`).toBeGreaterThanOrEqual(0);
  expect(value, `${context} exceeds 100%`).toBeLessThanOrEqual(100);
}

// ============================================================================
// Performance Assertions
// ============================================================================

/**
 * Assert response time is within threshold
 */
export function assertResponseTime(
  actualMs: number,
  thresholdMs: number
): void {
  expect(
    actualMs,
    `Response time ${actualMs}ms exceeds threshold ${thresholdMs}ms`
  ).toBeLessThanOrEqual(thresholdMs);
}

/**
 * Assert no UI freeze (frame drops)
 */
export async function assertNoUIFreeze(
  page: Page,
  durationMs: number = 1000
): Promise<void> {
  const frames = await page.evaluate((duration: number) => {
    return new Promise<number>((resolve) => {
      let count = 0;
      const start = performance.now();
      
      const countFrame = () => {
        count++;
        if (performance.now() - start < duration) {
          requestAnimationFrame(countFrame);
        } else {
          resolve(count);
        }
      };
      
      requestAnimationFrame(countFrame);
    });
  }, durationMs);
  
  // Expect at least 30fps (30 frames in 1000ms)
  expect(frames).toBeGreaterThan(25);
}