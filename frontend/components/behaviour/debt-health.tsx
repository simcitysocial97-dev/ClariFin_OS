/**
 * Debt Health - Stage 4 Behaviour Intelligence Workspace
 *
 * Displays debt health analysis.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, CreditCard } from 'lucide-react';
import { formatINR } from '@/lib/utils/format';
import type { DebtHealthViewModel } from '@/types/behaviour-view-model';

/**
 * Debt Health Props
 */
interface DebtHealthProps {
  debtHealth: DebtHealthViewModel | null | undefined;
  loading: boolean;
  error: Error | null;
}

/**
 * Debt Health Component
 *
 * Shows the debt-to-income ratio and health score.
 */
export function DebtHealth({ debtHealth, loading, error }: DebtHealthProps) {
  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-16 w-16 rounded-full mx-auto" />
            <Skeleton className="h-4 w-24 mx-auto" />
            <div className="grid grid-cols-2 gap-4">
              <Skeleton className="h-10" />
              <Skeleton className="h-10" />
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
            <span className="text-sm">Failed to load debt health</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Empty state
  if (!debtHealth) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-[var(--text-tertiary)] text-sm">No debt health data available</p>
        </CardContent>
      </Card>
    );
  }

  // Convert basis points to percentage
  const dtiPercentage = (debtHealth.debt_to_income_bps / 100).toFixed(1);
  const healthPercentage = (debtHealth.health_score / 100).toFixed(1);

  // Determine health color
  const healthColor = debtHealth.health_score >= 800 
    ? 'text-[var(--color-positive-600)]' 
    : debtHealth.health_score >= 600 
      ? 'text-[var(--color-warning-600)]' 
      : 'text-[var(--color-negative-600)]';

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-5 w-5" />
          Debt Health
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Health Score */}
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-1">Health Score</p>
            <p className={`text-3xl font-bold ${healthColor}`} aria-label="Debt health score">
              {healthPercentage}%
            </p>
          </div>

          {/* Debt to Income Ratio */}
          <div className="pt-2 border-t">
            <p className="text-xs text-gray-500 mb-1">Debt-to-Income Ratio</p>
            <p className="text-lg font-medium" aria-label="Debt to income ratio">
              {dtiPercentage}%
            </p>
          </div>

          {/* Total Debt and Income */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500">Total Debt</p>
              <p className="text-sm font-medium" aria-label="Total debt">
                {formatINR(debtHealth.total_debt_paise)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Total Income</p>
              <p className="text-sm font-medium" aria-label="Total income">
                {formatINR(debtHealth.total_income_paise)}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}