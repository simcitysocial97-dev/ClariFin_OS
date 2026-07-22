/**
 * Accounts Summary Card - Stage 4 Accounts Intelligence Workspace
 *
 * Displays aggregated account summary with total balance and account count.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINR, formatINRCompact } from '@/lib/utils/format';
import type { AccountsViewModel } from '@/types/accounts-view-model';

/**
 * Accounts Summary Card Props
 */
interface AccountsSummaryProps {
  accounts: AccountsViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Accounts Summary Card Component
 *
 * Shows total balance across all accounts, account count, and type breakdown.
 */
export function AccountsSummary({ accounts, loading, error }: AccountsSummaryProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="space-y-4">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-32" />
            <div className="grid grid-cols-3 gap-4 pt-4">
              <Skeleton className="h-12" />
              <Skeleton className="h-12" />
              <Skeleton className="h-12" />
            </div>
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
          <div className="flex items-center gap-2 text-[var(--color-negative-600)]">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load accounts data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!accounts) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-[var(--text-tertiary)] text-sm">No accounts data available</p>
        </CardContent>
      </Card>
    );
  }

  const { total_balance_paise, account_count, type_breakdown } = accounts;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Total Balance Label */}
          <p className="text-sm text-[var(--text-tertiary)]">Total Balance</p>

          {/* Total Balance Amount */}
          <p className="text-3xl font-bold" aria-label="Total account balance">
            {formatINR(total_balance_paise)}
          </p>

          {/* Account Count */}
          <p className="text-sm text-[var(--text-secondary)]">
            {account_count} account{account_count !== 1 ? 's' : ''}
          </p>

          {/* Type Breakdown */}
          {type_breakdown && type_breakdown.length > 0 && (
            <div className="pt-4 border-t">
              <p className="text-xs text-[var(--text-tertiary)] mb-2">By Type</p>
              <div className="space-y-2">
                {type_breakdown.map((tb) => (
                  <div key={tb.type} className="flex items-center justify-between">
                    <span className="text-xs capitalize">{tb.type}</span>
                    <span className="text-xs font-medium" aria-label={`${tb.type} balance`}>
                      {formatINRCompact(tb.total_balance_paise)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}