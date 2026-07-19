/**
 * Transaction List - Stage 4 Cashflow Truth Workspace
 *
 * Displays a list of transactions for cashflow analysis.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { CashflowTransactionViewModel } from '@/types/cashflow-view-model';

/**
 * Transaction List Props
 */
interface TransactionListProps {
  transactions: CashflowTransactionViewModel[];
  loading: boolean;
  error: Error | null;
}

/**
 * Transaction List Component
 *
 * Shows a list of transactions with date, description, amount, and category.
 */
export function TransactionList({ transactions, loading, error }: TransactionListProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load transaction data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!transactions || transactions.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No transactions found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Transactions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {transactions.map((transaction) => (
            <div
              key={transaction.id}
              className="flex justify-between items-start p-3 border rounded-lg hover:bg-gray-50"
            >
              <div className="space-y-1">
                <p className="text-sm font-medium">{transaction.description}</p>
                <p className="text-xs text-gray-500">{transaction.date}</p>
                {transaction.merchant && (
                  <p className="text-xs text-gray-400">{transaction.merchant}</p>
                )}
                <span className="inline-block px-2 py-1 text-xs bg-gray-100 rounded">
                  {transaction.category}
                </span>
              </div>
              <p className="text-sm font-semibold">
                {formatINR(transaction.amount_paise)}
              </p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}