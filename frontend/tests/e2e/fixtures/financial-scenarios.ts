/**
 * Financial Scenarios Generator
 * ==============================
 * 
 * Generates deterministic synthetic financial data for E2E validation:
 * - 400 transactions over 8 months
 * - 2 Savings accounts, 3 Credit Cards
 * - Debt loop pattern (3-4 cycles)
 * - Salary, EMI, utilities, expenses
 */

// ============================================================================
// Types
// ============================================================================

export interface FinancialTransaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  type: 'credit' | 'debit';
  accountId: string;
  accountType: 'savings' | 'credit';
  category: string;
  isRecurring?: boolean;
  isDebtLoop?: boolean;
}

export interface Account {
  id: string;
  name: string;
  type: 'savings' | 'credit';
  bankName: string;
  limit?: number; // For credit cards
}

export interface DebtLoopPattern {
  extraction: { amount: number; from: string; to: string };
  repayment: { amount: number; from: string; to: string };
  cycleDays: number;
  repeats: number;
}

export interface FinancialScenario {
  accounts: Account[];
  transactions: FinancialTransaction[];
  metadata: {
    totalTransactions: number;
    dateRange: { start: string; end: string };
    debtLoopsDetected: number;
    seed: number;
  };
}

// ============================================================================
// Constants
// ============================================================================

const ACCOUNTS: Account[] = [
  { id: 'SAV_001', name: 'Primary Savings', type: 'savings', bankName: 'HDFC' },
  { id: 'SAV_002', name: 'Emergency Fund', type: 'savings', bankName: 'ICICI' },
  { id: 'CC_001', name: 'Primary Credit', type: 'credit', bankName: 'HDFC', limit: 100000 },
  { id: 'CC_002', name: 'Secondary Credit', type: 'credit', bankName: 'ICICI', limit: 75000 },
  { id: 'CC_003', name: 'Travel Card', type: 'credit', bankName: 'Axis', limit: 50000 },
];

const CATEGORIES = {
  INCOME: ['Salary', 'Bonus', 'Interest'],
  ESSENTIAL: ['Rent', 'Utilities', 'Groceries', 'Transport'],
  EMI: ['Home Loan', 'Car Loan', 'Personal Loan'],
  LIFESTYLE: ['Dining', 'Entertainment', 'Shopping', 'Travel'],
  FINANCIAL: ['Credit Card Payment', 'Investment', 'Insurance'],
  DEBT_LOOP: ['Rent via Credit', 'Credit Extraction', 'Card Repayment'],
};

// ============================================================================
// Deterministic Random Generator
// ============================================================================

export class SeededRandom {
  private seed: number;

  constructor(seed: number = 12345) {
    this.seed = seed;
  }

  next(): number {
    // Linear Congruential Generator
    this.seed = (this.seed * 1103515245 + 12345) & 0x7fffffff;
    return this.seed / 0x7fffffff;
  }

  range(min: number, max: number): number {
    return min + this.next() * (max - min);
  }

  int(min: number, max: number): number {
    return Math.floor(this.range(min, max + 1));
  }

  pick<T>(array: T[]): T {
    return array[this.int(0, array.length - 1)];
  }

  bool(probability: number = 0.5): boolean {
    return this.next() < probability;
  }
}

// ============================================================================
// Scenario Generator
// ============================================================================

export function generateDebtLoopScenario(seed: number = 12345): FinancialScenario {
  const rng = new SeededRandom(seed);
  const transactions: FinancialTransaction[] = [];
  
  // 8 months of data
  const startDate = new Date('2025-06-01');
  const endDate = new Date('2026-01-31');
  let txnId = 1;
  
  // Track balances for validation
  const balances: Record<string, number> = {
    SAV_001: 50000,
    SAV_002: 20000,
    CC_001: 0,
    CC_002: 0,
    CC_003: 0,
  };
  
  // Generate monthly patterns
  for (let month = 0; month < 8; month++) {
    const monthStart = new Date(startDate);
    monthStart.setMonth(monthStart.getMonth() + month);
    
    // 1. Salary Credit (Day 1)
    const salary = 75000 + rng.int(-5000, 5000); // 70k-80k
    transactions.push({
      id: `TXN_${String(txnId++).padStart(4, '0')}`,
      date: formatDate(monthStart),
      description: 'Salary Credit',
      amount: salary,
      type: 'credit',
      accountId: 'SAV_001',
      accountType: 'savings',
      category: 'Salary',
      isRecurring: true,
    });
    balances.SAV_001 += salary;
    
    // 2. Rent Payment via Credit Card (Day 5) - DEBT LOOP START
    const rentAmount = 25000;
    const rentDate = new Date(monthStart);
    rentDate.setDate(5);
    
    // Credit extraction for rent
    transactions.push({
      id: `TXN_${String(txnId++).padStart(4, '0')}`,
      date: formatDate(rentDate),
      description: 'Rent Payment via Credit Card',
      amount: rentAmount,
      type: 'debit',
      accountId: 'CC_001',
      accountType: 'credit',
      category: 'Rent via Credit',
      isDebtLoop: true,
    });
    balances.CC_001 -= rentAmount;
    
    // Transfer to savings (CRED-like behavior)
    transactions.push({
      id: `TXN_${String(txnId++).padStart(4, '0')}`,
      date: formatDate(rentDate),
      description: 'Credit Cashback to Savings',
      amount: rentAmount * 0.02, // 2% cashback
      type: 'credit',
      accountId: 'SAV_001',
      accountType: 'savings',
      category: 'Cashback',
    });
    balances.SAV_001 += rentAmount * 0.02;
    
    // 3. EMI Payments (Day 10)
    const emiDate = new Date(monthStart);
    emiDate.setDate(10);
    const emiAmount = 15000;
    
    transactions.push({
      id: `TXN_${String(txnId++).padStart(4, '0')}`,
      date: formatDate(emiDate),
      description: 'Home Loan EMI',
      amount: emiAmount,
      type: 'debit',
      accountId: 'SAV_001',
      accountType: 'savings',
      category: 'Home Loan',
      isRecurring: true,
    });
    balances.SAV_001 -= emiAmount;
    
    // 4. Utilities (Day 15)
    const utilDate = new Date(monthStart);
    utilDate.setDate(15);
    const utilAmount = 3000 + rng.int(-500, 1000);
    
    transactions.push({
      id: `TXN_${String(txnId++).padStart(4, '0')}`,
      date: formatDate(utilDate),
      description: 'Electricity & Water Bill',
      amount: utilAmount,
      type: 'debit',
      accountId: 'SAV_001',
      accountType: 'savings',
      category: 'Utilities',
      isRecurring: true,
    });
    balances.SAV_001 -= utilAmount;
    
    // 5. Daily Expenses (Distributed throughout month)
    const dailyExpenses = [
      { category: 'Groceries', min: 500, max: 2000, count: 8 },
      { category: 'Dining', min: 300, max: 1500, count: 6 },
      { category: 'Transport', min: 100, max: 500, count: 10 },
      { category: 'Shopping', min: 500, max: 3000, count: 4 },
      { category: 'Entertainment', min: 200, max: 1000, count: 3 },
    ];
    
    for (const expense of dailyExpenses) {
      for (let i = 0; i < expense.count; i++) {
        const expenseDate = new Date(monthStart);
        expenseDate.setDate(rng.int(1, 28));
        
        const amount = rng.int(expense.min, expense.max);
        const useCredit = rng.bool(0.4); // 40% credit card usage
        
        const accountId = useCredit ? rng.pick(['CC_001', 'CC_002', 'CC_003']) : 'SAV_001';
        const accountType = useCredit ? 'credit' : 'savings';
        
        transactions.push({
          id: `TXN_${String(txnId++).padStart(4, '0')}`,
          date: formatDate(expenseDate),
          description: `${expense.category} Expense`,
          amount,
          type: 'debit',
          accountId,
          accountType,
          category: expense.category,
        });
        
        balances[accountId] -= amount;
      }
    }
    
    // 6. Credit Card Repayment (Day 25) - DEBT LOOP END
    const repaymentDate = new Date(monthStart);
    repaymentDate.setDate(25);
    
    // Calculate minimum due (5% of outstanding)
    const cc1Outstanding = Math.abs(balances.CC_001);
    const minDue = cc1Outstanding * 0.05;
    const fullPayment = cc1Outstanding;
    
    // Sometimes pay minimum, sometimes full
    const payFull = rng.bool(0.6); // 60% full payment
    const paymentAmount = payFull ? fullPayment : minDue;
    
    if (paymentAmount > 0) {
      transactions.push({
        id: `TXN_${String(txnId++).padStart(4, '0')}`,
        date: formatDate(repaymentDate),
        description: payFull ? 'Credit Card Full Payment' : 'Credit Card Minimum Due',
        amount: paymentAmount,
        type: 'debit',
        accountId: 'SAV_001',
        accountType: 'savings',
        category: 'Credit Card Payment',
        isRecurring: true,
      });
      balances.SAV_001 -= paymentAmount;
      
      // Credit the card
      transactions.push({
        id: `TXN_${String(txnId++).padStart(4, '0')}`,
        date: formatDate(repaymentDate),
        description: 'Card Payment Credit',
        amount: paymentAmount,
        type: 'credit',
        accountId: 'CC_001',
        accountType: 'credit',
        category: 'Credit Card Payment',
        isRecurring: true,
      });
      balances.CC_001 += paymentAmount;
    }
    
    // 7. Interest charges (if not paid in full)
    if (!payFull && cc1Outstanding > 0) {
      const interestDate = new Date(monthStart);
      interestDate.setDate(28);
      const interest = cc1Outstanding * 0.036; // ~3.6% monthly
      
      transactions.push({
        id: `TXN_${String(txnId++).padStart(4, '0')}`,
        date: formatDate(interestDate),
        description: 'Credit Card Interest',
        amount: interest,
        type: 'debit',
        accountId: 'CC_001',
        accountType: 'credit',
        category: 'Interest',
      });
      balances.CC_001 -= interest;
    }
    
    // 8. Savings transfer (if surplus)
    if (balances.SAV_001 > 30000 && rng.bool(0.5)) {
      const transferDate = new Date(monthStart);
      transferDate.setDate(20);
      const transferAmount = rng.int(5000, 10000);
      
      transactions.push({
        id: `TXN_${String(txnId++).padStart(4, '0')}`,
        date: formatDate(transferDate),
        description: 'Savings Transfer',
        amount: transferAmount,
        type: 'debit',
        accountId: 'SAV_001',
        accountType: 'savings',
        category: 'Investment',
      });
      balances.SAV_001 -= transferAmount;
      
      transactions.push({
        id: `TXN_${String(txnId++).padStart(4, '0')}`,
        date: formatDate(transferDate),
        description: 'Savings Transfer Credit',
        amount: transferAmount,
        type: 'credit',
        accountId: 'SAV_002',
        accountType: 'savings',
        category: 'Investment',
      });
      balances.SAV_002 += transferAmount;
    }
  }
  
  // Sort transactions by date
  transactions.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  
  // Count debt loops
  const debtLoops = transactions.filter(t => t.isDebtLoop).length;
  
  return {
    accounts: ACCOUNTS,
    transactions,
    metadata: {
      totalTransactions: transactions.length,
      dateRange: { start: formatDate(startDate), end: formatDate(endDate) },
      debtLoopsDetected: debtLoops,
      seed,
    },
  };
}

// ============================================================================
// Helper Functions
// ============================================================================

function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}

/**
 * Calculate expected balances from transactions
 */
export function calculateExpectedBalances(transactions: FinancialTransaction[]): Record<string, number> {
  const balances: Record<string, number> = {};
  
  for (const txn of transactions) {
    if (!balances[txn.accountId]) {
      balances[txn.accountId] = 0;
    }
    
    if (txn.type === 'credit') {
      balances[txn.accountId] += txn.amount;
    } else {
      balances[txn.accountId] -= txn.amount;
    }
  }
  
  return balances;
}

/**
 * Calculate net cashflow (income - expenses)
 */
export function calculateNetCashflow(transactions: FinancialTransaction[]): {
  income: number;
  expenses: number;
  netCashflow: number;
} {
  let income = 0;
  let expenses = 0;
  
  for (const txn of transactions) {
    // Only count savings account transactions for cashflow
    if (txn.accountType !== 'savings') continue;
    
    if (txn.type === 'credit') {
      // Exclude credit extraction (debt loop) from income
      if (!txn.isDebtLoop && txn.category !== 'Credit Extraction') {
        income += txn.amount;
      }
    } else {
      expenses += txn.amount;
    }
  }
  
  return {
    income,
    expenses,
    netCashflow: income - expenses,
  };
}

/**
 * Detect debt loop patterns
 */
export function detectDebtLoops(transactions: FinancialTransaction[]): {
  detected: boolean;
  cycles: number;
  totalExtraction: number;
} {
  const extractions = transactions.filter(t => 
    t.isDebtLoop && t.type === 'debit' && t.accountType === 'credit'
  );
  
  const repayments = transactions.filter(t =>
    t.category === 'Credit Card Payment' && t.type === 'debit'
  );
  
  // Group by month to detect cycles
  const monthlyExtractions = groupByMonth(extractions);
  const monthlyRepayments = groupByMonth(repayments);
  
  let cycles = 0;
  let totalExtraction = 0;
  
  for (const [month, extracts] of Object.entries(monthlyExtractions)) {
    const monthExtracts = extracts as FinancialTransaction[];
    const monthRepays = (monthlyRepayments[month] || []) as FinancialTransaction[];
    
    if (monthExtracts.length > 0 && monthRepays.length > 0) {
      cycles++;
      totalExtraction += monthExtracts.reduce((sum, t) => sum + t.amount, 0);
    }
  }
  
  return {
    detected: cycles >= 3,
    cycles,
    totalExtraction,
  };
}

function groupByMonth(transactions: FinancialTransaction[]): Record<string, FinancialTransaction[]> {
  const grouped: Record<string, FinancialTransaction[]> = {};
  
  for (const txn of transactions) {
    const month = txn.date.substring(0, 7); // YYYY-MM
    if (!grouped[month]) {
      grouped[month] = [];
    }
    grouped[month].push(txn);
  }
  
  return grouped;
}

// ============================================================================
// Export
// ============================================================================

export { ACCOUNTS, CATEGORIES };