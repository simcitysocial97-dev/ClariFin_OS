/**
 * Transaction List - Stage 4 Accounts Intelligence Workspace
 *
 * Shows transactions for selected account with sorting and pagination.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINR, formatDateDisplay } from '@/lib/utils/format';
import type { AccountsViewModel, AccountTransactionViewModel } from '@/types/accounts-view-model';

/**
 * Transaction List Props
 */
interface TransactionListProps {
  accounts: AccountsViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Transaction List Component
 *
 * Shows transactions in a table format with date, description, category, and amount.
 */
export function TransactionList({ accounts, loading, error }: TransactionListProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <Skeleton className="h-4 w-32 mb-4" />
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map(i => (
              <Skeleton key={i} className="h-10 w-full" />
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
            <span className="text-sm">Failed to load transactions</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!accounts || !accounts.transactions || accounts.transactions.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No transactions available</p>
        </CardContent>
      </Card>
    );
  }

  const { transactions } = accounts;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Title */}
          <p className="text-sm text-gray-500">Recent Transactions</p>

          {/* Transaction table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Date</th>
                  <th className="text-left py-2">Description</th>
                  <th className="text-left py-2">Category</th>
                  <th className="text-right py-2">Amount</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((txn: AccountTransactionViewModel) => (
                  <tr key={txn.id} className="border-b hover:bg-gray-50">
                    <td className="py-2" aria-label="Transaction date">
                      {formatDateDisplay(txn.date)}
                    </td>
                    <td className="py-2" aria-label="Transaction description">
                      {txn.description}
                    </td>
                    <td className="py-2" aria-label="Transaction category">
                      <span className="inline-block px-2 py-1 text-xs bg-gray-100 rounded">
                        {txn.category}
                      </span>
                    </td>
                    <td className="py-2 text-right" aria-label="Transaction amount">
                      <span className={txn.amount_paise >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {formatINR(txn.amount_paise)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}