/**
 * Seed Data Utility - Deterministic test data for Playwright tests
 */

import { Page } from '@playwright/test';

const APP_STORAGE_KEY = 'bank-parser-storage';
const MODE_STORAGE_KEY = 'clariFin_dashboard_mode';

/** Seed test data into page localStorage */
export async function seedLocalStorage(page: Page, options: {
  mode?: 'personal' | 'family';
  transactionCount?: number;
} = {}): Promise<void> {
  const { mode = 'personal', transactionCount = 20 } = options;
  
  const transactions = generateTestTransactions(transactionCount);
  const cards = [
    { id: 'card-1', bankName: 'HDFC Bank', cardNumber: '****1234' },
    { id: 'card-2', bankName: 'ICICI Bank', cardNumber: '****5678' },
  ];
  
  await page.evaluate(
    ({ key, modeKey, mode: m, transactions: txns, cards: cardData }) => {
      const data = {
        state: { cards: cardData, transactions: txns, paidBills: [], selectedCardId: null },
        version: 1,
      };
      localStorage.setItem(key, JSON.stringify(data));
      localStorage.setItem(modeKey, m);
    },
    { key: APP_STORAGE_KEY, modeKey: MODE_STORAGE_KEY, mode, transactions, cards }
  );
}

/** Generate deterministic test transactions */
function generateTestTransactions(count: number) {
  const transactions = [];
  const categories = ['Shopping', 'Food', 'Transport', 'Entertainment', 'Bills'];
  
  for (let i = 0; i < count; i++) {
    transactions.push({
      id: `txn-${i + 1}`,
      date: `2026-02-${String((i % 28) + 1).padStart(2, '0')}`,
      description: `Test Transaction ${i + 1}`,
      amount: (i + 1) * 100,
      type: i % 2 === 0 ? 'debit' : 'credit',
      category: categories[i % categories.length],
    });
  }
  return transactions;
}

/** Clear all test data */
export async function clearLocalStorage(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.removeItem(APP_STORAGE_KEY);
    localStorage.removeItem(MODE_STORAGE_KEY);
  });
}

export { APP_STORAGE_KEY, MODE_STORAGE_KEY };