import type { Transaction } from '@/types/transaction'

export const mockTransaction: Transaction = {
  id: 1,
  date: '2025-01-15',
  description: 'Test Transaction',
  amount: { paise: 50000, rupees: 500.0 },
  type: 'debit',
  category: 'Food & Dining',
  bank: 'HDFC',
  member: 'Self',
}

export const mockCreditTransaction: Transaction = {
  ...mockTransaction,
  id: 2,
  amount: { paise: 150000, rupees: 1500.0 },
  type: 'credit',
  description: 'Salary Credit',
  category: 'Income',
}

export const mockTransportTransaction: Transaction = {
  ...mockTransaction,
  id: 3,
  amount: { paise: 25000, rupees: 250.0 },
  type: 'debit',
  description: 'Uber Ride',
  category: 'Transport',
}

export const mockShoppingTransaction: Transaction = {
  ...mockTransaction,
  id: 4,
  amount: { paise: 35000, rupees: 350.0 },
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
