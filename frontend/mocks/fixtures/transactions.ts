import type { Transaction } from '@/types/transaction'

export const mockTransaction: Transaction = {
  id: 'test-tx-001',
  date: '2025-01-15',
  description: 'Test Transaction',
  amount_paise: 50000,
  type: 'debit',
  category: 'Food & Dining',
  bank: 'HDFC',
  member: undefined,
}

export const mockCreditTransaction: Transaction = {
  ...mockTransaction,
  id: 'test-tx-002',
  amount_paise: 150000,
  type: 'credit',
  description: 'Salary Credit',
  category: 'Income',
}

export const mockTransportTransaction: Transaction = {
  ...mockTransaction,
  id: 'test-tx-003',
  amount_paise: 25000,
  type: 'debit',
  description: 'Uber Ride',
  category: 'Transport',
}

export const mockShoppingTransaction: Transaction = {
  ...mockTransaction,
  id: 'test-tx-004',
  amount_paise: 35000,
  type: 'debit',
  description: 'Amazon Purchase',
  category: 'Shopping',
}

export const mockTransactionList: Transaction[] = [
  mockTransaction,
  mockCreditTransaction,
  mockTransportTransaction,
  mockShoppingTransaction,
]