/**
 * Transaction Validation
 * Validates extracted totals against metadata
 */
import type { Transaction } from '@/types/transaction';
import type { Metadata } from '@/types/transaction';

export interface ValidationResult {
    isValid: boolean;
    message: string;
    calculatedTotal: number;
    expectedTotal: number;
    bankTotal: number;
    difference: number;
    totalDebits: number;
    totalCredits: number;
    transactionCount: number;
}

/**
 * Validate transactions against metadata totals
 */
export function validateTransactions(
    transactions: Transaction[],
    metadata: Metadata
): ValidationResult {

    const totalDebits = transactions
        .filter(t => t.type === 'debit')
        .reduce((sum, t) => sum + ((t.amount_paise ?? 0) / 100), 0);

    const totalCredits = transactions
        .filter(t => t.type === 'credit')
        .reduce((sum, t) => sum + ((t.amount_paise ?? 0) / 100), 0);

    // Calculate expected total: opening + credits - debits
    const calculatedTotal = (metadata.openingBalance || 0) + totalCredits - totalDebits;
    const expectedTotal = metadata.totalAmountDue || 0;

    const difference = Math.abs(calculatedTotal - expectedTotal);
    const tolerance = 1.0; // Allow 1 rupee difference
    const isValid = difference <= tolerance;

    return {
        isValid,
        message: isValid
            ? 'Totals match'
            : `Difference: ₹${difference.toFixed(2)} (Calculated: ₹${calculatedTotal.toFixed(2)}, Expected: ₹${expectedTotal.toFixed(2)})`,
        calculatedTotal,
        expectedTotal,
        bankTotal: expectedTotal,
        difference,
        totalDebits,
        totalCredits,
        transactionCount: transactions.length
    };
}