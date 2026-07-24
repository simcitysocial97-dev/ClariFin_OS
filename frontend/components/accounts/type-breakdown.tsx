/**
 * Type Breakdown - Stage 4 Accounts Intelligence Workspace
 *
 * Shows account distribution by type (savings, current, etc.).
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';
import { formatINRCompact } from '@/lib/utils/format';
import type { AccountsViewModel, AccountTypeBreakdownViewModel } from '@/types/accounts-view-model';

/**
 * Type Breakdown Props
 */
interface TypeBreakdownProps {
  accounts: AccountsViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Type Breakdown Component
 *
 * Shows account type distribution with counts and balances.
 */
export function TypeBreakdown({ accounts, loading, error }: TypeBreakdownProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <Skeleton className="h-4 w-32 mb-4" />
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <Skeleton key={i} className="h-12 w-full" />
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
            <span className="text-sm">Failed to load type breakdown</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!accounts || !accounts.type_breakdown || accounts.type_breakdown.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-gray-500 text-sm">No account type data available</p>
        </CardContent>
      </Card>
    );
  }

  const { type_breakdown } = accounts;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Title */}
          <p className="text-sm text-gray-500">Account Types</p>

          {/* Type breakdown list */}
          <div className="space-y-3">
            {type_breakdown.map((tb: AccountTypeBreakdownViewModel) => (
              <div key={tb.type} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500" />
                  <span className="text-sm capitalize">{tb.type}</span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium" aria-label={`${tb.type} balance`}>
                    {formatINRCompact(tb.total_balance_paise)}
                  </p>
                  <p className="text-xs text-gray-500">{tb.count} account{tb.count !== 1 ? 's' : ''}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}