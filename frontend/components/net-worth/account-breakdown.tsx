/**
 * Net Worth Account Breakdown Table - Stage 4 Net Worth Intelligence Workspace
 *
 * Shows detailed list of all accounts contributing to net worth.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, Table2 } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { NetWorthViewModel, NetWorthBreakdownItemViewModel } from '@/types/net-worth-view-model';

/**
 * Net Worth Account Breakdown Props
 */
interface AccountBreakdownProps {
  netWorth: NetWorthViewModel | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Account Row Component
 * Displays a single account in the breakdown table
 */
function AccountRow({ account }: { account: NetWorthBreakdownItemViewModel }) {
  const isLiability = account.balance_paise < 0;
  const displayValue = Math.abs(account.balance_paise);

  return (
    <tr className="border-b last:border-0">
      <td className="py-2 px-2">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isLiability ? 'bg-red-500' : 'bg-green-500'
            }`}
            aria-label={isLiability ? 'Liability' : 'Asset'}
          />
          <span className="text-sm font-medium">{account.name}</span>
        </div>
      </td>
      <td className="py-2 px-2 text-sm text-gray-600">{account.type}</td>
      <td className="py-2 px-2 text-right">
        <span className="text-sm font-medium">{formatINR(displayValue)}</span>
      </td>
      <td className="py-2 px-2 text-right">
        <span className="text-xs text-gray-500">{account.percentage.toFixed(1)}%</span>
      </td>
    </tr>
  );
}

/**
 * Net Worth Account Breakdown Table Component
 *
 * Shows all accounts with their balances and contribution percentages.
 */
export function AccountBreakdown({ netWorth, loading, error }: AccountBreakdownProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <Skeleton className="h-5 w-40" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Account Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load account data</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!netWorth) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Account Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-sm">No accounts to display</p>
        </CardContent>
      </Card>
    );
  }

  const { composition } = netWorth;
  const allAccounts = [...composition.asset_breakdown, ...composition.liability_breakdown];

  if (allAccounts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Account Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-sm">No accounts configured</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Table2 className="h-5 w-5" />
          Account Breakdown
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full" role="table" aria-label="Net worth account breakdown">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 px-2 text-xs font-medium text-gray-500">Name</th>
                <th className="text-left py-2 px-2 text-xs font-medium text-gray-500">Type</th>
                <th className="text-right py-2 px-2 text-xs font-medium text-gray-500">Balance</th>
                <th className="text-right py-2 px-2 text-xs font-medium text-gray-500">Contribution</th>
              </tr>
            </thead>
            <tbody>
              {allAccounts.map((account) => (
                <AccountRow key={account.id} account={account} />
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}